"""Train and validation-select the final 40-class candidate without test access."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import shutil
import subprocess
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_17_config import (
    BATCH_SIZE,
    DROPOUT,
    EARLY_STOPPING_PATIENCE,
    EXPERIMENTS_DIR,
    FEATURE_ORDER,
    FINAL_LABELS,
    FIGURES_DIR,
    HIDDEN_UNITS,
    HISTORICAL_TRAIN_FEATURES,
    LEARNING_RATE,
    MAX_EPOCHS,
    METADATA_DIR,
    METRICS_DIR,
    MINIMUM_CALIBRATION_COVERAGE,
    MINIMUM_CONFIDENCE_GRID,
    MODEL_DIR,
    OUTPUT_CLASSES,
    PHONE_AUGMENTED_FEATURES,
    PHONE_TRAIN_FEATURES,
    PHONE_VALIDATION_FEATURES,
    REPORTS_DIR,
    ROOT,
    SEED,
    TOP2_MARGIN_GRID,
    ensure_output_directories,
)
from sprint_2_17_utils import (
    json_safe,
    relative_path,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


@dataclass(frozen=True)
class ExperimentSpec:
    """One bounded validation-only candidate configuration."""

    experiment_id: str
    description: str
    include_augmentation: bool
    include_historical: bool
    hidden_units: tuple[int, ...] = tuple(HIDDEN_UNITS)
    dropout: float = DROPOUT
    learning_rate: float = LEARNING_RATE
    batch_size: int = BATCH_SIZE


INITIAL_EXPERIMENTS = [
    ExperimentSpec(
        "experiment_A_phone_only",
        "600 real phone training samples; no augmentation or historical data",
        False,
        False,
    ),
    ExperimentSpec(
        "experiment_B_phone_augmentation",
        "600 real plus 600 conservative augmented phone training samples",
        True,
        False,
    ),
    ExperimentSpec(
        "experiment_C_phone_augmentation_historical",
        "Experiment B plus 260 final-label historical training samples",
        True,
        True,
    ),
]

TUNING_EXPERIMENTS = [
    ExperimentSpec(
        "tuning_D_lower_learning_rate",
        "Phone augmentation with lower learning rate",
        True,
        False,
        learning_rate=5e-4,
    ),
    ExperimentSpec(
        "tuning_E_lower_dropout",
        "Phone augmentation with lower dropout and learning rate",
        True,
        False,
        dropout=0.15,
        learning_rate=5e-4,
    ),
    ExperimentSpec(
        "tuning_F_smaller_network",
        "Phone augmentation with a smaller 384-192-96 network",
        True,
        False,
        hidden_units=(384, 192, 96),
        dropout=0.20,
        learning_rate=5e-4,
    ),
    ExperimentSpec(
        "tuning_G_larger_batch",
        "Phone augmentation with batch size 64",
        True,
        False,
        batch_size=64,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=MAX_EPOCHS)
    parser.add_argument("--patience", type=int, default=EARLY_STOPPING_PATIENCE)
    parser.add_argument("--max-tuning", type=int, default=2, choices=range(0, 5))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_directories()
    _protect_test_boundary()
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import sklearn
    import tensorflow as tf
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    train = _load_feature_file(PHONE_TRAIN_FEATURES, 600)
    validation = _load_feature_file(PHONE_VALIDATION_FEATURES, 200)
    augmented = _load_feature_file(PHONE_AUGMENTED_FEATURES, 600)
    historical = _load_feature_file(HISTORICAL_TRAIN_FEATURES, 260)
    datasets = {
        "train": train,
        "validation": validation,
        "augmented": augmented,
        "historical": historical,
    }

    if args.overwrite:
        for path in EXPERIMENTS_DIR.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
    elif any(EXPERIMENTS_DIR.iterdir()):
        raise FileExistsError(
            "Experiment artifacts already exist. Use --overwrite only for derived candidates."
        )

    results: list[dict[str, Any]] = []
    for spec in INITIAL_EXPERIMENTS:
        results.append(
            _train_experiment(
                tf,
                plt,
                spec,
                datasets,
                args.epochs,
                args.patience,
                accuracy_score,
                confusion_matrix,
                precision_recall_fscore_support,
            )
        )

    best_initial = _select_winner(results)
    tuning_used = best_initial["validation_macro_f1"] < 0.90 and args.max_tuning > 0
    if tuning_used:
        for spec in TUNING_EXPERIMENTS[: args.max_tuning]:
            results.append(
                _train_experiment(
                    tf,
                    plt,
                    spec,
                    datasets,
                    args.epochs,
                    args.patience,
                    accuracy_score,
                    confusion_matrix,
                    precision_recall_fscore_support,
                )
            )

    winner = _select_winner(results)
    winner_dir = EXPERIMENTS_DIR / winner["experiment_id"]
    locked_model = MODEL_DIR / "signsync_40class_final.keras"
    shutil.copy2(winner_dir / "best_checkpoint.keras", locked_model)
    winner_hash = sha256_file(locked_model)
    comparison_rows = [_comparison_row(result) for result in results]
    write_csv(
        METRICS_DIR / "validation_experiment_comparison.csv",
        comparison_rows,
        list(comparison_rows[0]),
    )
    write_json(
        METRICS_DIR / "experiment_ledger.json",
        {
            "created_at": utc_now(),
            "test_data_accessed": False,
            "initial_experiments": [asdict(spec) for spec in INITIAL_EXPERIMENTS],
            "bounded_tuning_triggered": tuning_used,
            "bounded_tuning_limit": args.max_tuning,
            "results": [
                {key: value for key, value in result.items() if key != "probabilities"}
                for result in results
            ],
        },
    )

    confidence = _write_confidence_analysis(plt, winner)
    lock = {
        "status": "winner_locked_test_not_evaluated",
        "locked_at": utc_now(),
        "selection_data": "phone validation only",
        "selection_rule": [
            "highest validation macro F1",
            "then validation accuracy",
            "then fewer high-confidence wrong predictions",
            "then smaller Keras model",
        ],
        "winning_experiment": winner["experiment_id"],
        "winning_checkpoint_source": relative_path(
            winner_dir / "best_checkpoint.keras"
        ),
        "locked_keras_model": relative_path(locked_model),
        "locked_keras_sha256": winner_hash,
        "validation_metrics": {
            key: winner[key]
            for key in (
                "validation_accuracy",
                "validation_macro_precision",
                "validation_macro_recall",
                "validation_macro_f1",
                "validation_weighted_f1",
                "validation_high_confidence_wrong",
            )
        },
        "confidence_recommendation": confidence,
        "test_evaluation_status": "not_run",
    }
    write_json(METADATA_DIR / "winner_lock.json", lock)
    _write_training_configuration(
        tf, sklearn, args, winner, locked_model, tuning_used
    )
    _write_model_selection_report(results, winner, confidence, tuning_used)

    print("Sprint 2.17 Validation-Only Training")
    print("-------------------------------------")
    for result in results:
        print(
            f"{result['experiment_id']}: val macro F1 "
            f"{result['validation_macro_f1']:.4f}, accuracy "
            f"{result['validation_accuracy']:.4f}"
        )
    print(f"Locked winner: {winner['experiment_id']}")
    print(f"Winner checkpoint SHA-256: {winner_hash}")
    print("Locked phone test accessed: False")
    print("PASS: winner selected and locked using validation only.")
    return 0


def _protect_test_boundary() -> None:
    lock_path = METADATA_DIR / "test_set_lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "locked_not_evaluated":
        raise ValueError("The phone test-set lock is not in its pre-evaluation state.")
    if (METRICS_DIR / "final_test_metrics.json").exists():
        raise FileExistsError("Final test metrics already exist; training is now closed.")


def _load_feature_file(path: Path, expected_rows: int) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as dataset:
        values = {key: dataset[key] for key in dataset.files}
    if values["X"].shape != (expected_rows, 756):
        raise ValueError(f"Unexpected feature shape in {relative_path(path)}.")
    if values["y"].shape != (expected_rows,) or not np.isfinite(values["X"]).all():
        raise ValueError(f"Invalid feature values in {relative_path(path)}.")
    if set(values["y"].astype(int)) != set(range(OUTPUT_CLASSES)):
        raise ValueError(f"Every class must appear in {relative_path(path)}.")
    return values


def _training_data(
    spec: ExperimentSpec,
    datasets: dict[str, dict[str, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    X_parts = [datasets["train"]["X"]]
    y_parts = [datasets["train"]["y"]]
    composition = ["600 real phone train"]
    if spec.include_augmentation:
        X_parts.append(datasets["augmented"]["X"])
        y_parts.append(datasets["augmented"]["y"])
        composition.append("600 augmented phone train")
    if spec.include_historical:
        X_parts.append(datasets["historical"]["X"])
        y_parts.append(datasets["historical"]["y"])
        composition.append("260 historical final-label train")
    return (
        np.concatenate(X_parts).astype(np.float32),
        np.concatenate(y_parts).astype(np.int64),
        composition,
    )


def _train_experiment(
    tf: Any,
    plt: Any,
    spec: ExperimentSpec,
    datasets: dict[str, dict[str, np.ndarray]],
    epochs: int,
    patience: int,
    accuracy_score: Any,
    confusion_matrix: Any,
    precision_recall_fscore_support: Any,
) -> dict[str, Any]:
    output_dir = EXPERIMENTS_DIR / spec.experiment_id
    output_dir.mkdir(parents=True, exist_ok=False)
    X_train, y_train, composition = _training_data(spec, datasets)
    X_val = datasets["validation"]["X"].astype(np.float32)
    y_val = datasets["validation"]["y"].astype(np.int64)
    class_weights = _balanced_class_weights(y_train)
    _set_determinism(tf, SEED)
    model = _build_model(tf, spec, X_train)
    checkpoint = output_dir / "best_checkpoint.keras"
    macro_callback = _macro_f1_callback(tf, X_val, y_val)
    callbacks = [
        macro_callback,
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint.as_posix(),
            monitor="val_macro_f1",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_macro_f1",
            mode="max",
            patience=patience,
            restore_best_weights=True,
            verbose=1,
        ),
    ]
    started = time.perf_counter()
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=spec.batch_size,
        class_weight=class_weights,
        callbacks=callbacks,
        shuffle=True,
        verbose=2,
    )
    duration = time.perf_counter() - started
    best_model = tf.keras.models.load_model(checkpoint)
    best_model.save(output_dir / "model.keras")
    probabilities = best_model.predict(X_val, verbose=0)
    predictions = np.argmax(probabilities, axis=1)
    accuracy = float(accuracy_score(y_val, predictions))
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_val,
        predictions,
        labels=list(range(OUTPUT_CLASSES)),
        average="macro",
        zero_division=0,
    )
    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            y_val,
            predictions,
            labels=list(range(OUTPUT_CLASSES)),
            average="weighted",
            zero_division=0,
        )
    )
    top_order = np.argsort(probabilities, axis=1)[:, ::-1]
    confidence = probabilities[np.arange(len(probabilities)), top_order[:, 0]]
    second_confidence = probabilities[np.arange(len(probabilities)), top_order[:, 1]]
    margin = confidence - second_confidence
    high_conf_wrong = int(
        np.sum((predictions != y_val) & (confidence >= 0.70) & (margin >= 0.15))
    )
    matrix = confusion_matrix(
        y_val, predictions, labels=list(range(OUTPUT_CLASSES))
    )
    best_epoch = int(np.argmax(history.history["val_macro_f1"])) + 1
    validation_rows = _prediction_rows(
        datasets["validation"], probabilities, 0.0, 0.0
    )
    write_csv(
        output_dir / "validation_predictions.csv",
        validation_rows,
        list(validation_rows[0]),
    )
    _write_matrix(output_dir / "validation_confusion_matrix.csv", matrix)
    history_rows = [
        {"epoch": index + 1, **{key: values[index] for key, values in history.history.items()}}
        for index in range(len(history.history["loss"]))
    ]
    write_csv(output_dir / "training_history.csv", history_rows, list(history_rows[0]))
    write_json(output_dir / "training_history.json", history.history)
    _plot_history(plt, history.history, output_dir / "training_history.png")
    model_size = (output_dir / "model.keras").stat().st_size
    result = {
        "experiment_id": spec.experiment_id,
        "description": spec.description,
        "dataset_composition": composition,
        "real_phone_training_samples": 600,
        "augmented_phone_training_samples": 600 if spec.include_augmentation else 0,
        "historical_training_samples": 260 if spec.include_historical else 0,
        "effective_training_samples": len(X_train),
        "validation_samples": len(X_val),
        "seed": SEED,
        "hidden_units": list(spec.hidden_units),
        "dropout": spec.dropout,
        "learning_rate": spec.learning_rate,
        "batch_size": spec.batch_size,
        "maximum_epochs": epochs,
        "epochs_trained": len(history.history["loss"]),
        "best_epoch": best_epoch,
        "early_stopped": len(history.history["loss"]) < epochs,
        "training_duration_seconds": duration,
        "parameter_count": int(best_model.count_params()),
        "keras_model_size_bytes": model_size,
        "validation_accuracy": accuracy,
        "validation_macro_precision": float(macro_precision),
        "validation_macro_recall": float(macro_recall),
        "validation_macro_f1": float(macro_f1),
        "validation_weighted_precision": float(weighted_precision),
        "validation_weighted_recall": float(weighted_recall),
        "validation_weighted_f1": float(weighted_f1),
        "validation_high_confidence_wrong": high_conf_wrong,
        "checkpoint_sha256": sha256_file(checkpoint),
        "test_data_accessed": False,
        "probabilities": probabilities,
    }
    write_json(
        output_dir / "validation_metrics.json",
        {key: value for key, value in result.items() if key != "probabilities"},
    )
    return result


def _set_determinism(tf: Any, seed: int) -> None:
    tf.keras.backend.clear_session()
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def _build_model(tf: Any, spec: ExperimentSpec, X_train: np.ndarray) -> Any:
    normalization = tf.keras.layers.Normalization(name="feature_normalization")
    normalization.adapt(X_train.astype(np.float32))
    inputs = tf.keras.Input(shape=(756,), dtype=tf.float32, name="features")
    values = normalization(inputs)
    for index, units in enumerate(spec.hidden_units):
        values = tf.keras.layers.Dense(
            units, activation="relu", name=f"dense_{index + 1}"
        )(values)
        values = tf.keras.layers.Dropout(
            spec.dropout, name=f"dropout_{index + 1}"
        )(values)
    outputs = tf.keras.layers.Dense(
        OUTPUT_CLASSES, activation="softmax", name="probabilities"
    )(values)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=spec.learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


def _macro_f1_callback(tf: Any, X_val: np.ndarray, y_val: np.ndarray) -> Any:
    from sklearn.metrics import f1_score

    class ValidationMacroF1(tf.keras.callbacks.Callback):
        def on_epoch_end(self, epoch: int, logs: dict[str, float] | None = None) -> None:
            values = logs if logs is not None else {}
            probabilities = self.model.predict(X_val, verbose=0)
            predictions = np.argmax(probabilities, axis=1)
            score = float(
                f1_score(
                    y_val,
                    predictions,
                    labels=list(range(OUTPUT_CLASSES)),
                    average="macro",
                    zero_division=0,
                )
            )
            values["val_macro_f1"] = score
            print(f" - val_macro_f1: {score:.4f}")

    return ValidationMacroF1()


def _balanced_class_weights(y: np.ndarray) -> dict[int, float]:
    counts = Counter(y.astype(int).tolist())
    if set(counts) != set(range(OUTPUT_CLASSES)):
        raise ValueError("Every final class must appear in training.")
    total = len(y)
    return {
        index: total / (OUTPUT_CLASSES * counts[index])
        for index in range(OUTPUT_CLASSES)
    }


def _select_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        results,
        key=lambda item: (
            item["validation_macro_f1"],
            item["validation_accuracy"],
            -item["validation_high_confidence_wrong"],
            -item["keras_model_size_bytes"],
        ),
    )


def _prediction_rows(
    dataset: dict[str, np.ndarray],
    probabilities: np.ndarray,
    threshold: float,
    margin_threshold: float,
) -> list[dict[str, object]]:
    order = np.argsort(probabilities, axis=1)[:, ::-1]
    rows = []
    for index, probability in enumerate(probabilities):
        top1 = int(order[index, 0])
        top2 = int(order[index, 1])
        confidence = float(probability[top1])
        second = float(probability[top2])
        margin = confidence - second
        accepted = confidence >= threshold and margin >= margin_threshold
        actual = int(dataset["y"][index])
        rows.append(
            {
                "sample_id": str(dataset["sample_ids"][index]),
                "actual_label": FINAL_LABELS[actual],
                "actual_index": actual,
                "predicted_label": FINAL_LABELS[top1],
                "predicted_index": top1,
                "confidence": confidence,
                "second_label": FINAL_LABELS[top2],
                "second_confidence": second,
                "margin": margin,
                "accepted": accepted,
                "correct": top1 == actual,
            }
        )
    return rows


def _write_confidence_analysis(plt: Any, winner: dict[str, Any]) -> dict[str, Any]:
    validation = _load_feature_file(PHONE_VALIDATION_FEATURES, 200)
    probabilities = winner["probabilities"]
    grid_rows = []
    for threshold in MINIMUM_CONFIDENCE_GRID:
        for margin_threshold in TOP2_MARGIN_GRID:
            rows = _prediction_rows(
                validation, probabilities, threshold, margin_threshold
            )
            accepted = [row for row in rows if row["accepted"]]
            grid_rows.append(
                {
                    "minimum_confidence": threshold,
                    "minimum_top2_margin": margin_threshold,
                    "accepted_samples": len(accepted),
                    "coverage": len(accepted) / len(rows),
                    "accepted_accuracy": (
                        sum(bool(row["correct"]) for row in accepted) / len(accepted)
                        if accepted
                        else 0.0
                    ),
                    "rejection_rate": 1.0 - (len(accepted) / len(rows)),
                    "high_confidence_wrong": sum(
                        not bool(row["correct"]) for row in accepted
                    ),
                }
            )
    eligible = [
        row for row in grid_rows if row["coverage"] >= MINIMUM_CALIBRATION_COVERAGE
    ]
    recommendation = max(
        eligible,
        key=lambda row: (
            row["accepted_accuracy"],
            row["coverage"],
            -row["minimum_confidence"],
            -row["minimum_top2_margin"],
        ),
    )
    recommendation = {
        **recommendation,
        "selected_using": "phone validation only",
        "minimum_required_coverage": MINIMUM_CALIBRATION_COVERAGE,
        "explanation": (
            "Highest accepted validation accuracy among candidates with at least "
            "70% coverage; ties prefer higher coverage and less restrictive thresholds."
        ),
    }
    write_csv(
        METRICS_DIR / "validation_confidence_analysis.csv",
        grid_rows,
        list(grid_rows[0]),
    )
    write_json(METADATA_DIR / "confidence_recommendation.json", recommendation)

    rows = _prediction_rows(validation, probabilities, 0.0, 0.0)
    correct_confidence = [row["confidence"] for row in rows if row["correct"]]
    wrong_confidence = [row["confidence"] for row in rows if not row["correct"]]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(correct_confidence, bins=10, alpha=0.75, label="Correct")
    if wrong_confidence:
        axes[0].hist(wrong_confidence, bins=10, alpha=0.75, label="Incorrect")
    axes[0].set_title("Validation confidence distribution")
    axes[0].set_xlabel("Top-1 probability")
    axes[0].legend()
    axes[1].plot(
        [row["coverage"] for row in grid_rows],
        [row["accepted_accuracy"] for row in grid_rows],
        "o",
    )
    axes[1].set_title("Validation coverage vs accepted accuracy")
    axes[1].set_xlabel("Coverage")
    axes[1].set_ylabel("Accepted accuracy")
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "confidence_analysis.png", dpi=160)
    plt.close(figure)
    return recommendation


def _comparison_row(result: dict[str, Any]) -> dict[str, object]:
    return {
        "experiment_id": result["experiment_id"],
        "dataset_composition": "; ".join(result["dataset_composition"]),
        "real_train": result["real_phone_training_samples"],
        "augmented_train": result["augmented_phone_training_samples"],
        "historical_train": result["historical_training_samples"],
        "effective_train": result["effective_training_samples"],
        "validation_samples": result["validation_samples"],
        "validation_accuracy": result["validation_accuracy"],
        "validation_macro_precision": result["validation_macro_precision"],
        "validation_macro_recall": result["validation_macro_recall"],
        "validation_macro_f1": result["validation_macro_f1"],
        "validation_weighted_f1": result["validation_weighted_f1"],
        "high_confidence_wrong": result["validation_high_confidence_wrong"],
        "model_size_bytes": result["keras_model_size_bytes"],
        "parameter_count": result["parameter_count"],
        "training_duration_seconds": result["training_duration_seconds"],
        "best_epoch": result["best_epoch"],
    }


def _write_matrix(path: Path, matrix: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["actual_label", *FINAL_LABELS])
        for index, row in enumerate(matrix):
            writer.writerow([FINAL_LABELS[index], *row.astype(int).tolist()])


def _plot_history(plt: Any, history: dict[str, list[float]], path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(history["loss"], label="train")
    axes[0].plot(history["val_loss"], label="validation")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[1].plot(history["accuracy"], label="train accuracy")
    axes[1].plot(history["val_accuracy"], label="validation accuracy")
    axes[1].plot(history["val_macro_f1"], label="validation macro F1")
    axes[1].set_title("Validation selection metrics")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _write_training_configuration(
    tf: Any,
    sklearn: Any,
    args: argparse.Namespace,
    winner: dict[str, Any],
    locked_model: Path,
    tuning_used: bool,
) -> None:
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = "unavailable"
    write_json(
        METADATA_DIR / "training_configuration.json",
        {
            "project": "SignSync",
            "sprint": "2.17",
            "created_at": utc_now(),
            "training_script": relative_path(Path(__file__)),
            "git_commit": git_commit,
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "seed": SEED,
            "dataset_order_seed": SEED,
            "input_shape": [1, 756],
            "output_shape": [1, 40],
            "dtype": "float32",
            "feature_order": FEATURE_ORDER,
            "architecture": winner["hidden_units"],
            "dropout": winner["dropout"],
            "optimizer": "Adam",
            "learning_rate": winner["learning_rate"],
            "batch_size": winner["batch_size"],
            "maximum_epochs": args.epochs,
            "early_stopping_monitor": "validation macro F1",
            "early_stopping_patience": args.patience,
            "loss": "SparseCategoricalCrossentropy",
            "class_weighting": "balanced inverse-frequency",
            "winning_experiment": winner["experiment_id"],
            "best_epoch": winner["best_epoch"],
            "bounded_tuning_triggered": tuning_used,
            "locked_model": relative_path(locked_model),
            "test_evaluation_status": "not_run",
            "deployment_status": "candidate_not_deployed",
        },
    )
    write_json(METADATA_DIR / "labels_40.json", FINAL_LABELS)
    (METADATA_DIR / "labels_40.txt").write_text(
        "\n".join(FINAL_LABELS) + "\n", encoding="utf-8"
    )


def _write_model_selection_report(
    results: list[dict[str, Any]],
    winner: dict[str, Any],
    confidence: dict[str, Any],
    tuning_used: bool,
) -> None:
    rows = "\n".join(
        "| {experiment_id} | {effective_training_samples} | {validation_accuracy:.4f} | "
        "{validation_macro_f1:.4f} | {validation_high_confidence_wrong} | "
        "{best_epoch} |".format(**result)
        for result in results
    )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "model_selection_report.md").write_text(
        f"""# Sprint 2.17 Validation-Based Model Selection

## Test-Set Protection

The locked 200-sample phone test set was not opened by training, early stopping, model comparison, confidence calibration, or winner selection.

## Comparison

| Experiment | Effective train | Validation accuracy | Validation macro F1 | High-confidence wrong | Best epoch |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

## Locked Winner

- Experiment: `{winner['experiment_id']}`
- Validation macro F1: {winner['validation_macro_f1']:.4f}
- Validation accuracy: {winner['validation_accuracy']:.4f}
- Selection reason: highest validation macro F1, followed by the declared tie-breakers.
- Bounded tuning triggered: {tuning_used}
- Test evaluation status: not run

## Confidence Recommendation

- Minimum confidence: {confidence['minimum_confidence']:.2f}
- Minimum top-2 margin: {confidence['minimum_top2_margin']:.2f}
- Validation coverage: {confidence['coverage']:.4f}
- Accepted validation accuracy: {confidence['accepted_accuracy']:.4f}
- Rejection rate: {confidence['rejection_rate']:.4f}

The winner is locked and must not be altered before the one-time test evaluation.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

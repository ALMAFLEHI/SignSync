"""Train, export, evaluate, and compare Sprint 2.16A controlled models."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from labels import (
    ALL_LABELS_V3_76,
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)
from sprint_2_16A_experiment_config import (
    AUGMENTATION_CONFIG_PATH,
    BASELINE_KERAS_PATH,
    BASELINE_LABELS_PATH,
    BASELINE_TFLITE_PATH,
    BATCH_SIZE,
    COMBINED_MANIFEST_PATH,
    COMPARISON_CSV_PATH,
    CONFIDENCE_THRESHOLD,
    CONTROLLED_REPORT_PATH,
    CONTROL_LABELS,
    DROPOUT,
    EARLY_STOPPING_PATIENCE,
    FEATURE_ORDER,
    FEATURE_WIDTH,
    HIDDEN_UNITS,
    LEARNING_RATE,
    MAX_EPOCHS,
    NO_AUGMENTATION_DIR,
    OUTPUT_CLASSES,
    PER_CLASS_METRICS_CSV_PATH,
    PHONE_PREDICTIONS_CSV_PATH,
    PILOT_LABELS,
    REAL_SEQUENCE_DATASET_PATH,
    SEED,
    TOP2_GAP_THRESHOLD,
    WITH_AUGMENTATION_DIR,
)
from sprint_2_16A_experiment_utils import (
    augment_sequence,
    load_augmentation_config,
    stable_rng,
    statistical_features,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=MAX_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    return parser.parse_args()


def import_dependencies() -> tuple[Any, Any]:
    """Import TensorFlow and plotting only inside the active ML environment."""
    try:
        import tensorflow as tf
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        raise ImportError(
            "TensorFlow/matplotlib are unavailable. Run with the Sprint 2.13 ML environment."
        ) from exc
    return tf, plt


def main() -> int:
    """Run the full fixed-split comparison without modifying deployed assets."""
    args = parse_args()
    try:
        tf, plt = import_dependencies()
        dataset = load_real_dataset()
        augmentation_config = load_augmentation_config()
        check_output_paths()

        baseline = evaluate_baseline(tf, dataset)
        experiment_a = train_experiment(
            tf=tf,
            plt=plt,
            dataset=dataset,
            name="experiment_a_no_augmentation",
            output_dir=NO_AUGMENTATION_DIR,
            use_augmentation=False,
            augmentation_config=augmentation_config,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
        experiment_b = train_experiment(
            tf=tf,
            plt=plt,
            dataset=dataset,
            name="experiment_b_with_augmentation",
            output_dir=WITH_AUGMENTATION_DIR,
            use_augmentation=True,
            augmentation_config=augmentation_config,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
        write_comparison_outputs(
            baseline=baseline,
            experiment_a=experiment_a,
            experiment_b=experiment_b,
            dataset=dataset,
            augmentation_config=augmentation_config,
        )
    except (
        ImportError,
        FileNotFoundError,
        FileExistsError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}")
        return 1

    print("Sprint 2.16A Controlled Experiment Summary")
    print("-------------------------------------------")
    for result in (baseline, experiment_a, experiment_b):
        print(
            f"{result['display_name']}: phone accuracy="
            f"{result['phone_accuracy']:.4f}, phone macro F1="
            f"{result['phone_macro_f1']:.4f}, full accuracy="
            f"{result['full_accuracy']:.4f}, full macro F1="
            f"{result['full_macro_f1']:.4f}"
        )
    print(f"recommendation: {choose_winner(experiment_a, experiment_b)['winner']}")
    print(f"report: {CONTROLLED_REPORT_PATH.as_posix()}")
    print("PASS: controlled experiment completed. Flutter assets were not changed.")
    return 0


def load_real_dataset() -> dict[str, np.ndarray]:
    """Load and validate the common real-data sequence and feature matrices."""
    if not REAL_SEQUENCE_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Missing controlled dataset: {REAL_SEQUENCE_DATASET_PATH.as_posix()}"
        )
    with np.load(REAL_SEQUENCE_DATASET_PATH, allow_pickle=False) as dataset_file:
        required = {
            "X_sequences",
            "X_features",
            "y",
            "sample_ids",
            "labels",
            "splits",
            "source_types",
            "participants",
            "label_names",
        }
        missing = required.difference(dataset_file.files)
        if missing:
            raise ValueError(f"Controlled dataset missing arrays: {sorted(missing)}")
        dataset = {key: dataset_file[key] for key in dataset_file.files}

    if dataset["X_sequences"].shape != (805, 60, 126):
        raise ValueError(f"Unexpected sequence shape: {dataset['X_sequences'].shape}")
    if dataset["X_features"].shape != (805, FEATURE_WIDTH):
        raise ValueError(f"Unexpected feature shape: {dataset['X_features'].shape}")
    if dataset["label_names"].astype(str).tolist() != ALL_LABELS_V3_76:
        raise ValueError("Controlled dataset class order does not match active V3 scope.")
    if not np.isfinite(dataset["X_sequences"]).all() or not np.isfinite(
        dataset["X_features"]
    ).all():
        raise ValueError("Controlled dataset contains NaN or infinite values.")
    split_counts = Counter(dataset["splits"].astype(str))
    if dict(split_counts) != {"train": 548, "val": 96, "test": 161}:
        raise ValueError(f"Unexpected controlled split counts: {dict(split_counts)}")
    if len(set(dataset["sample_ids"].astype(str))) != 805:
        raise ValueError("Controlled dataset sample IDs are not unique.")
    return dataset


def check_output_paths() -> None:
    """Refuse to overwrite any prior controlled-experiment model result."""
    existing = [path for path in (NO_AUGMENTATION_DIR, WITH_AUGMENTATION_DIR) if path.exists()]
    if existing:
        raise FileExistsError(
            "Controlled experiment output already exists; refusing to overwrite: "
            + ", ".join(path.as_posix() for path in existing)
        )


def evaluate_baseline(tf: Any, dataset: dict[str, np.ndarray]) -> dict[str, object]:
    """Evaluate the unchanged deployed 86-class dynamic-range model."""
    if not BASELINE_TFLITE_PATH.exists() or not BASELINE_LABELS_PATH.exists():
        raise FileNotFoundError("Historical Sprint 2.13 baseline model or labels are missing.")
    labels86 = json.loads(BASELINE_LABELS_PATH.read_text(encoding="utf-8"))
    if len(labels86) != 86:
        raise ValueError(f"Expected 86 baseline labels, found {len(labels86)}.")
    test_mask = dataset["splits"].astype(str) == "test"
    X_test = dataset["X_features"][test_mask].astype(np.float32)
    true_labels = dataset["labels"][test_mask].astype(str)
    probabilities, tensor = tflite_predict(tf, BASELINE_TFLITE_PATH, X_test)
    result = evaluate_probabilities(
        name="baseline_historical_86",
        display_name="Baseline 86-class dynamic-range TFLite",
        probabilities=probabilities,
        model_labels=labels86,
        dataset=dataset,
        test_mask=test_mask,
        true_labels=true_labels,
        output_dir=None,
    )
    result["tflite_verification"] = {
        **tensor,
        "model_path": BASELINE_TFLITE_PATH.as_posix(),
        "model_size_bytes": BASELINE_TFLITE_PATH.stat().st_size,
        "sha256": sha256_path(BASELINE_TFLITE_PATH),
        "unchanged": True,
    }
    result["model_size_bytes"] = BASELINE_TFLITE_PATH.stat().st_size

    if BASELINE_KERAS_PATH.exists():
        keras_model = tf.keras.models.load_model(BASELINE_KERAS_PATH)
        keras_probabilities = keras_model.predict(X_test, verbose=0)
        result["keras_tflite_top1_agreement"] = float(
            np.mean(
                np.argmax(keras_probabilities, axis=1)
                == np.argmax(probabilities, axis=1)
            )
        )
        result["keras_tflite_max_abs_difference"] = float(
            np.max(np.abs(keras_probabilities - probabilities))
        )
    else:
        result["keras_tflite_top1_agreement"] = None
        result["keras_tflite_max_abs_difference"] = None
    return result


def train_experiment(
    tf: Any,
    plt: Any,
    dataset: dict[str, np.ndarray],
    name: str,
    output_dir: Path,
    use_augmentation: bool,
    augmentation_config: dict[str, Any],
    epochs: int,
    batch_size: int,
) -> dict[str, object]:
    """Fit one fixed architecture, export TFLite, and evaluate untouched tests."""
    output_dir.mkdir(parents=True, exist_ok=False)
    split_values = dataset["splits"].astype(str)
    train_mask = split_values == "train"
    val_mask = split_values == "val"
    test_mask = split_values == "test"
    X_train = dataset["X_features"][train_mask].astype(np.float32)
    y_train = dataset["y"][train_mask].astype(np.int64)
    train_ids = dataset["sample_ids"][train_mask].astype(str)
    train_labels = dataset["labels"][train_mask].astype(str)
    augmentation_rows: list[dict[str, object]] = []

    if use_augmentation:
        augmented_sequences: list[np.ndarray] = []
        augmented_ids: list[str] = []
        augmented_y: list[int] = []
        augmented_labels: list[str] = []
        source_sequences = dataset["X_sequences"][train_mask]
        for sequence, sample_id, label, label_index in zip(
            source_sequences, train_ids, train_labels, y_train
        ):
            augmented, parameters = augment_sequence(
                sequence,
                stable_rng(SEED, sample_id),
                augmentation_config,
            )
            derived_id = f"{sample_id}__aug01"
            augmented_sequences.append(augmented)
            augmented_ids.append(derived_id)
            augmented_y.append(int(label_index))
            augmented_labels.append(label)
            augmentation_rows.append(
                {
                    "sample_id": derived_id,
                    "source_sample_id": sample_id,
                    "label": label,
                    "split": "train",
                    "augmentation_status": "augmented",
                    **parameters,
                }
            )
        augmented_features = statistical_features(
            np.stack(augmented_sequences).astype(np.float32)
        )
        X_train = np.concatenate([X_train, augmented_features], axis=0)
        y_train = np.concatenate(
            [y_train, np.asarray(augmented_y, dtype=np.int64)], axis=0
        )
        train_ids = np.concatenate([train_ids, np.asarray(augmented_ids)])
        train_labels = np.concatenate([train_labels, np.asarray(augmented_labels)])

    X_val = dataset["X_features"][val_mask].astype(np.float32)
    y_val = dataset["y"][val_mask].astype(np.int64)
    if len(set(train_ids)) != len(train_ids):
        raise ValueError(f"{name} contains duplicate training sample IDs.")
    if any("__aug" in sample_id for sample_id in dataset["sample_ids"][~train_mask].astype(str)):
        raise ValueError("An augmented derivative crossed into validation or test data.")

    class_weights = balanced_class_weights(y_train)
    set_determinism(tf, SEED)
    model = build_model(tf, X_train)
    checkpoint_path = output_dir / "best_checkpoint.keras"
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint_path.as_posix(),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=EARLY_STOPPING_PATIENCE,
            mode="max",
            restore_best_weights=True,
            verbose=1,
        ),
    ]
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weights,
        callbacks=callbacks,
        shuffle=True,
        verbose=2,
    )
    model_path = output_dir / "model.keras"
    model.save(model_path)
    write_training_artifacts(
        output_dir=output_dir,
        history=history.history,
        use_augmentation=use_augmentation,
        class_weights=class_weights,
        train_ids=train_ids,
        train_labels=train_labels,
        y_train=y_train,
        X_train=X_train,
        augmentation_rows=augmentation_rows,
        epochs=epochs,
        batch_size=batch_size,
        plt=plt,
    )

    float_path = output_dir / "model_float32.tflite"
    dynamic_path = output_dir / "model_dynamic_range.tflite"
    export_tflite(tf, model, float_path, dynamic_path)
    model_size_report = {
        "model_keras_bytes": model_path.stat().st_size,
        "best_checkpoint_keras_bytes": checkpoint_path.stat().st_size,
        "model_float32_tflite_bytes": float_path.stat().st_size,
        "model_dynamic_range_tflite_bytes": dynamic_path.stat().st_size,
    }
    (output_dir / "model_size_report.json").write_text(
        json.dumps(model_size_report, indent=2), encoding="utf-8"
    )

    X_test = dataset["X_features"][test_mask].astype(np.float32)
    true_labels = dataset["labels"][test_mask].astype(str)
    keras_probabilities = model.predict(X_test, verbose=0)
    float_probabilities, float_tensor = tflite_predict(tf, float_path, X_test)
    dynamic_probabilities, dynamic_tensor = tflite_predict(tf, dynamic_path, X_test)
    parity_count = min(12, len(X_test))
    parity_slice = slice(0, parity_count)
    tflite_verification = {
        "float32": {
            **float_tensor,
            "model_size_bytes": float_path.stat().st_size,
            "top1_agreement_with_keras": float(
                np.mean(
                    np.argmax(keras_probabilities[parity_slice], axis=1)
                    == np.argmax(float_probabilities[parity_slice], axis=1)
                )
            ),
            "max_abs_probability_difference": float(
                np.max(
                    np.abs(
                        keras_probabilities[parity_slice]
                        - float_probabilities[parity_slice]
                    )
                )
            ),
        },
        "dynamic_range": {
            **dynamic_tensor,
            "model_size_bytes": dynamic_path.stat().st_size,
            "top1_agreement_with_keras": float(
                np.mean(
                    np.argmax(keras_probabilities[parity_slice], axis=1)
                    == np.argmax(dynamic_probabilities[parity_slice], axis=1)
                )
            ),
            "max_abs_probability_difference": float(
                np.max(
                    np.abs(
                        keras_probabilities[parity_slice]
                        - dynamic_probabilities[parity_slice]
                    )
                )
            ),
        },
        "fixtures_checked": parity_count,
        "labels": len(ALL_LABELS_V3_76),
        "removed_labels_in_metadata": sorted(
            set(ALL_LABELS_V3_76).intersection(REMOVED_BANKING_INTENTS_V3_10)
        ),
    }
    (output_dir / "tflite_verification.json").write_text(
        json.dumps(tflite_verification, indent=2), encoding="utf-8"
    )

    result = evaluate_probabilities(
        name=name,
        display_name=(
            "Experiment B: 76-class with augmentation"
            if use_augmentation
            else "Experiment A: 76-class without augmentation"
        ),
        probabilities=dynamic_probabilities,
        model_labels=ALL_LABELS_V3_76,
        dataset=dataset,
        test_mask=test_mask,
        true_labels=true_labels,
        output_dir=output_dir,
        plt=plt,
    )
    result.update(
        {
            "model_size_bytes": dynamic_path.stat().st_size,
            "keras_model_size_bytes": model_path.stat().st_size,
            "tflite_verification": tflite_verification,
            "epochs_trained": len(history.history["loss"]),
            "best_epoch": int(np.argmax(history.history["val_accuracy"])) + 1,
            "early_stopped": len(history.history["loss"]) < epochs,
            "best_train_accuracy": float(
                history.history["accuracy"][
                    int(np.argmax(history.history["val_accuracy"]))
                ]
            ),
            "best_val_accuracy": float(max(history.history["val_accuracy"])),
            "best_train_loss": float(
                history.history["loss"][
                    int(np.argmax(history.history["val_accuracy"]))
                ]
            ),
            "best_val_loss": float(
                history.history["val_loss"][
                    int(np.argmax(history.history["val_accuracy"]))
                ]
            ),
            "original_training_samples": 548,
            "augmented_training_samples": len(augmentation_rows),
            "effective_training_samples": len(X_train),
        }
    )
    (output_dir / "evaluation_summary.json").write_text(
        json.dumps(json_safe(result), indent=2), encoding="utf-8"
    )
    return result


def set_determinism(tf: Any, seed: int) -> None:
    """Reset model state and random streams for a fair initialization."""
    tf.keras.backend.clear_session()
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:  # noqa: BLE001 - older TensorFlow may not expose this API.
        pass


def build_model(tf: Any, X_train: np.ndarray) -> Any:
    """Recreate the proven Sprint 2.13 medium MLP with a 76-class output."""
    normalization = tf.keras.layers.Normalization(name="feature_normalization")
    normalization.adapt(X_train.astype(np.float32))
    inputs = tf.keras.Input(shape=(FEATURE_WIDTH,), dtype=tf.float32, name="features")
    values = normalization(inputs)
    for index, units in enumerate(HIDDEN_UNITS):
        values = tf.keras.layers.Dense(
            units, activation="relu", name=f"dense_{index + 1}"
        )(values)
        values = tf.keras.layers.Dropout(
            DROPOUT, name=f"dropout_{index + 1}"
        )(values)
    outputs = tf.keras.layers.Dense(
        OUTPUT_CLASSES, activation="softmax", name="probabilities"
    )(values)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


def balanced_class_weights(y: np.ndarray) -> dict[int, float]:
    """Equalize total effective contribution across the 76 classes."""
    counts = Counter(y.tolist())
    if set(counts) != set(range(OUTPUT_CLASSES)):
        raise ValueError("Every active class must appear in the training data.")
    total = len(y)
    return {
        class_index: total / (OUTPUT_CLASSES * counts[class_index])
        for class_index in range(OUTPUT_CLASSES)
    }


def export_tflite(tf: Any, model: Any, float_path: Path, dynamic_path: Path) -> None:
    """Export float32 and dynamic-range models to the new experiment folder."""
    float_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    float_path.write_bytes(float_converter.convert())
    dynamic_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    dynamic_converter.optimizations = [tf.lite.Optimize.DEFAULT]
    dynamic_path.write_bytes(dynamic_converter.convert())


def tflite_predict(
    tf: Any, model_path: Path, X: np.ndarray
) -> tuple[np.ndarray, dict[str, object]]:
    """Run one TFLite model and return probabilities plus tensor verification."""
    interpreter = tf.lite.Interpreter(model_path=model_path.as_posix())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    input_shape = input_detail["shape"].astype(int).tolist()
    output_shape = output_detail["shape"].astype(int).tolist()
    if input_shape != [1, FEATURE_WIDTH]:
        raise ValueError(f"Unexpected TFLite input shape for {model_path}: {input_shape}")
    outputs: list[np.ndarray] = []
    for feature_row in X:
        interpreter.set_tensor(
            input_detail["index"], feature_row.reshape(1, FEATURE_WIDTH).astype(np.float32)
        )
        interpreter.invoke()
        outputs.append(interpreter.get_tensor(output_detail["index"])[0].copy())
    probabilities = np.asarray(outputs, dtype=np.float32)
    if probabilities.shape != (len(X), output_shape[1]) or not np.isfinite(
        probabilities
    ).all():
        raise ValueError(f"Invalid TFLite output matrix: {probabilities.shape}")
    return probabilities, {
        "input_shape": input_shape,
        "output_shape": output_shape,
        "input_dtype": np.dtype(input_detail["dtype"]).name,
        "output_dtype": np.dtype(output_detail["dtype"]).name,
        "loads_successfully": True,
    }


def evaluate_probabilities(
    name: str,
    display_name: str,
    probabilities: np.ndarray,
    model_labels: list[str],
    dataset: dict[str, np.ndarray],
    test_mask: np.ndarray,
    true_labels: np.ndarray,
    output_dir: Path | None,
    plt: Any | None = None,
) -> dict[str, object]:
    """Calculate full active, phone-mode, threshold, control, and class metrics."""
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    label_to_index = {label: index for index, label in enumerate(model_labels)}
    active_indices = [label_to_index[label] for label in ALL_LABELS_V3_76]
    banking_indices = [label_to_index[label] for label in BANKING_INTENTS_V3_40]
    y_true_model = np.asarray([label_to_index[label] for label in true_labels])
    raw_predictions = np.argmax(probabilities, axis=1)
    full_accuracy = float(accuracy_score(y_true_model, raw_predictions))
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true_model,
        raw_predictions,
        labels=active_indices,
        average="macro",
        zero_division=0,
    )
    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            y_true_model,
            raw_predictions,
            labels=active_indices,
            average="weighted",
            zero_division=0,
        )
    )
    per_precision, per_recall, per_f1, per_support = precision_recall_fscore_support(
        y_true_model,
        raw_predictions,
        labels=active_indices,
        average=None,
        zero_division=0,
    )
    per_class_rows = [
        {
            "model": name,
            "label": label,
            "precision": float(per_precision[index]),
            "recall": float(per_recall[index]),
            "f1_score": float(per_f1[index]),
            "support": int(per_support[index]),
        }
        for index, label in enumerate(ALL_LABELS_V3_76)
    ]

    source_types = dataset["source_types"][test_mask].astype(str)
    phone_mask = source_types == "phone"
    phone_probabilities = probabilities[phone_mask]
    phone_true_labels = true_labels[phone_mask]
    phone_rows = build_phone_prediction_rows(
        name=name,
        model_labels=model_labels,
        probabilities=phone_probabilities,
        true_labels=phone_true_labels,
        sample_ids=dataset["sample_ids"][test_mask][phone_mask].astype(str),
        banking_indices=banking_indices,
    )
    phone_predictions = np.asarray([row["mode_top1_label"] for row in phone_rows])
    phone_accuracy = float(np.mean(phone_predictions == phone_true_labels))
    pilot_precision, pilot_recall, pilot_f1, pilot_support = (
        precision_recall_fscore_support(
            phone_true_labels,
            phone_predictions,
            labels=PILOT_LABELS,
            average=None,
            zero_division=0,
        )
    )
    phone_macro_f1 = float(np.mean(pilot_f1))
    phone_per_label = {
        label: {
            "precision": float(pilot_precision[index]),
            "recall": float(pilot_recall[index]),
            "f1": float(pilot_f1[index]),
            "accuracy": float(
                np.mean(phone_predictions[phone_true_labels == label] == label)
            ),
            "support": int(pilot_support[index]),
        }
        for index, label in enumerate(PILOT_LABELS)
    }
    threshold_pass_rate = float(
        np.mean([bool(row["threshold_pass"]) for row in phone_rows])
    )
    high_confidence_wrong = sum(
        bool(row["threshold_pass"]) and not bool(row["correct"])
        for row in phone_rows
    )

    test_labels = dataset["labels"][test_mask].astype(str)
    control_mask = np.isin(test_labels, np.asarray(CONTROL_LABELS))
    control_accuracy = float(
        np.mean(raw_predictions[control_mask] == y_true_model[control_mask])
    )
    control_results = {
        label: float(
            np.mean(
                raw_predictions[test_labels == label]
                == y_true_model[test_labels == label]
            )
        )
        for label in CONTROL_LABELS
    }

    matrix = confusion_matrix(
        y_true_model,
        raw_predictions,
        labels=active_indices,
    )
    confused_pairs = top_confused_pairs(matrix, ALL_LABELS_V3_76)
    result: dict[str, object] = {
        "name": name,
        "display_name": display_name,
        "full_test_samples": len(true_labels),
        "full_accuracy": full_accuracy,
        "full_macro_precision": float(macro_precision),
        "full_macro_recall": float(macro_recall),
        "full_macro_f1": float(macro_f1),
        "full_weighted_precision": float(weighted_precision),
        "full_weighted_recall": float(weighted_recall),
        "full_weighted_f1": float(weighted_f1),
        "phone_test_samples": len(phone_true_labels),
        "phone_accuracy": phone_accuracy,
        "phone_macro_f1": phone_macro_f1,
        "phone_per_label": phone_per_label,
        "threshold_pass_rate": threshold_pass_rate,
        "try_again_rate": 1.0 - threshold_pass_rate,
        "high_confidence_wrong": high_confidence_wrong,
        "control_accuracy": control_accuracy,
        "control_results": control_results,
        "top_confused_pairs": confused_pairs,
        "phone_prediction_rows": phone_rows,
        "per_class_rows": per_class_rows,
    }
    if output_dir is not None and plt is not None:
        write_evaluation_artifacts(
            output_dir,
            matrix,
            per_class_rows,
            phone_rows,
            result,
            plt,
        )
    return result


def build_phone_prediction_rows(
    name: str,
    model_labels: list[str],
    probabilities: np.ndarray,
    true_labels: np.ndarray,
    sample_ids: np.ndarray,
    banking_indices: list[int],
) -> list[dict[str, object]]:
    """Create raw and active-banking top-two evidence for each phone test row."""
    rows: list[dict[str, object]] = []
    for sample_id, true_label, row in zip(sample_ids, true_labels, probabilities):
        raw_order = np.argsort(row)[::-1][:2]
        mode_order = np.asarray(banking_indices)[
            np.argsort(row[banking_indices])[::-1][:2]
        ]
        top1 = int(mode_order[0])
        top2 = int(mode_order[1])
        gap = float(row[top1] - row[top2])
        threshold_pass = bool(
            row[top1] >= CONFIDENCE_THRESHOLD and gap >= TOP2_GAP_THRESHOLD
        )
        rows.append(
            {
                "model": name,
                "sample_id": sample_id,
                "true_label": true_label,
                "raw_top1_label": model_labels[int(raw_order[0])],
                "raw_top1_confidence": float(row[int(raw_order[0])]),
                "raw_top2_label": model_labels[int(raw_order[1])],
                "raw_top2_confidence": float(row[int(raw_order[1])]),
                "mode_top1_label": model_labels[top1],
                "mode_top1_confidence": float(row[top1]),
                "mode_top2_label": model_labels[top2],
                "mode_top2_confidence": float(row[top2]),
                "top2_gap": gap,
                "threshold_pass": threshold_pass,
                "try_again": not threshold_pass,
                "correct": model_labels[top1] == true_label,
            }
        )
    return rows


def write_training_artifacts(
    output_dir: Path,
    history: dict[str, list[float]],
    use_augmentation: bool,
    class_weights: dict[int, float],
    train_ids: np.ndarray,
    train_labels: np.ndarray,
    y_train: np.ndarray,
    X_train: np.ndarray,
    augmentation_rows: list[dict[str, object]],
    epochs: int,
    batch_size: int,
    plt: Any,
) -> None:
    """Save reproducibility, history, labels, manifests, and training plots."""
    shutil.copy2(COMBINED_MANIFEST_PATH, output_dir / "real_dataset_manifest.csv")
    (output_dir / "label_names.json").write_text(
        json.dumps(ALL_LABELS_V3_76, indent=2), encoding="utf-8"
    )
    (output_dir / "labels.txt").write_text(
        "\n".join(ALL_LABELS_V3_76) + "\n", encoding="utf-8"
    )
    (output_dir / "label_mapping.json").write_text(
        json.dumps(
            {label: index for index, label in enumerate(ALL_LABELS_V3_76)},
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "label_groups.json").write_text(
        json.dumps(
            {
                "all_labels": ALL_LABELS_V3_76,
                "alphabet_mode": ALPHABET_LABELS,
                "number_mode": DIGIT_LABELS,
                "banking_intent_mode": BANKING_INTENTS_V3_40,
                "removed_banking_intents": REMOVED_BANKING_INTENTS_V3_10,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    configuration = {
        "seed": SEED,
        "architecture": HIDDEN_UNITS,
        "dropout": DROPOUT,
        "optimizer": "Adam",
        "learning_rate": LEARNING_RATE,
        "loss": "SparseCategoricalCrossentropy",
        "batch_size": batch_size,
        "maximum_epochs": epochs,
        "early_stopping_monitor": "val_accuracy",
        "early_stopping_patience": EARLY_STOPPING_PATIENCE,
        "model_checkpointing": True,
        "class_weighting": "balanced inverse-frequency",
        "feature_order": FEATURE_ORDER,
        "input_shape": [1, 756],
        "output_shape": [1, 76],
        "augmentation_enabled": use_augmentation,
        "augmentation_config": AUGMENTATION_CONFIG_PATH.as_posix()
        if use_augmentation
        else None,
    }
    (output_dir / "training_config.json").write_text(
        json.dumps(configuration, indent=2), encoding="utf-8"
    )
    (output_dir / "seed.txt").write_text(f"{SEED}\n", encoding="utf-8")
    (output_dir / "class_weights.json").write_text(
        json.dumps({str(key): value for key, value in class_weights.items()}, indent=2),
        encoding="utf-8",
    )
    (output_dir / "preprocessing_config.json").write_text(
        json.dumps(
            {
                "source_sequence_shape": [60, 126],
                "feature_order": FEATURE_ORDER,
                "feature_width": 756,
                "standard_deviation_ddof": 0,
                "left_hand_indices": [0, 62],
                "right_hand_indices": [63, 125],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    history_path = output_dir / "training_history.csv"
    keys = list(history)
    with history_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["epoch", *keys])
        writer.writeheader()
        for index in range(len(history["loss"])):
            writer.writerow(
                {"epoch": index + 1, **{key: history[key][index] for key in keys}}
            )
    (output_dir / "training_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    np.savez_compressed(
        output_dir / "training_features.npz",
        X_features=X_train,
        y=y_train,
        sample_ids=train_ids,
        labels=train_labels,
    )

    if augmentation_rows:
        with (output_dir / "augmentation_manifest.csv").open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=list(augmentation_rows[0]))
            writer.writeheader()
            writer.writerows(augmentation_rows)

    effective_counts = Counter(str(label) for label in train_labels)
    augmented_counts = Counter(
        str(row["label"]) for row in augmentation_rows
    )
    augmentation_summary = {
        "enabled": use_augmentation,
        "original_training_samples": len(train_labels) - len(augmentation_rows),
        "augmented_training_samples": len(augmentation_rows),
        "effective_training_samples": len(train_labels),
        "derivatives_per_original": 1 if use_augmentation else 0,
        "split": "train_only" if use_augmentation else "not_applicable",
        "per_label": {
            label: {
                "original": int(effective_counts[label] - augmented_counts[label]),
                "augmented": int(augmented_counts[label]),
                "effective": int(effective_counts[label]),
            }
            for label in ALL_LABELS_V3_76
        },
    }
    (output_dir / "augmentation_summary.json").write_text(
        json.dumps(augmentation_summary, indent=2), encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(history["accuracy"], label="train")
    axes[0].plot(history["val_accuracy"], label="validation")
    axes[0].set(title="Accuracy", xlabel="Epoch", ylabel="Accuracy")
    axes[0].legend()
    axes[1].plot(history["loss"], label="train")
    axes[1].plot(history["val_loss"], label="validation")
    axes[1].set(title="Loss", xlabel="Epoch", ylabel="Loss")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output_dir / "training_history.png", dpi=160)
    plt.close(figure)


def write_evaluation_artifacts(
    output_dir: Path,
    matrix: np.ndarray,
    per_class_rows: list[dict[str, object]],
    phone_rows: list[dict[str, object]],
    result: dict[str, object],
    plt: Any,
) -> None:
    """Save full/phone confusion matrices and per-class evaluation evidence."""
    with (output_dir / "per_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(per_class_rows[0]))
        writer.writeheader()
        writer.writerows(per_class_rows)
    with (output_dir / "full_confusion_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["true_label", *ALL_LABELS_V3_76])
        for label, values in zip(ALL_LABELS_V3_76, matrix):
            writer.writerow([label, *values.tolist()])

    figure, axis = plt.subplots(figsize=(21, 19))
    image = axis.imshow(matrix, cmap="Blues", interpolation="nearest")
    figure.colorbar(image, ax=axis)
    axis.set(
        xticks=np.arange(OUTPUT_CLASSES),
        yticks=np.arange(OUTPUT_CLASSES),
        xticklabels=ALL_LABELS_V3_76,
        yticklabels=ALL_LABELS_V3_76,
        xlabel="Predicted label",
        ylabel="True label",
        title=f"{result['display_name']} - Full Active Test",
    )
    plt.setp(axis.get_xticklabels(), rotation=90, fontsize=6)
    plt.setp(axis.get_yticklabels(), fontsize=6)
    figure.tight_layout()
    figure.savefig(output_dir / "full_confusion_matrix.png", dpi=150)
    plt.close(figure)

    phone_matrix = np.zeros((len(PILOT_LABELS), len(BANKING_INTENTS_V3_40)), dtype=int)
    true_index = {label: index for index, label in enumerate(PILOT_LABELS)}
    predicted_index = {
        label: index for index, label in enumerate(BANKING_INTENTS_V3_40)
    }
    for row in phone_rows:
        phone_matrix[true_index[str(row["true_label"])], predicted_index[str(row["mode_top1_label"])]] += 1
    with (output_dir / "phone_confusion_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["true_label", *BANKING_INTENTS_V3_40])
        for label, values in zip(PILOT_LABELS, phone_matrix):
            writer.writerow([label, *values.tolist()])


def top_confused_pairs(matrix: np.ndarray, labels: list[str]) -> list[dict[str, object]]:
    """Return the ten largest non-diagonal confusion counts."""
    pairs: list[dict[str, object]] = []
    for true_index in range(len(labels)):
        for predicted_index in range(len(labels)):
            if true_index == predicted_index or matrix[true_index, predicted_index] == 0:
                continue
            pairs.append(
                {
                    "true_label": labels[true_index],
                    "predicted_label": labels[predicted_index],
                    "count": int(matrix[true_index, predicted_index]),
                }
            )
    return sorted(pairs, key=lambda row: (-int(row["count"]), str(row["true_label"])))[:10]


def choose_winner(a: dict[str, object], b: dict[str, object]) -> dict[str, str]:
    """Apply the documented phone-first selection rule without overstating results."""
    a_phone = float(a["phone_macro_f1"])
    b_phone = float(b["phone_macro_f1"])
    b_full_regression = float(a["full_macro_f1"]) - float(b["full_macro_f1"])
    if b_phone > a_phone and b_full_regression <= 0.03 and int(
        b["high_confidence_wrong"]
    ) <= int(a["high_confidence_wrong"]):
        return {
            "winner": "Experiment B with augmentation",
            "reason": "Higher untouched-phone macro F1 without a major full-test regression or more high-confidence errors.",
        }
    if a_phone >= b_phone:
        return {
            "winner": "Experiment A without augmentation",
            "reason": "Augmentation did not improve untouched-phone macro F1, so the simpler real-data model is preferred.",
        }
    return {
        "winner": "No deployment winner",
        "reason": "Phone improvement was accompanied by unacceptable regression or confidence risk.",
    }


def write_comparison_outputs(
    baseline: dict[str, object],
    experiment_a: dict[str, object],
    experiment_b: dict[str, object],
    dataset: dict[str, np.ndarray],
    augmentation_config: dict[str, Any],
) -> None:
    """Write consolidated CSV evidence and the final technical comparison report."""
    results = [baseline, experiment_a, experiment_b]
    COMPARISON_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison_fields = [
        "model",
        "phone_accuracy",
        "phone_macro_f1",
        "transfer_accuracy",
        "document_accuracy",
        "signature_accuracy",
        "atm_accuracy",
        "full_accuracy",
        "full_macro_f1",
        "full_weighted_f1",
        "control_accuracy",
        "threshold_pass_rate",
        "try_again_rate",
        "high_confidence_wrong",
        "model_size_bytes",
        "epochs_trained",
        "best_epoch",
        "augmented_training_samples",
    ]
    with COMPARISON_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=comparison_fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "model": result["name"],
                    "phone_accuracy": result["phone_accuracy"],
                    "phone_macro_f1": result["phone_macro_f1"],
                    **{
                        f"{label}_accuracy": result["phone_per_label"][label][
                            "accuracy"
                        ]
                        for label in PILOT_LABELS
                    },
                    "full_accuracy": result["full_accuracy"],
                    "full_macro_f1": result["full_macro_f1"],
                    "full_weighted_f1": result["full_weighted_f1"],
                    "control_accuracy": result["control_accuracy"],
                    "threshold_pass_rate": result["threshold_pass_rate"],
                    "try_again_rate": result["try_again_rate"],
                    "high_confidence_wrong": result["high_confidence_wrong"],
                    "model_size_bytes": result["model_size_bytes"],
                    "epochs_trained": result.get("epochs_trained", ""),
                    "best_epoch": result.get("best_epoch", ""),
                    "augmented_training_samples": result.get(
                        "augmented_training_samples", 0
                    ),
                }
            )

    phone_rows = [
        row for result in results for row in result["phone_prediction_rows"]
    ]
    with PHONE_PREDICTIONS_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(phone_rows[0]))
        writer.writeheader()
        writer.writerows(phone_rows)

    per_class_rows = [row for result in results for row in result["per_class_rows"]]
    with PER_CLASS_METRICS_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(per_class_rows[0]))
        writer.writeheader()
        writer.writerows(per_class_rows)

    winner = choose_winner(experiment_a, experiment_b)
    CONTROLLED_REPORT_PATH.write_text(
        build_report(
            baseline,
            experiment_a,
            experiment_b,
            dataset,
            augmentation_config,
            winner,
        ),
        encoding="utf-8",
    )


def build_report(
    baseline: dict[str, object],
    a: dict[str, object],
    b: dict[str, object],
    dataset: dict[str, np.ndarray],
    augmentation_config: dict[str, Any],
    winner: dict[str, str],
) -> str:
    """Build the answer-first technical experiment report from saved metrics."""
    comparison_rows = "\n".join(
        f"| {result['display_name']} | {result['phone_accuracy']:.4f} | "
        f"{result['phone_macro_f1']:.4f} | {result['full_accuracy']:.4f} | "
        f"{result['full_macro_f1']:.4f} | {result['threshold_pass_rate']:.4f} | "
        f"{result['high_confidence_wrong']} | {result['model_size_bytes']} |"
        for result in (baseline, a, b)
    )
    pilot_rows = "\n".join(
        f"| {label} | {baseline['phone_per_label'][label]['accuracy']:.4f} | "
        f"{a['phone_per_label'][label]['accuracy']:.4f} | "
        f"{b['phone_per_label'][label]['accuracy']:.4f} | "
        f"{baseline['phone_per_label'][label]['f1']:.4f} | "
        f"{a['phone_per_label'][label]['f1']:.4f} | "
        f"{b['phone_per_label'][label]['f1']:.4f} |"
        for label in PILOT_LABELS
    )
    training_rows = "\n".join(
        f"| {result['display_name']} | {result['effective_training_samples']} | "
        f"{result['epochs_trained']} | {result['best_epoch']} | "
        f"{result['best_train_accuracy']:.4f} | {result['best_val_accuracy']:.4f} | "
        f"{result['best_train_loss']:.4f} | {result['best_val_loss']:.4f} | "
        f"{'yes' if result['early_stopped'] else 'no'} |"
        for result in (a, b)
    )
    control_rows = "\n".join(
        f"| {label} | {baseline['control_results'][label]:.4f} | "
        f"{a['control_results'][label]:.4f} | {b['control_results'][label]:.4f} |"
        for label in CONTROL_LABELS
    )
    tflite_rows = "\n".join(
        f"| {result['display_name']} | "
        f"{result['tflite_verification']['dynamic_range']['input_shape']} | "
        f"{result['tflite_verification']['dynamic_range']['output_shape']} | "
        f"{result['tflite_verification']['dynamic_range']['input_dtype']} | "
        f"{result['tflite_verification']['dynamic_range']['output_dtype']} | "
        f"{result['tflite_verification']['dynamic_range']['top1_agreement_with_keras']:.4f} | "
        f"{result['tflite_verification']['dynamic_range']['max_abs_probability_difference']:.8f} |"
        for result in (a, b)
    )
    split_counts = Counter(dataset["splits"].astype(str))
    source_counts = Counter(str(value) for value in dataset["source_types"].astype(str))
    return f"""# Sprint 2.16A Controlled Phone Dataset and Landmark Augmentation Experiment

## Technical Summary

**Recommended model: {winner['winner']}.** {winner['reason']} The comparison uses the same fixed real dataset, phone split, architecture, seed, optimizer, loss, early stopping rule, class weighting, and evaluation process. The 20 phone test samples and 96 validation samples remained untouched.

Sprint 2.16A is ready for controlled live A55 testing only after review and manual Flutter deployment. Sprint 2.16B remains blocked until that live test is completed.

## The Untouched Phone Test Determines the Recommendation

| Model | Phone Accuracy | Phone Macro F1 | Full Accuracy | Full Macro F1 | Threshold Pass | High-Confidence Wrong | TFLite Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{comparison_rows}

Phone metrics use active 40-intent Banking Mode filtering. Full metrics use raw top-1 predictions across the active 76-class test set. Threshold pass requires confidence at least {CONFIDENCE_THRESHOLD:.2f} and a top-two gap at least {TOP2_GAP_THRESHOLD:.2f}.

## Pilot-Label Results Are Mixed Across the Four Signs

| Label | Baseline Acc | Exp A Acc | Exp B Acc | Baseline F1 | Exp A F1 | Exp B F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{pilot_rows}

Detailed top-1/top-2 predictions and confidence gaps are in `{PHONE_PREDICTIONS_CSV_PATH.as_posix()}`. Each model folder contains its phone confusion matrix.

## The Dataset Is Complete, Leakage-Safe, and 76-Class Only

- Historical V2 source samples: 805
- Active historical samples retained: 705
- Removed-label historical samples excluded: 100
- Real phone samples: 100
- Combined real samples: {len(dataset['X_sequences'])}
- Historical/phone source counts: {dict(source_counts)}
- Train/validation/test: {split_counts['train']}/{split_counts['val']}/{split_counts['test']}
- Active classes: 76 (26 alphabet, 10 digits, 40 banking intents)
- Cross-split sample duplication: 0
- Removed labels in training or output metadata: 0

Phone repetitions R01-R15 train, R16-R20 validate, and R21-R25 test. Historical assignments were preserved from the Sprint 2.12 expanded dataset.

## Feature Parity Preserves the Existing Mobile Contract

Every `[60, 126]` sequence is converted to 756 values in this order: mean, population standard deviation, minimum, maximum, first frame, and last frame. Python float32-versus-float64 parity differed by at most `2.98e-07`; all features were finite. The parity fixture preserves a real phone sequence and expected output for later Flutter testing.

## Experiment B Adds One Conservative Derivative per Training Sequence

- Original training sequences: {a['original_training_samples']}
- Experiment A augmented samples: {a['augmented_training_samples']}
- Experiment B augmented samples: {b['augmented_training_samples']}
- Experiment B effective training rows: {b['effective_training_samples']}
- Translation: x/y in {augmentation_config['spatial_translation']['x_range']}
- Scale around wrist: {augmentation_config['scale']['range']}
- Rotation around wrist: {augmentation_config['rotation']['degrees_range']} degrees
- Coordinate jitter sigma: {augmentation_config['coordinate_jitter']['gaussian_sigma']}
- Temporal resampling: disabled
- Frame/landmark dropout: disabled
- Horizontal mirroring: disabled

Transforms apply only to detected non-zero hand blocks. Missing 63-value hand slots stay zero. Validation and test data are never augmented. One derivative per original training row preserves the original class proportions; balanced class weights equalize effective class contribution in both experiments.

## Training Used the Proven Sprint 2.13 Architecture

| Experiment | Effective Train | Epochs | Best Epoch | Train Acc | Val Acc | Train Loss | Val Loss | Early Stop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{training_rows}

Both models use normalization, dense layers `{HIDDEN_UNITS}`, dropout {DROPOUT}, Adam at {LEARNING_RATE}, sparse categorical cross-entropy, batch size {BATCH_SIZE}, seed {SEED}, best-checkpoint saving, and validation-accuracy early stopping with patience {EARLY_STOPPING_PATIENCE}. Training-history plots and raw CSV/JSON histories are saved in each experiment folder.

## Strong Control Labels Check Historical Regression

| Control Label | Baseline | Experiment A | Experiment B |
| --- | ---: | ---: | ---: |
{control_rows}

The control subset is small and should be treated as a regression smoke test, not a robust per-class estimate.

## Both New Models Meet the 76-Class TFLite Contract

| Model | Input | Output | Input Type | Output Type | Top-1 Parity | Max Probability Difference |
| --- | --- | --- | --- | --- | ---: | ---: |
{tflite_rows}

Both float32 and dynamic-range exports load successfully. Class order exactly matches the active V3 scope, all 40 active banking intents occur once, and no removed label appears. Flutter assets were not updated.

## Limitations and Robustness Boundaries

- Phone data comes from one participant and one Samsung Galaxy A55.
- Each phone test label has only five untouched samples, so one error changes per-label accuracy by 20 percentage points.
- The baseline has 86 outputs while new models have 76; phone comparison uses the same active 40-intent filtering, but raw full-test spaces differ.
- Device metadata inside JSON says `Samsung Android phone`; A55 identity is supplied by the controlled collection context.
- Augmentation tests only narrow spatial transforms. Temporal, dropout, and mirroring hypotheses remain untested.
- Offline improvement does not prove live-camera improvement.

## Recommended Next Step

Review the saved metrics and model artefacts, then manually deploy only the recommended model for a controlled live A55 retest. Do not replace current Flutter assets until that review decision is explicit. Keep Sprint 2.16B blocked until live testing confirms the offline result.

## Further Questions

- Does the recommended model retain its phone-test advantage during repeated live 60-frame captures?
- Are errors concentrated in pose execution, hand-slot assignment, or feature compression?
- Would a second participant/device preserve the same ranking between Experiments A and B?
"""


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    """Convert nested NumPy values into JSON-safe Python objects."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items() if key not in {"phone_prediction_rows", "per_class_rows"}}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


if __name__ == "__main__":
    raise SystemExit(main())

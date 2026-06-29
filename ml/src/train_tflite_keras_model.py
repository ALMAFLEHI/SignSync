"""Train a Sprint 2.13 TensorFlow/Keras MLP for TensorFlow Lite export."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from tflite_model_config import (
    EXPECTED_TEST,
    EXPECTED_TRAIN,
    EXPECTED_VAL,
    FEATURE_DATASET_PATH,
    INPUT_FEATURE_WIDTH,
    KERAS_METRICS_SUMMARY_PATH,
    KERAS_MODEL_PATH,
    KERAS_TRAINING_HISTORY_CSV_PATH,
    KERAS_TRAINING_REPORT_MD_PATH,
    MODEL_LABEL_GROUPS_PATH,
    MODEL_LABEL_NAMES_PATH,
    OUTPUT_CLASSES,
    SAVED_MODEL_DIR,
    SOURCE_LABEL_GROUPS_PATH,
    SPRINT_OUTPUT_DIR,
    expected_split_counts,
)


CANDIDATE_ARCHITECTURES: dict[str, list[int]] = {
    "small": [256, 128],
    "medium": [512, 256, 128],
    "large": [1024, 512, 256],
}


def parse_args() -> argparse.Namespace:
    """Parse Sprint 2.13 Keras training options."""
    parser = argparse.ArgumentParser(
        description="Train TensorFlow/Keras MLP candidates for Sprint 2.13 TFLite export."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def import_tensorflow() -> Any:
    """Import TensorFlow only when a train/dry-run command is executed."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001 - report environment issue clearly.
        raise ImportError(
            "TensorFlow is not available. Use a compatible Python environment and "
            "install requirements_sprint_2_13.txt."
        ) from exc
    return tf


def load_feature_dataset() -> dict[str, np.ndarray]:
    """Load the prepared 756-feature dataset."""
    if not FEATURE_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Feature dataset is missing: {FEATURE_DATASET_PATH.as_posix()}"
        )
    with np.load(FEATURE_DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X_features", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            raise ValueError(f"Feature dataset missing arrays: {sorted(missing)}")
        return {key: dataset[key] for key in dataset.files}


def validate_dataset(dataset: dict[str, np.ndarray]) -> Counter[str]:
    """Validate feature shape, output classes, and deterministic split counts."""
    X = dataset["X_features"]
    y = dataset["y"]
    label_names = dataset["label_names"]
    splits = dataset["splits"].astype(str)
    if X.shape != (sum(expected_split_counts().values()), INPUT_FEATURE_WIDTH):
        raise ValueError(f"Unexpected feature shape: {X.shape}")
    if y.shape != (X.shape[0],):
        raise ValueError(f"Unexpected y shape: {y.shape}")
    if len(label_names) != OUTPUT_CLASSES:
        raise ValueError(f"Expected {OUTPUT_CLASSES} labels, found {len(label_names)}")
    if not np.isfinite(X).all():
        raise ValueError("Feature dataset contains NaN or infinite values.")
    counts = Counter(splits)
    if dict(counts) != expected_split_counts():
        raise ValueError(f"Unexpected split counts: {dict(counts)}")
    return counts


def set_random_seed(tf: Any, seed: int) -> None:
    """Set Python, NumPy, and TensorFlow seeds for repeatable training."""
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def macro_f1_score_np(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate macro F1 without requiring TensorFlow-specific metric state."""
    from sklearn.metrics import f1_score

    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def build_model(tf: Any, hidden_units: list[int], train_features: np.ndarray, dropout: float = 0.25) -> Any:
    """Build one normalized MLP candidate."""
    normalization = tf.keras.layers.Normalization(name="feature_normalization")
    normalization.adapt(train_features.astype(np.float32))
    inputs = tf.keras.Input(shape=(INPUT_FEATURE_WIDTH,), dtype=tf.float32, name="features")
    x = normalization(inputs)
    for index, units in enumerate(hidden_units):
        x = tf.keras.layers.Dense(units, activation="relu", name=f"dense_{index + 1}")(x)
        x = tf.keras.layers.Dropout(dropout, name=f"dropout_{index + 1}")(x)
    outputs = tf.keras.layers.Dense(OUTPUT_CLASSES, activation="softmax", name="probabilities")(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


def train_candidate(
    tf: Any,
    name: str,
    hidden_units: list[int],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int,
    batch_size: int,
) -> dict[str, object]:
    """Train one candidate and evaluate on validation data only."""
    model = build_model(tf, hidden_units, X_train)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=20,
            mode="max",
            restore_best_weights=True,
        )
    ]
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=2,
    )
    probabilities = model.predict(X_val, verbose=0)
    predictions = np.argmax(probabilities, axis=1)
    val_accuracy = float(np.mean(predictions == y_val))
    val_macro_f1 = macro_f1_score_np(y_val, predictions)
    return {
        "candidate": name,
        "hidden_units": hidden_units,
        "model": model,
        "history": history.history,
        "validation_accuracy": val_accuracy,
        "validation_macro_f1": val_macro_f1,
        "epochs_trained": len(history.history.get("loss", [])),
    }


def select_best(results: list[dict[str, object]]) -> dict[str, object]:
    """Select best candidate by validation macro F1, then validation accuracy."""
    return max(
        results,
        key=lambda result: (
            float(result["validation_macro_f1"]),
            float(result["validation_accuracy"]),
        ),
    )


def write_history_csv(best: dict[str, object]) -> None:
    """Write the selected model training history."""
    history = dict(best["history"])
    KERAS_TRAINING_HISTORY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    keys = list(history)
    max_rows = max((len(values) for values in history.values()), default=0)
    with KERAS_TRAINING_HISTORY_CSV_PATH.open("w", newline="", encoding="utf-8") as history_file:
        writer = csv.DictWriter(history_file, fieldnames=["epoch", *keys])
        writer.writeheader()
        for index in range(max_rows):
            row = {"epoch": index + 1}
            for key in keys:
                values = history[key]
                row[key] = values[index] if index < len(values) else ""
            writer.writerow(row)


def export_saved_model(tf: Any, model: Any) -> str:
    """Export an optional SavedModel folder using the available Keras API."""
    if SAVED_MODEL_DIR.exists():
        return "skipped_existing_saved_model"
    SAVED_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(model, "export"):
        model.export(SAVED_MODEL_DIR.as_posix())
    else:
        tf.saved_model.save(model, SAVED_MODEL_DIR.as_posix())
    return SAVED_MODEL_DIR.as_posix()


def write_reports(dataset: dict[str, np.ndarray], results: list[dict[str, object]], best: dict[str, object], saved_model_status: str) -> None:
    """Write model metadata, report Markdown, and metrics JSON."""
    SPRINT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    label_names = dataset["label_names"].astype(str).tolist()
    MODEL_LABEL_NAMES_PATH.write_text(json.dumps(label_names, indent=2), encoding="utf-8")
    if not SOURCE_LABEL_GROUPS_PATH.exists():
        raise FileNotFoundError(f"Missing label groups: {SOURCE_LABEL_GROUPS_PATH.as_posix()}")
    MODEL_LABEL_GROUPS_PATH.write_text(SOURCE_LABEL_GROUPS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    write_history_csv(best)

    candidate_text = "\n".join(
        f"- {result['candidate']}: units {result['hidden_units']}, "
        f"validation accuracy {float(result['validation_accuracy']):.4f}, "
        f"validation macro F1 {float(result['validation_macro_f1']):.4f}, "
        f"epochs {result['epochs_trained']}"
        for result in results
    )
    content = f"""# Sprint 2.13 Keras Training Report

## Dataset
- Feature dataset: {FEATURE_DATASET_PATH.as_posix()}
- Feature shape: {tuple(dataset['X_features'].shape)}
- Classes: {len(label_names)}
- Train/validation/test: {EXPECTED_TRAIN}/{EXPECTED_VAL}/{EXPECTED_TEST}

## Candidate Models
{candidate_text}

## Selected Model
- Candidate: {best['candidate']}
- Hidden units: {best['hidden_units']}
- Validation accuracy: {float(best['validation_accuracy']):.4f}
- Validation macro F1: {float(best['validation_macro_f1']):.4f}
- Keras model: {KERAS_MODEL_PATH.as_posix()}
- SavedModel export: {saved_model_status}

## Scope Note
The test split is not used for model selection. Test evaluation is handled by `evaluate_tflite_keras_model.py`.
"""
    KERAS_TRAINING_REPORT_MD_PATH.write_text(content, encoding="utf-8")
    KERAS_METRICS_SUMMARY_PATH.write_text(
        json.dumps(
            {
                "feature_dataset": FEATURE_DATASET_PATH.as_posix(),
                "selected_candidate": best["candidate"],
                "hidden_units": best["hidden_units"],
                "validation_accuracy": float(best["validation_accuracy"]),
                "validation_macro_f1": float(best["validation_macro_f1"]),
                "keras_model": KERAS_MODEL_PATH.as_posix(),
                "saved_model": saved_model_status,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def print_dry_run(dataset: dict[str, np.ndarray], counts: Counter[str]) -> None:
    """Print training readiness without fitting models."""
    print("Sprint 2.13 Keras Training Dry Run")
    print("----------------------------------")
    print(f"feature dataset: {FEATURE_DATASET_PATH.as_posix()}")
    print(f"feature shape: {tuple(dataset['X_features'].shape)}")
    print(f"train/val/test: {counts['train']}/{counts['val']}/{counts['test']}")
    print("candidates:")
    for name, units in CANDIDATE_ARCHITECTURES.items():
        print(f"- {name}: {units}")
    print("Dry run completed. No model training or files were created.")


def main() -> int:
    """Dry-run or train Keras MLP candidates for TFLite export."""
    args = parse_args()
    try:
        tf = import_tensorflow()
        dataset = load_feature_dataset()
        counts = validate_dataset(dataset)
        if args.dry_run:
            print_dry_run(dataset, counts)
            return 0
        if KERAS_MODEL_PATH.exists() and not args.overwrite:
            print(f"Keras model already exists: {KERAS_MODEL_PATH.as_posix()}. Use --overwrite.")
            return 1

        set_random_seed(tf, args.random_state)
        splits = dataset["splits"].astype(str)
        X = dataset["X_features"].astype(np.float32)
        y = dataset["y"].astype(np.int64)
        train_mask = splits == "train"
        val_mask = splits == "val"
        results = [
            train_candidate(
                tf,
                name,
                hidden_units,
                X[train_mask],
                y[train_mask],
                X[val_mask],
                y[val_mask],
                args.epochs,
                args.batch_size,
            )
            for name, hidden_units in CANDIDATE_ARCHITECTURES.items()
        ]
        best = select_best(results)
        SPRINT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        best["model"].save(KERAS_MODEL_PATH)
        saved_model_status = export_saved_model(tf, best["model"])
        write_reports(dataset, results, best, saved_model_status)
        print("Sprint 2.13 Keras Training Summary")
        print("----------------------------------")
        print(f"selected candidate: {best['candidate']}")
        print(f"validation accuracy: {float(best['validation_accuracy']):.4f}")
        print(f"validation macro F1: {float(best['validation_macro_f1']):.4f}")
        print(f"Keras model: {KERAS_MODEL_PATH.as_posix()}")
        print("next command: python ml/src/evaluate_tflite_keras_model.py")
        return 0
    except (ImportError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

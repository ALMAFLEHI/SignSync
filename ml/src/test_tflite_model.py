"""Evaluate exported Sprint 2.13 TensorFlow Lite models on the held-out test split."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from tflite_model_config import (
    FEATURE_DATASET_PATH,
    KERAS_MODEL_PATH,
    TFLITE_DYNAMIC_RANGE_PATH,
    TFLITE_FLOAT32_PATH,
    TFLITE_TEST_REPORT_CSV_PATH,
    TFLITE_TEST_REPORT_MD_PATH,
)


def import_tensorflow():
    """Import TensorFlow only when TFLite testing runs."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001
        raise ImportError("TensorFlow is not available in this environment.") from exc
    return tf


def load_feature_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load test features, labels, and split assignments."""
    if not FEATURE_DATASET_PATH.exists():
        raise FileNotFoundError(f"Feature dataset is missing: {FEATURE_DATASET_PATH.as_posix()}")
    with np.load(FEATURE_DATASET_PATH, allow_pickle=False) as dataset:
        return (
            dataset["X_features"].astype(np.float32),
            dataset["y"].astype(np.int64),
            dataset["splits"].astype(str),
        )


def evaluate_keras(tf, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, object]:
    """Evaluate the Keras model if present."""
    if not KERAS_MODEL_PATH.exists():
        return {"model": "keras", "status": "missing", "accuracy": "", "macro_f1": "", "weighted_f1": ""}
    from sklearn.metrics import accuracy_score, f1_score

    model = tf.keras.models.load_model(KERAS_MODEL_PATH)
    predictions = np.argmax(model.predict(X_test, verbose=0), axis=1)
    return {
        "model": "keras",
        "status": "evaluated",
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
    }


def evaluate_tflite(tf, model_path: Path, X_test: np.ndarray, y_test: np.ndarray, name: str) -> dict[str, object]:
    """Evaluate one TFLite model on the test split."""
    if not model_path.exists():
        return {"model": name, "status": "missing", "accuracy": "", "macro_f1": "", "weighted_f1": ""}
    from sklearn.metrics import accuracy_score, f1_score

    interpreter = tf.lite.Interpreter(model_path=model_path.as_posix())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    predictions: list[int] = []
    for row in X_test:
        interpreter.set_tensor(input_detail["index"], row.reshape(1, -1).astype(np.float32))
        interpreter.invoke()
        output = interpreter.get_tensor(output_detail["index"])
        predictions.append(int(np.argmax(output, axis=1)[0]))
    predictions_array = np.asarray(predictions, dtype=np.int64)
    return {
        "model": name,
        "status": "evaluated",
        "accuracy": float(accuracy_score(y_test, predictions_array)),
        "macro_f1": float(f1_score(y_test, predictions_array, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, predictions_array, average="weighted", zero_division=0)),
    }


def write_reports(rows: list[dict[str, object]]) -> None:
    """Save TFLite test CSV and Markdown reports."""
    TFLITE_TEST_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "status", "accuracy", "macro_f1", "weighted_f1"]
    with TFLITE_TEST_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    keras_row = next((row for row in rows if row["model"] == "keras"), None)
    tflite_rows = [row for row in rows if row["model"].startswith("tflite") and row["status"] == "evaluated"]
    pass_close = False
    if keras_row and keras_row["status"] == "evaluated" and tflite_rows:
        pass_close = all(abs(float(row["accuracy"]) - float(keras_row["accuracy"])) <= 0.02 for row in tflite_rows)
    row_text = "\n".join(
        f"- {row['model']}: {row['status']}, accuracy {row['accuracy']}, macro F1 {row['macro_f1']}, weighted F1 {row['weighted_f1']}"
        for row in rows
    )
    content = f"""# Sprint 2.13 TFLite Test Report

## Result
{'PASS' if pass_close else 'REVIEW'}

## Model Comparison
{row_text}

## Pass Rule
TFLite accuracy should be within 0.02 of the Keras model accuracy.
"""
    TFLITE_TEST_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Run held-out test evaluation for Keras and exported TFLite models."""
    try:
        tf = import_tensorflow()
        X, y, splits = load_feature_dataset()
        test_mask = splits == "test"
        X_test = X[test_mask]
        y_test = y[test_mask]
        rows = [
            evaluate_keras(tf, X_test, y_test),
            evaluate_tflite(tf, TFLITE_FLOAT32_PATH, X_test, y_test, "tflite_float32"),
            evaluate_tflite(tf, TFLITE_DYNAMIC_RANGE_PATH, X_test, y_test, "tflite_dynamic_range"),
        ]
        write_reports(rows)
        print("Sprint 2.13 TFLite Test Summary")
        print("--------------------------------")
        for row in rows:
            print(f"{row['model']}: {row['status']}, accuracy={row['accuracy']}, macro_f1={row['macro_f1']}")
        print(f"CSV report: {TFLITE_TEST_REPORT_CSV_PATH.as_posix()}")
        print(f"Markdown report: {TFLITE_TEST_REPORT_MD_PATH.as_posix()}")
        return 0
    except (ImportError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

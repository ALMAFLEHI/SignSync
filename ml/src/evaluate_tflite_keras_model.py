"""Evaluate the Sprint 2.13 Keras model on the held-out expanded V2 test split."""

from __future__ import annotations

import csv
import json

import numpy as np

from tflite_model_config import (
    FEATURE_DATASET_PATH,
    KERAS_CONFUSION_MATRIX_CSV_PATH,
    KERAS_CONFUSION_MATRIX_PNG_PATH,
    KERAS_EVALUATION_REPORT_CSV_PATH,
    KERAS_EVALUATION_REPORT_MD_PATH,
    KERAS_MODEL_PATH,
    MODEL_LABEL_NAMES_PATH,
    SPRINT_2_12_BASELINE_ACCURACY,
    SPRINT_2_12_BASELINE_MACRO_F1,
)


def import_tensorflow():
    """Import TensorFlow only when evaluation runs."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001
        raise ImportError("TensorFlow is not available in this environment.") from exc
    return tf


def load_feature_dataset() -> dict[str, np.ndarray]:
    """Load the prepared feature dataset."""
    if not FEATURE_DATASET_PATH.exists():
        raise FileNotFoundError(f"Feature dataset is missing: {FEATURE_DATASET_PATH.as_posix()}")
    with np.load(FEATURE_DATASET_PATH, allow_pickle=False) as dataset:
        return {key: dataset[key] for key in dataset.files}


def main() -> int:
    """Evaluate Keras model on test split only and save reports."""
    try:
        tf = import_tensorflow()
        import matplotlib.pyplot as plt
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            precision_recall_fscore_support,
        )

        if not KERAS_MODEL_PATH.exists():
            raise FileNotFoundError(f"Keras model is missing: {KERAS_MODEL_PATH.as_posix()}")
        dataset = load_feature_dataset()
        label_names = json.loads(MODEL_LABEL_NAMES_PATH.read_text(encoding="utf-8"))
        splits = dataset["splits"].astype(str)
        test_mask = splits == "test"
        X_test = dataset["X_features"][test_mask].astype(np.float32)
        y_test = dataset["y"][test_mask].astype(np.int64)
        model = tf.keras.models.load_model(KERAS_MODEL_PATH)
        probabilities = model.predict(X_test, verbose=0)
        predictions = np.argmax(probabilities, axis=1)

        accuracy = float(accuracy_score(y_test, predictions))
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            y_test, predictions, average="macro", zero_division=0
        )
        weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
            y_test, predictions, average="weighted", zero_division=0
        )
        report = classification_report(
            y_test,
            predictions,
            labels=list(range(len(label_names))),
            target_names=label_names,
            zero_division=0,
            output_dict=True,
        )
        matrix = confusion_matrix(y_test, predictions, labels=list(range(len(label_names))))

        KERAS_EVALUATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with KERAS_EVALUATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
            writer = csv.writer(report_file)
            writer.writerow(["label", "precision", "recall", "f1_score", "support"])
            for label in label_names:
                values = report[label]
                writer.writerow(
                    [
                        label,
                        f"{values['precision']:.6f}",
                        f"{values['recall']:.6f}",
                        f"{values['f1-score']:.6f}",
                        int(values["support"]),
                    ]
                )
            writer.writerow(["accuracy", "", "", f"{accuracy:.6f}", len(y_test)])
            writer.writerow(["macro avg", f"{macro_precision:.6f}", f"{macro_recall:.6f}", f"{macro_f1:.6f}", len(y_test)])
            writer.writerow(["weighted avg", f"{weighted_precision:.6f}", f"{weighted_recall:.6f}", f"{weighted_f1:.6f}", len(y_test)])

        with KERAS_CONFUSION_MATRIX_CSV_PATH.open("w", newline="", encoding="utf-8") as matrix_file:
            writer = csv.writer(matrix_file)
            writer.writerow(["true_label", *label_names])
            for label, row in zip(label_names, matrix):
                writer.writerow([label, *row.tolist()])

        figure, axis = plt.subplots(figsize=(22, 20))
        image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
        figure.colorbar(image, ax=axis)
        axis.set(
            xticks=np.arange(len(label_names)),
            yticks=np.arange(len(label_names)),
            xticklabels=label_names,
            yticklabels=label_names,
            xlabel="Predicted label",
            ylabel="True label",
            title="Sprint 2.13 Keras Confusion Matrix",
        )
        plt.setp(axis.get_xticklabels(), rotation=90, ha="center", fontsize=6)
        plt.setp(axis.get_yticklabels(), rotation=0, fontsize=6)
        figure.tight_layout()
        figure.savefig(KERAS_CONFUSION_MATRIX_PNG_PATH, dpi=160)
        plt.close(figure)

        accuracy_delta = accuracy - SPRINT_2_12_BASELINE_ACCURACY
        macro_f1_delta = macro_f1 - SPRINT_2_12_BASELINE_MACRO_F1
        content = f"""# Sprint 2.13 Keras Evaluation Report

## Held-Out Test Results
- Test samples: {len(y_test)}
- Accuracy: {accuracy:.4f}
- Macro precision: {macro_precision:.4f}
- Macro recall: {macro_recall:.4f}
- Macro F1-score: {macro_f1:.4f}
- Weighted F1-score: {weighted_f1:.4f}

## Comparison With Sprint 2.12 scikit-learn Baseline
- Sprint 2.12 ExtraTrees accuracy: approximately {SPRINT_2_12_BASELINE_ACCURACY:.4f}
- Sprint 2.12 ExtraTrees macro F1: approximately {SPRINT_2_12_BASELINE_MACRO_F1:.4f}
- Keras accuracy change: {accuracy_delta:+.4f}
- Keras macro F1 change: {macro_f1_delta:+.4f}

## Important Caution
This remains a controlled single-participant result. Mobile testing and usability evaluation are still pending.

## Output Files
- Evaluation CSV: {KERAS_EVALUATION_REPORT_CSV_PATH.as_posix()}
- Confusion matrix CSV: {KERAS_CONFUSION_MATRIX_CSV_PATH.as_posix()}
- Confusion matrix PNG: {KERAS_CONFUSION_MATRIX_PNG_PATH.as_posix()}
"""
        KERAS_EVALUATION_REPORT_MD_PATH.write_text(content, encoding="utf-8")
        print("Sprint 2.13 Keras Evaluation Summary")
        print("------------------------------------")
        print(f"test samples: {len(y_test)}")
        print(f"accuracy: {accuracy:.4f}")
        print(f"macro F1: {macro_f1:.4f}")
        print(f"weighted F1: {weighted_f1:.4f}")
        print(f"accuracy vs Sprint 2.12: {accuracy_delta:+.4f}")
        return 0
    except (ImportError, FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

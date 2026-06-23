"""Evaluate the saved Sprint 2.10 full baseline model on the held-out test split."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from full_dataset_config import (
    CONFUSION_MATRIX_CSV_PATH,
    CONFUSION_MATRIX_PNG_PATH,
    DATASET_PATH,
    EVALUATION_REPORT_CSV_PATH,
    EVALUATION_REPORT_MD_PATH,
    MODEL_LABEL_NAMES_PATH,
    MODEL_PATH,
)
from full_model_feature_utils import create_statistical_features


def load_json(path: Path):
    """Load JSON metadata with a clear missing-file message."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Evaluate only held-out test examples and write reproducible evidence reports."""
    try:
        import joblib
        import matplotlib.pyplot as plt
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            precision_recall_fscore_support,
        )

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Saved model is missing: {MODEL_PATH.as_posix()}")
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"Full dataset is missing: {DATASET_PATH.as_posix()}")
        label_names = [str(label) for label in load_json(MODEL_LABEL_NAMES_PATH)]
        with np.load(DATASET_PATH, allow_pickle=False) as dataset:
            X = dataset["X"]
            y = dataset["y"]
            splits = dataset["splits"].astype(str)
        test_mask = splits == "test"
        features = create_statistical_features(X[test_mask])
        y_test = y[test_mask]
        model = joblib.load(MODEL_PATH)
        predictions = model.predict(features)

        accuracy = float(accuracy_score(y_test, predictions))
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(y_test, predictions, average="macro", zero_division=0)
        weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(y_test, predictions, average="weighted", zero_division=0)
        report = classification_report(y_test, predictions, labels=list(range(len(label_names))), target_names=label_names, zero_division=0, output_dict=True)
        matrix = confusion_matrix(y_test, predictions, labels=list(range(len(label_names))))

        EVALUATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EVALUATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
            writer = csv.writer(report_file)
            writer.writerow(["label", "precision", "recall", "f1_score", "support"])
            for label in label_names:
                values = report[label]
                writer.writerow([label, f"{values['precision']:.6f}", f"{values['recall']:.6f}", f"{values['f1-score']:.6f}", int(values["support"])])
            writer.writerow(["accuracy", "", "", f"{accuracy:.6f}", len(y_test)])
            writer.writerow(["macro avg", f"{macro_precision:.6f}", f"{macro_recall:.6f}", f"{macro_f1:.6f}", len(y_test)])
            writer.writerow(["weighted avg", f"{weighted_precision:.6f}", f"{weighted_recall:.6f}", f"{weighted_f1:.6f}", len(y_test)])

        with CONFUSION_MATRIX_CSV_PATH.open("w", newline="", encoding="utf-8") as matrix_file:
            writer = csv.writer(matrix_file)
            writer.writerow(["true_label", *label_names])
            for label, row in zip(label_names, matrix):
                writer.writerow([label, *row.tolist()])

        figure, axis = plt.subplots(figsize=(16, 14))
        image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
        figure.colorbar(image, ax=axis)
        axis.set(
            xticks=np.arange(len(label_names)),
            yticks=np.arange(len(label_names)),
            xticklabels=label_names,
            yticklabels=label_names,
            xlabel="Predicted label",
            ylabel="True label",
            title="Sprint 2.10 Full Baseline Confusion Matrix",
        )
        plt.setp(axis.get_xticklabels(), rotation=90, ha="center")
        plt.setp(axis.get_yticklabels(), rotation=0)
        figure.tight_layout()
        figure.savefig(CONFUSION_MATRIX_PNG_PATH, dpi=160)
        plt.close(figure)

        content = f"""# Sprint 2.10 Full Baseline Evaluation Report

## Held-Out Test Results
- Test samples: {len(y_test)}
- Accuracy: {accuracy:.4f}
- Macro precision: {macro_precision:.4f}
- Macro recall: {macro_recall:.4f}
- Macro F1-score: {macro_f1:.4f}
- Weighted precision: {weighted_precision:.4f}
- Weighted recall: {weighted_recall:.4f}
- Weighted F1-score: {weighted_f1:.4f}

## Important Caution
This is a single-participant controlled dataset baseline. It validates the pipeline and the current scoped dataset, but it is not a real-world production accuracy claim. More participants and environmental variation are required for final evaluation.

## Output Files
- Per-label evaluation CSV: {EVALUATION_REPORT_CSV_PATH.as_posix()}
- Confusion matrix CSV: {CONFUSION_MATRIX_CSV_PATH.as_posix()}
- Confusion matrix PNG: {CONFUSION_MATRIX_PNG_PATH.as_posix()}
"""
        EVALUATION_REPORT_MD_PATH.write_text(content, encoding="utf-8")
        print("Sprint 2.10 Full Baseline Evaluation Summary")
        print("--------------------------------------------")
        print(f"test samples: {len(y_test)}")
        print(f"accuracy: {accuracy:.4f}")
        print(f"macro F1: {macro_f1:.4f}")
        print(f"weighted F1: {weighted_f1:.4f}")
        print(f"evaluation report: {EVALUATION_REPORT_MD_PATH.as_posix()}")
        return 0
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Evaluate the saved Sprint 2.6 baseline model on the test split."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from model_config import (
    DATASET_PATH,
    EVALUATION_REPORT_CSV_PATH,
    EVALUATION_REPORT_MD_PATH,
    CONFUSION_MATRIX_PATH,
    LABEL_NAMES_OUTPUT_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_OUTPUT_PATH,
    SCALER_OUTPUT_PATH,
)
from train_baseline_model import create_features


def load_json(path: Path):
    """Load a JSON file with a clear error if it is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON file: {path.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Evaluate the saved model and write reports."""
    import joblib
    import matplotlib.pyplot as plt
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    if not MODEL_OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing model file: {MODEL_OUTPUT_PATH.as_posix()}. Run training first."
        )

    metrics_summary = load_json(METRICS_SUMMARY_PATH)
    label_names = load_json(LABEL_NAMES_OUTPUT_PATH)
    feature_mode = metrics_summary.get("feature_mode", "stats")
    scaler_required = bool(metrics_summary.get("scaler_required", False))

    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        X = dataset["X"]
        y = dataset["y"]
        splits = dataset["splits"].astype(str)

    test_mask = splits == "test"
    X_test = create_features(X[test_mask], feature_mode)
    y_test = y[test_mask]

    model = joblib.load(MODEL_OUTPUT_PATH)
    if scaler_required:
        if not SCALER_OUTPUT_PATH.exists():
            raise FileNotFoundError(f"Missing scaler file: {SCALER_OUTPUT_PATH.as_posix()}")
        scaler = joblib.load(SCALER_OUTPUT_PATH)
        X_test = scaler.transform(X_test)

    predictions = model.predict(X_test)
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
        target_names=label_names,
        zero_division=0,
        output_dict=True,
    )
    matrix = confusion_matrix(y_test, predictions, labels=list(range(len(label_names))))

    EVALUATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVALUATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.writer(report_file)
        writer.writerow(["metric", "precision", "recall", "f1_score", "support"])
        for label_name in label_names:
            row = report[label_name]
            writer.writerow(
                [
                    label_name,
                    f"{row['precision']:.6f}",
                    f"{row['recall']:.6f}",
                    f"{row['f1-score']:.6f}",
                    int(row["support"]),
                ]
            )
        writer.writerow(["accuracy", "", "", f"{accuracy:.6f}", len(y_test)])
        writer.writerow(["macro avg", f"{macro_precision:.6f}", f"{macro_recall:.6f}", f"{macro_f1:.6f}", len(y_test)])
        writer.writerow(["weighted avg", f"{weighted_precision:.6f}", f"{weighted_recall:.6f}", f"{weighted_f1:.6f}", len(y_test)])

    fig, ax = plt.subplots(figsize=(9, 8))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set(
        xticks=np.arange(len(label_names)),
        yticks=np.arange(len(label_names)),
        xticklabels=label_names,
        yticklabels=label_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Sprint 2.6 Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            ax.text(column_index, row_index, matrix[row_index, column_index], ha="center", va="center")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PATH, dpi=150)
    plt.close(fig)

    markdown = f"""# Sprint 2.6 Evaluation Report

## Summary
- Test samples: {len(y_test)}
- Accuracy: {accuracy:.4f}
- Macro precision: {macro_precision:.4f}
- Macro recall: {macro_recall:.4f}
- Macro F1-score: {macro_f1:.4f}
- Weighted precision: {weighted_precision:.4f}
- Weighted recall: {weighted_recall:.4f}
- Weighted F1-score: {weighted_f1:.4f}

## Important Note
This evaluation is based on a small trial dataset with one test sample per class. It validates the pipeline but does not represent final production accuracy.

## Output Files
- Evaluation CSV: {EVALUATION_REPORT_CSV_PATH.as_posix()}
- Evaluation Markdown: {EVALUATION_REPORT_MD_PATH.as_posix()}
- Confusion matrix: {CONFUSION_MATRIX_PATH.as_posix()}
"""
    EVALUATION_REPORT_MD_PATH.write_text(markdown, encoding="utf-8")

    print("Sprint 2.6 Baseline Evaluation Summary")
    print("--------------------------------------")
    print(f"test samples: {len(y_test)}")
    print(f"accuracy: {accuracy:.4f}")
    print(f"macro F1: {macro_f1:.4f}")
    print(f"weighted F1: {weighted_f1:.4f}")
    print(f"evaluation CSV: {EVALUATION_REPORT_CSV_PATH.as_posix()}")
    print(f"evaluation Markdown: {EVALUATION_REPORT_MD_PATH.as_posix()}")
    print(f"confusion matrix path: {CONFUSION_MATRIX_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

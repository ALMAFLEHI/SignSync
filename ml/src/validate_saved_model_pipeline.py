"""Validate that the saved Sprint 2.6 model still predicts the trial dataset."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from pipeline_validation_config import (
    DATASET_PATH,
    DEFAULT_FEATURE_MODE,
    LABEL_NAMES_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_PATH,
    PIPELINE_VALIDATION_REPORT_CSV,
    PIPELINE_VALIDATION_REPORT_MD,
    PREDICTION_CHECK_REPORT_CSV,
    PREDICTION_CHECK_REPORT_MD,
    SCALER_PATH,
    SPLIT_CSV_PATH,
    STATS_FEATURE_SIZE,
    report_path,
)


def parse_args() -> argparse.Namespace:
    """Parse options for safe saved-model validation."""
    parser = argparse.ArgumentParser(
        description="Validate the saved Sprint 2.6 model without retraining it."
    )
    parser.add_argument("--feature-mode", choices=("stats",), default=DEFAULT_FEATURE_MODE)
    parser.add_argument("--max-prediction-rows", type=int, default=55)
    return parser.parse_args()


def create_stats_features(X: np.ndarray) -> np.ndarray:
    """Use Sprint 2.6's mean/std/min/max/first/last stats feature method."""
    means = X.mean(axis=1)
    stds = X.std(axis=1)
    mins = X.min(axis=1)
    maxs = X.max(axis=1)
    first_frames = X[:, 0, :]
    last_frames = X[:, -1, :]
    return np.concatenate([means, stds, mins, maxs, first_frames, last_frames], axis=1)


def load_split_rows() -> dict[str, dict[str, str]]:
    """Read the Sprint 2.5 split CSV into a lookup keyed by sample ID."""
    with Path(SPLIT_CSV_PATH).open("r", newline="", encoding="utf-8") as split_file:
        rows = list(csv.DictReader(split_file))
    required_fields = {"sample_id", "label", "label_index", "split"}
    if not rows or not required_fields.issubset(rows[0]):
        raise ValueError("Sprint 2.5 split CSV has missing required columns.")
    lookup = {row["sample_id"]: row for row in rows}
    if len(lookup) != len(rows):
        raise ValueError("Sprint 2.5 split CSV contains duplicate sample IDs.")
    return lookup


def load_scaler_if_required():
    """Load a scaler only when Sprint 2.6 recorded that the saved model needs one."""
    if not Path(METRICS_SUMMARY_PATH).exists():
        return None, False

    summary = json.loads(Path(METRICS_SUMMARY_PATH).read_text(encoding="utf-8"))
    scaler_required = bool(summary.get("scaler_required", False))
    if not scaler_required:
        return None, False
    if not Path(SCALER_PATH).exists():
        raise FileNotFoundError(f"Saved model requires a scaler, but it is missing: {SCALER_PATH}")

    import joblib

    return joblib.load(SCALER_PATH), True


def calculate_metrics(y_true: np.ndarray, predictions: np.ndarray) -> dict[str, float | int]:
    """Calculate the requested aggregate metrics without changing model state."""
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support

    macro = precision_recall_fscore_support(
        y_true, predictions, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        y_true, predictions, average="weighted", zero_division=0
    )
    return {
        "sample_count": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "macro_precision": float(macro[0]),
        "macro_recall": float(macro[1]),
        "macro_f1": float(macro[2]),
        "weighted_precision": float(weighted[0]),
        "weighted_recall": float(weighted[1]),
        "weighted_f1": float(weighted[2]),
    }


def write_pipeline_reports(metrics_by_split: dict[str, dict[str, float | int]]) -> None:
    """Write CSV and Markdown metric reports for the loaded model pipeline."""
    csv_path = report_path(PIPELINE_VALIDATION_REPORT_CSV)
    md_path = report_path(PIPELINE_VALIDATION_REPORT_MD)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "split",
        "sample_count",
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_precision",
        "weighted_recall",
        "weighted_f1",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        for split_name, values in metrics_by_split.items():
            writer.writerow({"split": split_name, **values})

    rows = "\n".join(
        "| {split} | {sample_count} | {accuracy:.4f} | {macro_precision:.4f} | "
        "{macro_recall:.4f} | {macro_f1:.4f} | {weighted_precision:.4f} | "
        "{weighted_recall:.4f} | {weighted_f1:.4f} |".format(
            split=split_name, **values
        )
        for split_name, values in metrics_by_split.items()
    )
    content = f"""# Sprint 2.7 Saved Model Pipeline Validation Report

## Result
The saved Sprint 2.6 model loaded successfully and produced predictions after loading. The pipeline from the Sprint 2.5 dataset, through the Sprint 2.6 saved model, to prediction is working.

| Split | Samples | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted Precision | Weighted Recall | Weighted F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{rows}

## Important Limitation
The high score validates the stored trial pipeline, but it must not be claimed as production accuracy. The current dataset is small, contains only trial labels, and has no cross-participant evaluation.

## Output Files
- Metrics CSV: {csv_path.as_posix()}
- Prediction check CSV: {report_path(PREDICTION_CHECK_REPORT_CSV).as_posix()}
"""
    md_path.write_text(content, encoding="utf-8")


def write_prediction_reports(prediction_rows: list[dict[str, str]], total_predictions: int) -> None:
    """Write per-sample prediction evidence in CSV and Markdown formats."""
    csv_path = report_path(PREDICTION_CHECK_REPORT_CSV)
    md_path = report_path(PREDICTION_CHECK_REPORT_MD)
    fieldnames = [
        "sample_id",
        "split",
        "true_label",
        "predicted_label",
        "result",
        "confidence",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prediction_rows)

    correct_count = sum(row["result"] == "correct" for row in prediction_rows)
    content = f"""# Sprint 2.7 Prediction Check Report

## Summary
- Predictions evaluated: {total_predictions}
- Rows written: {len(prediction_rows)}
- Correct rows written: {correct_count}
- Confidence values are included because the saved RandomForestClassifier supports `predict_proba`.

## Result
The saved model can make predictions after loading. This check is a pipeline validation result, not a claim of final production performance.

## Output File
- Prediction CSV: {csv_path.as_posix()}
"""
    md_path.write_text(content, encoding="utf-8")


def main() -> int:
    """Load the saved model, predict every split, and write validation evidence."""
    args = parse_args()
    if args.max_prediction_rows < 1:
        raise ValueError("--max-prediction-rows must be at least 1.")

    import joblib

    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        X = dataset["X"]
        y = dataset["y"]
        sample_ids = dataset["sample_ids"].astype(str)
        dataset_splits = dataset["splits"].astype(str)

    label_names = [str(label) for label in json.loads(Path(LABEL_NAMES_PATH).read_text(encoding="utf-8"))]
    split_lookup = load_split_rows()
    if set(sample_ids) != set(split_lookup):
        raise ValueError("Dataset sample IDs do not match the Sprint 2.5 split CSV.")

    csv_splits = np.asarray([split_lookup[sample_id]["split"] for sample_id in sample_ids])
    if not np.array_equal(dataset_splits, csv_splits):
        raise ValueError("Dataset split assignments do not match the Sprint 2.5 split CSV.")

    features = create_stats_features(X)
    if features.shape[1] != STATS_FEATURE_SIZE:
        raise ValueError(f"Stats feature width must be {STATS_FEATURE_SIZE}, found {features.shape[1]}.")

    model = joblib.load(MODEL_PATH)
    model_feature_count = getattr(model, "n_features_in_", None)
    if model_feature_count != features.shape[1]:
        raise ValueError(
            f"Saved model expects {model_feature_count} features, but stats features contain {features.shape[1]}."
        )

    scaler, scaler_required = load_scaler_if_required()
    model_features = scaler.transform(features) if scaler is not None else features
    predictions = model.predict(model_features)
    probabilities = model.predict_proba(model_features) if hasattr(model, "predict_proba") else None

    masks = {
        "train": csv_splits == "train",
        "validation": csv_splits == "val",
        "test": csv_splits == "test",
        "all": np.ones(len(y), dtype=bool),
    }
    metrics_by_split = {
        split_name: calculate_metrics(y[mask], predictions[mask])
        for split_name, mask in masks.items()
    }

    prediction_rows: list[dict[str, str]] = []
    for index, (sample_id, split, true_index, predicted_index) in enumerate(
        zip(sample_ids, csv_splits, y, predictions)
    ):
        if index >= args.max_prediction_rows:
            break
        confidence = "not available"
        if probabilities is not None:
            confidence = f"{float(np.max(probabilities[index])):.6f}"
        prediction_rows.append(
            {
                "sample_id": sample_id,
                "split": split,
                "true_label": label_names[int(true_index)],
                "predicted_label": label_names[int(predicted_index)],
                "result": "correct" if true_index == predicted_index else "incorrect",
                "confidence": confidence,
            }
        )

    write_pipeline_reports(metrics_by_split)
    write_prediction_reports(prediction_rows, total_predictions=len(y))

    print("Sprint 2.7 Saved Model Pipeline Validation")
    print("------------------------------------------")
    print(f"saved model: {type(model).__name__}")
    print(f"feature mode: {args.feature_mode}")
    print(f"stats feature shape: {tuple(features.shape)}")
    print(f"scaler required: {'yes' if scaler_required else 'no'}")
    for split_name, values in metrics_by_split.items():
        print(
            f"{split_name}: samples={values['sample_count']}, "
            f"accuracy={values['accuracy']:.4f}, macro F1={values['macro_f1']:.4f}"
        )
    print(f"pipeline validation report: {report_path(PIPELINE_VALIDATION_REPORT_MD).as_posix()}")
    print(f"prediction check report: {report_path(PREDICTION_CHECK_REPORT_MD).as_posix()}")
    print("PASS: Saved model pipeline validation completed without retraining.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Predict one sample with the saved Sprint 2.6 baseline model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from model_config import (
    DATASET_PATH,
    DEFAULT_FEATURE_MODE,
    FEATURE_MODES,
    LABEL_NAMES_OUTPUT_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_OUTPUT_PATH,
    SCALER_OUTPUT_PATH,
)
from train_baseline_model import create_features


def parse_args() -> argparse.Namespace:
    """Parse one-sample prediction options."""
    parser = argparse.ArgumentParser(description="Predict one SignSync trial sample.")
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--feature-mode", choices=FEATURE_MODES, default=DEFAULT_FEATURE_MODE)
    return parser.parse_args()


def load_json(path: Path):
    """Load a JSON file with a clear error if it is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON file: {path.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Run a single-sample prediction and print the result."""
    import joblib

    args = parse_args()
    if not MODEL_OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing model file: {MODEL_OUTPUT_PATH.as_posix()}. Run training first."
        )

    label_names = load_json(LABEL_NAMES_OUTPUT_PATH)
    metrics_summary = (
        load_json(METRICS_SUMMARY_PATH) if METRICS_SUMMARY_PATH.exists() else {}
    )
    scaler_required = bool(metrics_summary.get("scaler_required", False))

    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        sample_ids = dataset["sample_ids"].astype(str)
        labels = dataset["labels"].astype(str)
        y = dataset["y"]
        X = dataset["X"]

    matches = np.where(sample_ids == args.sample_id)[0]
    if len(matches) == 0:
        raise ValueError(f"Sample ID not found in dataset: {args.sample_id}")

    sample_index = int(matches[0])
    features = create_features(X[sample_index : sample_index + 1], args.feature_mode)
    model = joblib.load(MODEL_OUTPUT_PATH)
    if scaler_required:
        if not SCALER_OUTPUT_PATH.exists():
            raise FileNotFoundError(f"Missing scaler file: {SCALER_OUTPUT_PATH.as_posix()}")
        scaler = joblib.load(SCALER_OUTPUT_PATH)
        features = scaler.transform(features)

    predicted_index = int(model.predict(features)[0])
    true_index = int(y[sample_index])
    true_label = str(labels[sample_index])
    predicted_label = label_names[predicted_index]
    correct = predicted_index == true_index

    print("Sprint 2.6 Single Sample Prediction")
    print("-----------------------------------")
    print(f"sample ID: {args.sample_id}")
    print(f"true label: {true_label}")
    print(f"predicted label: {predicted_label}")
    print(f"result: {'correct' if correct else 'incorrect'}")

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        top_indices = np.argsort(probabilities)[::-1][:5]
        print("top probability scores:")
        for index in top_indices:
            print(f"- {label_names[int(index)]}: {float(probabilities[int(index)]):.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Predict one prepared expanded V2 sample using the Sprint 2.12 saved baseline."""

from __future__ import annotations

import argparse
import json

import numpy as np

from expanded_dataset_config import (
    DATASET_PATH,
    EXPANDED_DATASET_PARTICIPANT,
    MODEL_LABEL_NAMES_PATH,
    MODEL_PATH,
)
from expanded_model_feature_utils import create_statistical_features


def parse_args() -> argparse.Namespace:
    """Parse either a direct sample ID or a participant/label/repetition selection."""
    parser = argparse.ArgumentParser(description="Predict one Sprint 2.12 expanded dataset sample.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--sample-id")
    selection.add_argument("--label")
    parser.add_argument("--repetition", type=int)
    parser.add_argument("--participant", default=EXPANDED_DATASET_PARTICIPANT)
    return parser.parse_args()


def selected_sample_id(args: argparse.Namespace) -> str:
    """Return a direct sample ID or construct one after validating paired arguments."""
    if args.sample_id:
        return args.sample_id
    if args.repetition is None or args.repetition < 1:
        raise ValueError("--repetition must be supplied with --label.")
    return f"{args.participant}_{args.label}_R{args.repetition:02d}"


def main() -> int:
    """Load the saved pipeline, predict one sample, and print confidence evidence."""
    try:
        import joblib

        args = parse_args()
        sample_id = selected_sample_id(args)
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Saved model is missing: {MODEL_PATH.as_posix()}")
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"Expanded dataset is missing: {DATASET_PATH.as_posix()}")
        label_names = [
            str(label)
            for label in json.loads(MODEL_LABEL_NAMES_PATH.read_text(encoding="utf-8"))
        ]
        with np.load(DATASET_PATH, allow_pickle=False) as dataset:
            sample_ids = dataset["sample_ids"].astype(str)
            labels = dataset["labels"].astype(str)
            y = dataset["y"]
            X = dataset["X"]
        matches = np.where(sample_ids == sample_id)[0]
        if len(matches) != 1:
            raise ValueError(f"Expected one matching sample ID, found {len(matches)}: {sample_id}")
        index = int(matches[0])
        features = create_statistical_features(X[index:index + 1])
        model = joblib.load(MODEL_PATH)
        predicted_index = int(model.predict(features)[0])
        true_index = int(y[index])
        print("Sprint 2.12 Expanded Sample Prediction")
        print("--------------------------------------")
        print(f"sample ID: {sample_id}")
        print(f"true label: {labels[index]}")
        print(f"predicted label: {label_names[predicted_index]}")
        print(f"result: {'correct' if predicted_index == true_index else 'incorrect'}")
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)[0]
            classes = np.asarray(model.classes_, dtype=int)
            predicted_probability = float(probabilities[np.where(classes == predicted_index)[0][0]])
            print(f"confidence: {predicted_probability:.4f}")
            print("top 5 predictions:")
            for probability_index in np.argsort(probabilities)[::-1][:5]:
                label_index = int(classes[int(probability_index)])
                print(f"- {label_names[label_index]}: {float(probabilities[int(probability_index)]):.4f}")
        return 0
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Prepare 756-feature Sprint 2.13 training data for Keras and TFLite."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter

import numpy as np

from expanded_model_feature_utils import create_statistical_features
from tflite_model_config import (
    EXPECTED_TOTAL_SAMPLES,
    EXPECTED_TRAIN,
    EXPECTED_VAL,
    EXPECTED_TEST,
    FEATURE_DATASET_PATH,
    FEATURE_ORDER,
    FEATURE_PREPARATION_REPORT_CSV_PATH,
    FEATURE_PREPARATION_REPORT_MD_PATH,
    INPUT_FEATURE_WIDTH,
    OUTPUT_CLASSES,
    SOURCE_DATASET_PATH,
    SOURCE_LABEL_GROUPS_PATH,
    TARGET_FRAMES,
    LANDMARK_DIMENSION,
)


def parse_args() -> argparse.Namespace:
    """Parse feature preparation controls."""
    parser = argparse.ArgumentParser(
        description="Prepare 756-statistical-feature dataset for Sprint 2.13 TFLite training."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_source_dataset() -> dict[str, np.ndarray]:
    """Load the Sprint 2.12 expanded sequence dataset."""
    if not SOURCE_DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing expanded dataset: {SOURCE_DATASET_PATH.as_posix()}")
    with np.load(SOURCE_DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            raise ValueError(f"Expanded dataset missing arrays: {sorted(missing)}")
        return {key: dataset[key] for key in dataset.files}


def load_label_groups(label_names: np.ndarray) -> dict[str, object]:
    """Load label groups and build mode indices against the model output order."""
    if not SOURCE_LABEL_GROUPS_PATH.exists():
        raise FileNotFoundError(f"Missing label groups: {SOURCE_LABEL_GROUPS_PATH.as_posix()}")
    groups = json.loads(SOURCE_LABEL_GROUPS_PATH.read_text(encoding="utf-8"))
    label_to_index = {label: index for index, label in enumerate(label_names.astype(str))}
    normal_labels = [str(label) for label in groups.get("normal_mode", [])]
    number_labels = [str(label) for label in groups.get("number_mode", [])]
    return {
        "all_labels": [str(label) for label in groups.get("all_labels", [])],
        "normal_mode_labels": normal_labels,
        "number_mode_labels": number_labels,
        "normal_mode_indices": np.asarray([label_to_index[label] for label in normal_labels], dtype=np.int64),
        "number_mode_indices": np.asarray([label_to_index[label] for label in number_labels], dtype=np.int64),
    }


def validate_source(dataset: dict[str, np.ndarray]) -> Counter[str]:
    """Validate the expanded dataset before feature extraction."""
    if dataset["X"].shape != (EXPECTED_TOTAL_SAMPLES, TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(f"Unexpected source X shape: {dataset['X'].shape}")
    if dataset["y"].shape != (EXPECTED_TOTAL_SAMPLES,):
        raise ValueError(f"Unexpected y shape: {dataset['y'].shape}")
    if len(dataset["label_names"]) != OUTPUT_CLASSES:
        raise ValueError(f"Expected {OUTPUT_CLASSES} labels, found {len(dataset['label_names'])}")
    splits = dataset["splits"].astype(str)
    counts = Counter(splits)
    if dict(counts) != {"train": EXPECTED_TRAIN, "val": EXPECTED_VAL, "test": EXPECTED_TEST}:
        raise ValueError(f"Unexpected split counts: {dict(counts)}")
    return counts


def build_feature_arrays(dataset: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Create feature arrays and copy required metadata arrays."""
    X_features = create_statistical_features(dataset["X"])
    if X_features.shape != (EXPECTED_TOTAL_SAMPLES, INPUT_FEATURE_WIDTH):
        raise ValueError(f"Unexpected feature shape: {X_features.shape}")
    if not np.isfinite(X_features).all():
        raise ValueError("Feature dataset contains NaN or infinite values.")
    groups = load_label_groups(dataset["label_names"])
    return {
        "X_features": X_features.astype(np.float32, copy=False),
        "y": dataset["y"].astype(np.int64, copy=False),
        "sample_ids": dataset["sample_ids"],
        "labels": dataset["labels"],
        "splits": dataset["splits"],
        "label_names": dataset["label_names"],
        "normal_mode_labels": np.asarray(groups["normal_mode_labels"]),
        "number_mode_labels": np.asarray(groups["number_mode_labels"]),
        "normal_mode_indices": groups["normal_mode_indices"],
        "number_mode_indices": groups["number_mode_indices"],
        "feature_order": np.asarray(FEATURE_ORDER),
        "source_sequence_shape": np.asarray([TARGET_FRAMES, LANDMARK_DIMENSION], dtype=np.int64),
        "input_feature_width": np.asarray(INPUT_FEATURE_WIDTH, dtype=np.int64),
        "output_classes": np.asarray(OUTPUT_CLASSES, dtype=np.int64),
    }


def write_reports(dataset: dict[str, np.ndarray], features: dict[str, np.ndarray], counts: Counter[str]) -> None:
    """Write CSV and Markdown evidence reports for feature preparation."""
    FEATURE_PREPARATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"item": "source_X_shape", "value": str(tuple(dataset["X"].shape))},
        {"item": "X_features_shape", "value": str(tuple(features["X_features"].shape))},
        {"item": "y_shape", "value": str(tuple(features["y"].shape))},
        {"item": "labels", "value": str(len(features["label_names"]))},
        {"item": "train", "value": str(counts["train"])},
        {"item": "val", "value": str(counts["val"])},
        {"item": "test", "value": str(counts["test"])},
        {"item": "normal_mode_labels", "value": str(len(features["normal_mode_labels"]))},
        {"item": "number_mode_labels", "value": str(len(features["number_mode_labels"]))},
    ]
    with FEATURE_PREPARATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["item", "value"])
        writer.writeheader()
        writer.writerows(rows)
    content = f"""# Sprint 2.13 TFLite Feature Preparation Report

## Summary
- Source dataset: {SOURCE_DATASET_PATH.as_posix()}
- Source X shape: {tuple(dataset['X'].shape)}
- Feature dataset: {FEATURE_DATASET_PATH.as_posix()}
- X_features shape: {tuple(features['X_features'].shape)}
- y shape: {tuple(features['y'].shape)}
- Feature order: {', '.join(FEATURE_ORDER)}
- Train/validation/test: {counts['train']}/{counts['val']}/{counts['test']}
- Normal Mode labels: {len(features['normal_mode_labels'])}
- Number Mode labels: {len(features['number_mode_labels'])}

## Flutter Note
The Flutter app must collect 60 frames of 126-value landmarks, compute the same 756 statistical features, and pass a float32 tensor shaped `[1, 756]` to the TFLite model.
"""
    FEATURE_PREPARATION_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_dry_run(dataset: dict[str, np.ndarray], counts: Counter[str]) -> None:
    """Print expected output without writing the feature dataset."""
    print("Sprint 2.13 TFLite Feature Preparation Dry Run")
    print("----------------------------------------------")
    print(f"source dataset: {SOURCE_DATASET_PATH.as_posix()}")
    print(f"source X shape: {tuple(dataset['X'].shape)}")
    print(f"expected feature shape: ({EXPECTED_TOTAL_SAMPLES}, {INPUT_FEATURE_WIDTH})")
    print(f"expected train/val/test: {counts['train']}/{counts['val']}/{counts['test']}")
    print(f"output feature dataset: {FEATURE_DATASET_PATH.as_posix()}")
    print("Dry run completed. No feature dataset was written.")


def main() -> int:
    """Dry-run or create the Sprint 2.13 feature dataset."""
    args = parse_args()
    try:
        dataset = load_source_dataset()
        counts = validate_source(dataset)
        if args.dry_run:
            print_dry_run(dataset, counts)
            return 0
        if FEATURE_DATASET_PATH.exists() and not args.overwrite:
            print(f"Feature dataset already exists: {FEATURE_DATASET_PATH.as_posix()}. Use --overwrite.")
            return 1
        features = build_feature_arrays(dataset)
        FEATURE_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(FEATURE_DATASET_PATH, **features)
        write_reports(dataset, features, counts)
        print("Sprint 2.13 TFLite Feature Preparation Summary")
        print("----------------------------------------------")
        print(f"X_features shape: {tuple(features['X_features'].shape)}")
        print(f"y shape: {tuple(features['y'].shape)}")
        print(f"feature dataset: {FEATURE_DATASET_PATH.as_posix()}")
        print("Feature preparation completed successfully.")
        return 0
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

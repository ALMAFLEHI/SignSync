"""Create the Sprint 2.12 ML-ready expanded V2 dataset from landmark outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from expanded_dataset_config import (
    ALL_LABELS_V2,
    DATASET_PATH,
    DATASET_ROOT,
    EXPECTED_SAMPLES,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    EXPANDED_DATASET_PARTICIPANT,
    LABEL_GROUPS,
    LABEL_GROUPS_PATH,
    LABEL_MAPPING_PATH,
    LANDMARK_DIMENSION,
    MASK_DIMENSION,
    METADATA_PATH,
    PREPARATION_REPORT_CSV_PATH,
    PREPARATION_REPORT_MD_PATH,
    SPLIT_CSV_PATH,
    TARGET_FRAMES,
    iter_expected_samples,
)


METADATA_HEADERS = [
    "sample_id", "participant_id", "label", "repetition", "video_path",
    "landmark_path", "status", "notes",
]


def parse_args() -> argparse.Namespace:
    """Parse expanded-dataset preparation options."""
    parser = argparse.ArgumentParser(
        description="Prepare the Sprint 2.12 expanded V2 2-hand training dataset."
    )
    parser.add_argument("--participant", default=EXPANDED_DATASET_PARTICIPANT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def read_metadata_index() -> dict[str, list[dict[str, str]]]:
    """Read metadata rows by ID solely to validate expected sample records."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {METADATA_PATH.as_posix()}")
    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError("metadata.csv headers are incorrect.")
        rows: dict[str, list[dict[str, str]]] = {}
        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if sample_id:
                rows.setdefault(sample_id, []).append(row)
    return rows


def standardize_pair(landmarks: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, str]:
    """Resample or zero-pad landmarks and masks to exactly 60 synchronized frames."""
    frame_count = landmarks.shape[0]
    if frame_count == TARGET_FRAMES:
        return landmarks.astype(np.float32, copy=False), mask.astype(np.uint8, copy=False), "unchanged"
    if frame_count > TARGET_FRAMES:
        indices = np.linspace(0, frame_count - 1, TARGET_FRAMES).round().astype(int)
        return (
            landmarks[indices].astype(np.float32, copy=False),
            mask[indices].astype(np.uint8, copy=False),
            "resampled",
        )

    landmark_padding = np.zeros((TARGET_FRAMES - frame_count, LANDMARK_DIMENSION), dtype=np.float32)
    mask_padding = np.zeros((TARGET_FRAMES - frame_count, MASK_DIMENSION), dtype=np.uint8)
    return (
        np.vstack([landmarks.astype(np.float32, copy=False), landmark_padding]),
        np.vstack([mask.astype(np.uint8, copy=False), mask_padding]),
        "padded",
    )


def load_valid_pair(sample: dict[str, object]) -> tuple[np.ndarray, np.ndarray]:
    """Load and validate an original landmark/mask pair without changing it."""
    landmark_path = Path(sample["landmark_path"])
    mask_path = Path(sample["mask_path"])
    if not landmark_path.exists() or not mask_path.exists():
        raise FileNotFoundError(f"Missing landmark or mask output for {sample['sample_id']}.")
    landmarks = np.load(landmark_path, allow_pickle=False)
    mask = np.load(mask_path, allow_pickle=False)
    if landmarks.ndim != 2 or landmarks.shape[1] != LANDMARK_DIMENSION or landmarks.shape[0] < 1:
        raise ValueError(f"Invalid landmark shape for {sample['sample_id']}: {tuple(landmarks.shape)}")
    if mask.ndim != 2 or mask.shape[1] != MASK_DIMENSION or mask.shape[0] != landmarks.shape[0]:
        raise ValueError(f"Invalid mask shape for {sample['sample_id']}: {tuple(mask.shape)}")
    return landmarks, mask


def validate_metadata_row(sample: dict[str, object], rows: list[dict[str, str]]) -> None:
    """Require one matching metadata row but do not modify metadata."""
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one metadata row for {sample['sample_id']}, found {len(rows)}.")
    row = rows[0]
    if (
        row.get("participant_id") != sample["participant_id"]
        or row.get("label") != sample["label"]
        or row.get("repetition") != str(sample["repetition"])
    ):
        raise ValueError(f"Metadata fields do not match expected sample {sample['sample_id']}.")


def prepare_arrays(participant_id: str) -> tuple[dict[str, np.ndarray], list[dict[str, str]]]:
    """Load, validate, standardize, and stack all 805 expanded landmark pairs."""
    metadata_index = read_metadata_index()
    mapping = {label: index for index, label in enumerate(ALL_LABELS_V2)}
    x_values: list[np.ndarray] = []
    mask_values: list[np.ndarray] = []
    y_values: list[int] = []
    sample_ids: list[str] = []
    labels: list[str] = []
    splits: list[str] = []
    report_rows: list[dict[str, str]] = []

    for sample in iter_expected_samples(participant_id):
        sample_id = str(sample["sample_id"])
        validate_metadata_row(sample, metadata_index.get(sample_id, []))
        landmarks, mask = load_valid_pair(sample)
        standardized_landmarks, standardized_mask, action = standardize_pair(landmarks, mask)
        x_values.append(standardized_landmarks)
        mask_values.append(standardized_mask)
        y_values.append(mapping[str(sample["label"])])
        sample_ids.append(sample_id)
        labels.append(str(sample["label"]))
        splits.append(str(sample["split"]))
        report_rows.append(
            {
                "sample_id": sample_id,
                "label": str(sample["label"]),
                "repetition": str(sample["repetition"]),
                "split": str(sample["split"]),
                "source_frames": str(landmarks.shape[0]),
                "target_frames": str(TARGET_FRAMES),
                "standardization": action,
                "landmark_path": Path(sample["landmark_path"]).as_posix(),
                "mask_path": Path(sample["mask_path"]).as_posix(),
            }
        )

    arrays = {
        "X": np.stack(x_values).astype(np.float32),
        "mask": np.stack(mask_values).astype(np.uint8),
        "y": np.asarray(y_values, dtype=np.int64),
        "sample_ids": np.asarray(sample_ids),
        "labels": np.asarray(labels),
        "label_names": np.asarray(ALL_LABELS_V2),
        "splits": np.asarray(splits),
        "target_frames": np.asarray(TARGET_FRAMES),
        "landmark_dim": np.asarray(LANDMARK_DIMENSION),
        "mask_dim": np.asarray(MASK_DIMENSION),
    }
    return arrays, report_rows


def validate_arrays(arrays: dict[str, np.ndarray]) -> dict[str, int]:
    """Validate tensor shapes, splits, labels, uniqueness, and finite values."""
    if arrays["X"].shape != (EXPECTED_SAMPLES, TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(f"Unexpected X shape: {arrays['X'].shape}")
    if arrays["mask"].shape != (EXPECTED_SAMPLES, TARGET_FRAMES, MASK_DIMENSION):
        raise ValueError(f"Unexpected mask shape: {arrays['mask'].shape}")
    if arrays["y"].shape != (EXPECTED_SAMPLES,):
        raise ValueError(f"Unexpected y shape: {arrays['y'].shape}")
    if len(arrays["label_names"]) != len(ALL_LABELS_V2):
        raise ValueError("Dataset label names do not contain all expanded labels.")
    if len(set(arrays["sample_ids"].astype(str))) != EXPECTED_SAMPLES:
        raise ValueError("Dataset sample IDs are not unique.")
    if not np.isfinite(arrays["X"]).all():
        raise ValueError("Landmark dataset contains NaN or infinite values.")
    split_counts = Counter(arrays["splits"].astype(str))
    expected_counts = {
        "train": EXPECTED_TRAIN_SAMPLES,
        "val": EXPECTED_VAL_SAMPLES,
        "test": EXPECTED_TEST_SAMPLES,
    }
    if dict(split_counts) != expected_counts:
        raise ValueError(f"Unexpected split counts: {dict(split_counts)}")
    return expected_counts


def output_exists() -> bool:
    """Return True if any expanded dataset output already exists."""
    return any(
        path.exists()
        for path in [DATASET_PATH, LABEL_MAPPING_PATH, LABEL_GROUPS_PATH, SPLIT_CSV_PATH]
    )


def write_outputs(arrays: dict[str, np.ndarray], report_rows: list[dict[str, str]]) -> None:
    """Write new expanded-dataset outputs after complete validation succeeds."""
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DATASET_PATH, **arrays)
    LABEL_MAPPING_PATH.write_text(
        json.dumps({label: index for index, label in enumerate(ALL_LABELS_V2)}, indent=2),
        encoding="utf-8",
    )
    LABEL_GROUPS_PATH.write_text(json.dumps(LABEL_GROUPS, indent=2), encoding="utf-8")
    with SPLIT_CSV_PATH.open("w", newline="", encoding="utf-8") as split_file:
        writer = csv.DictWriter(split_file, fieldnames=["sample_id", "label", "label_index", "split"])
        writer.writeheader()
        for sample_id, label, label_index, split in zip(
            arrays["sample_ids"], arrays["labels"], arrays["y"], arrays["splits"]
        ):
            writer.writerow(
                {"sample_id": sample_id, "label": label, "label_index": int(label_index), "split": split}
            )

    PREPARATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PREPARATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=list(report_rows[0]))
        writer.writeheader()
        writer.writerows(report_rows)
    split_counts = Counter(arrays["splits"].astype(str))
    content = f"""# Sprint 2.12 Expanded Dataset Preparation Report

## Dataset Summary
- X shape: {tuple(arrays['X'].shape)}
- Mask shape: {tuple(arrays['mask'].shape)}
- y shape: {tuple(arrays['y'].shape)}
- Labels: {len(arrays['label_names'])}
- Train/validation/test: {split_counts['train']}/{split_counts['val']}/{split_counts['test']}
- payment included: yes
- receipt included: no
- document included: yes
- signature included: yes

## Output Files
- Dataset: {DATASET_PATH.as_posix()}
- Label mapping: {LABEL_MAPPING_PATH.as_posix()}
- Label groups: {LABEL_GROUPS_PATH.as_posix()}
- Split CSV: {SPLIT_CSV_PATH.as_posix()}
"""
    PREPARATION_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_dry_run(participant_id: str) -> int:
    """Print expected preparation output without writing a dataset file."""
    samples = iter_expected_samples(participant_id)
    metadata_index = read_metadata_index()
    missing_metadata = [
        sample for sample in samples
        if len(metadata_index.get(str(sample["sample_id"]), [])) != 1
    ]
    missing_arrays = [
        sample for sample in samples
        if not Path(sample["landmark_path"]).exists() or not Path(sample["mask_path"]).exists()
    ]
    print("Sprint 2.12 Expanded Dataset Preparation Dry Run")
    print("------------------------------------------------")
    print(f"participant: {participant_id}")
    print(f"expected X shape: ({EXPECTED_SAMPLES}, {TARGET_FRAMES}, {LANDMARK_DIMENSION})")
    print(f"expected mask shape: ({EXPECTED_SAMPLES}, {TARGET_FRAMES}, {MASK_DIMENSION})")
    print(f"expected y shape: ({EXPECTED_SAMPLES},)")
    print(f"expected train/val/test: {EXPECTED_TRAIN_SAMPLES}/{EXPECTED_VAL_SAMPLES}/{EXPECTED_TEST_SAMPLES}")
    print(f"missing or duplicate metadata rows: {len(missing_metadata)}")
    print(f"missing landmark or mask files: {len(missing_arrays)}")
    print(f"dataset output: {DATASET_PATH.as_posix()}")
    print("Dry run completed. No dataset files were written.")
    return 0 if not missing_metadata and not missing_arrays else 1


def main() -> int:
    """Dry-run or create the expanded ML dataset while preserving landmark files."""
    args = parse_args()
    try:
        if args.dry_run:
            return print_dry_run(args.participant)
        if output_exists() and not args.overwrite:
            print("Expanded dataset output already exists. Use --overwrite to replace it.")
            return 1
        arrays, report_rows = prepare_arrays(args.participant)
        validate_arrays(arrays)
        write_outputs(arrays, report_rows)
        print("Sprint 2.12 Expanded Dataset Preparation Summary")
        print("------------------------------------------------")
        print(f"X shape: {tuple(arrays['X'].shape)}")
        print(f"mask shape: {tuple(arrays['mask'].shape)}")
        print(f"y shape: {tuple(arrays['y'].shape)}")
        print(f"dataset path: {DATASET_PATH.as_posix()}")
        print("Expanded dataset preparation completed successfully.")
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

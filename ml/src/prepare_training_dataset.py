"""Prepare the Sprint 2.5 machine-learning-ready trial dataset."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from dataset_config import (
    DATASET_OUTPUT_DIR,
    DATASET_PATH,
    EXPECTED_SAMPLES,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    LANDMARK_DIM,
    LABEL_MAPPING_PATH,
    PARTICIPANT_ID,
    PREPARATION_REPORT_CSV_PATH,
    PREPARATION_REPORT_MD_PATH,
    SPLIT_CSV_PATH,
    TARGET_FRAMES,
    TEST_REPETITIONS,
    TRAIN_REPETITIONS,
    VAL_REPETITIONS,
)
from trial_config import TRIAL_LABELS


METADATA_PATH = Path("ml") / "metadata.csv"
METADATA_HEADERS = [
    "sample_id",
    "participant_id",
    "label",
    "repetition",
    "video_path",
    "landmark_path",
    "status",
    "notes",
]


def parse_args() -> argparse.Namespace:
    """Parse dataset preparation options."""
    parser = argparse.ArgumentParser(
        description="Prepare the Sprint 2.5 training dataset arrays."
    )
    parser.add_argument("--participant", default=PARTICIPANT_ID)
    parser.add_argument("--target-frames", type=int, default=TARGET_FRAMES)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def read_metadata_rows() -> list[dict[str, str]]:
    """Read metadata.csv and validate the expected headers."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError("ml/metadata.csv is missing.")

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
        return list(reader)


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the expected trial sample ID."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def split_for_repetition(repetition: int) -> str:
    """Assign fixed Sprint 2.5 splits by repetition number."""
    if repetition in TRAIN_REPETITIONS:
        return "train"
    if repetition in VAL_REPETITIONS:
        return "val"
    if repetition in TEST_REPETITIONS:
        return "test"
    raise ValueError(f"Unsupported repetition for split assignment: {repetition}")


def label_mapping() -> dict[str, int]:
    """Create the stable label mapping from trial_config.py order."""
    return {label: index for index, label in enumerate(TRIAL_LABELS)}


def indexed_metadata(rows: list[dict[str, str]], participant_id: str) -> dict[str, dict[str, str]]:
    """Index successful trial metadata rows by sample ID."""
    indexed_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("participant_id") != participant_id:
            continue
        if row.get("status") != "landmarks_extracted":
            continue
        if row.get("label") not in TRIAL_LABELS:
            continue
        sample_id = row.get("sample_id", "")
        if sample_id:
            indexed_rows[sample_id] = row
    return indexed_rows


def expected_rows(participant_id: str) -> list[dict[str, object]]:
    """Build the expected 55 sample descriptors in stable label order."""
    rows: list[dict[str, object]] = []
    for label in TRIAL_LABELS:
        for repetition in range(1, 6):
            sample_id = build_sample_id(participant_id, label, repetition)
            rows.append(
                {
                    "sample_id": sample_id,
                    "label": label,
                    "repetition": repetition,
                    "split": split_for_repetition(repetition),
                }
            )
    return rows


def standardize_frames(landmarks: np.ndarray, target_frames: int) -> tuple[np.ndarray, str]:
    """Resize a landmark sequence to exactly target_frames."""
    frame_count = landmarks.shape[0]
    if frame_count == target_frames:
        return landmarks.astype(np.float32, copy=False), "unchanged"

    if frame_count > target_frames:
        indices = np.linspace(0, frame_count - 1, target_frames).round().astype(int)
        return landmarks[indices].astype(np.float32, copy=False), "resampled"

    padding = np.zeros((target_frames - frame_count, landmarks.shape[1]), dtype=np.float32)
    standardized = np.vstack([landmarks.astype(np.float32, copy=False), padding])
    return standardized, "padded"


def build_dataset_arrays(
    participant_id: str,
    target_frames: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, str]]]:
    """Load landmarks, standardize sequences, and build X/y/split arrays."""
    rows = read_metadata_rows()
    metadata_by_sample = indexed_metadata(rows, participant_id)
    mapping = label_mapping()

    x_values: list[np.ndarray] = []
    y_values: list[int] = []
    sample_ids: list[str] = []
    labels: list[str] = []
    splits: list[str] = []
    report_rows: list[dict[str, str]] = []

    for expected in expected_rows(participant_id):
        sample_id = str(expected["sample_id"])
        label = str(expected["label"])
        repetition = int(expected["repetition"])
        split = str(expected["split"])
        metadata_row = metadata_by_sample.get(sample_id)
        if metadata_row is None:
            raise RuntimeError(f"Missing landmarks_extracted metadata row for {sample_id}.")

        landmark_path = Path(metadata_row.get("landmark_path", ""))
        if not landmark_path.exists():
            raise FileNotFoundError(f"Missing landmark file for {sample_id}: {landmark_path.as_posix()}")

        landmarks = np.load(landmark_path)
        if landmarks.ndim != 2 or landmarks.shape[1] != LANDMARK_DIM:
            raise ValueError(
                f"{sample_id} landmark shape must be number_of_frames x {LANDMARK_DIM}, "
                f"but found {tuple(landmarks.shape)}."
            )

        standardized, action = standardize_frames(landmarks, target_frames)
        x_values.append(standardized)
        y_values.append(mapping[label])
        sample_ids.append(sample_id)
        labels.append(label)
        splits.append(split)
        report_rows.append(
            {
                "sample_id": sample_id,
                "label": label,
                "repetition": str(repetition),
                "split": split,
                "source_frames": str(landmarks.shape[0]),
                "target_frames": str(target_frames),
                "standardization": action,
                "landmark_path": landmark_path.as_posix(),
            }
        )

    return (
        np.stack(x_values).astype(np.float32),
        np.asarray(y_values, dtype=np.int64),
        np.asarray(sample_ids),
        np.asarray(labels),
        np.asarray(TRIAL_LABELS),
        np.asarray(splits),
        report_rows,
    )


def split_counts(splits: np.ndarray) -> dict[str, int]:
    """Count train, validation, and test samples."""
    return {
        "train": int(np.count_nonzero(splits == "train")),
        "val": int(np.count_nonzero(splits == "val")),
        "test": int(np.count_nonzero(splits == "test")),
    }


def validate_prepared_dataset(X: np.ndarray, y: np.ndarray, splits: np.ndarray) -> None:
    """Validate expected array shapes and split totals before writing files."""
    counts = split_counts(splits)
    if X.shape != (EXPECTED_SAMPLES, TARGET_FRAMES, LANDMARK_DIM):
        raise ValueError(f"Unexpected X shape: {X.shape}")
    if y.shape != (EXPECTED_SAMPLES,):
        raise ValueError(f"Unexpected y shape: {y.shape}")
    if counts["train"] != EXPECTED_TRAIN_SAMPLES:
        raise ValueError("Unexpected train split count.")
    if counts["val"] != EXPECTED_VAL_SAMPLES:
        raise ValueError("Unexpected validation split count.")
    if counts["test"] != EXPECTED_TEST_SAMPLES:
        raise ValueError("Unexpected test split count.")


def write_split_csv(sample_ids: np.ndarray, labels: np.ndarray, y: np.ndarray, splits: np.ndarray) -> None:
    """Write the split assignment CSV next to the dataset output."""
    with SPLIT_CSV_PATH.open("w", newline="", encoding="utf-8") as split_file:
        writer = csv.writer(split_file)
        writer.writerow(["sample_id", "label", "label_index", "split"])
        for sample_id, label, label_index, split in zip(sample_ids, labels, y, splits):
            writer.writerow([sample_id, label, int(label_index), split])


def write_preparation_reports(report_rows: list[dict[str, str]], counts: dict[str, int]) -> None:
    """Save CSV and Markdown preparation reports for FYP evidence."""
    PREPARATION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "split",
        "source_frames",
        "target_frames",
        "standardization",
        "landmark_path",
    ]
    with PREPARATION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    content = f"""# Sprint 2.5 Training Dataset Preparation Report

## Summary
- Total samples: {len(report_rows)}
- Target frames: {TARGET_FRAMES}
- Landmark dimension: {LANDMARK_DIM}
- Labels: {len(TRIAL_LABELS)}
- Train samples: {counts['train']}
- Validation samples: {counts['val']}
- Test samples: {counts['test']}

## Output Files
- Dataset: {DATASET_PATH.as_posix()}
- Label mapping: {LABEL_MAPPING_PATH.as_posix()}
- Split CSV: {SPLIT_CSV_PATH.as_posix()}
- CSV report: {PREPARATION_REPORT_CSV_PATH.as_posix()}
- Markdown report: {PREPARATION_REPORT_MD_PATH.as_posix()}
"""
    PREPARATION_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_dry_run(participant_id: str, target_frames: int) -> None:
    """Print the expected dataset plan without writing dataset files."""
    print("Sprint 2.5 Dataset Preparation Dry Run")
    print("--------------------------------------")
    print(f"participant: {participant_id}")
    print(f"expected samples: {EXPECTED_SAMPLES}")
    print(f"expected X shape: ({EXPECTED_SAMPLES}, {target_frames}, {LANDMARK_DIM})")
    print(f"expected train count: {EXPECTED_TRAIN_SAMPLES}")
    print(f"expected val count: {EXPECTED_VAL_SAMPLES}")
    print(f"expected test count: {EXPECTED_TEST_SAMPLES}")
    print(f"dataset output path: {DATASET_PATH.as_posix()}")
    print(f"label mapping path: {LABEL_MAPPING_PATH.as_posix()}")
    print(f"split CSV path: {SPLIT_CSV_PATH.as_posix()}")
    print("Dry run completed. No dataset files were written.")


def main() -> int:
    """Prepare the compressed Sprint 2.5 dataset unless dry-run is requested."""
    args = parse_args()

    if args.target_frames != TARGET_FRAMES:
        raise ValueError(f"Sprint 2.5 target frames must be {TARGET_FRAMES}.")

    if args.dry_run:
        print_dry_run(args.participant, args.target_frames)
        return 0

    if DATASET_PATH.exists() and not args.overwrite:
        print(
            f"Output dataset already exists: {DATASET_PATH.as_posix()}. "
            "Use --overwrite to replace it."
        )
        return 1

    DATASET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (
        X,
        y,
        sample_ids,
        labels,
        label_names,
        splits,
        report_rows,
    ) = build_dataset_arrays(args.participant, args.target_frames)
    validate_prepared_dataset(X, y, splits)
    counts = split_counts(splits)

    np.savez_compressed(
        DATASET_PATH,
        X=X,
        y=y,
        sample_ids=sample_ids,
        labels=labels,
        label_names=label_names,
        splits=splits,
        target_frames=np.asarray(args.target_frames),
        landmark_dim=np.asarray(LANDMARK_DIM),
    )
    LABEL_MAPPING_PATH.write_text(
        json.dumps(label_mapping(), indent=2),
        encoding="utf-8",
    )
    write_split_csv(sample_ids, labels, y, splits)
    write_preparation_reports(report_rows, counts)

    print("Sprint 2.5 Training Dataset Preparation Summary")
    print("-----------------------------------------------")
    print(f"total samples: {X.shape[0]}")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"number of labels: {len(label_names)}")
    print(f"train count: {counts['train']}")
    print(f"val count: {counts['val']}")
    print(f"test count: {counts['test']}")
    print(f"output dataset path: {DATASET_PATH.as_posix()}")
    print("next command: python ml/src/check_training_dataset.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

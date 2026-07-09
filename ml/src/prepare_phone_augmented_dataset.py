"""Prepare the Sprint 2.16A mixed laptop + phone landmark dataset when samples exist."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter

from check_phone_landmark_samples import (
    summarize_counts,
    target_reached,
    validate_all_samples,
)
from phone_dataset_config import (
    DATASET_REPORT_CSV_PATH,
    DATASET_REPORT_MD_PATH,
    LANDMARK_DIMENSION,
    OLD_EXPANDED_DATASET_PATH,
    OLD_LABEL_GROUPS_PATH,
    OLD_LABEL_MAPPING_PATH,
    PARTICIPANT_ID,
    PHONE_PILOT_DATASET_PATH,
    PHONE_PILOT_LABEL_GROUPS_PATH,
    PHONE_PILOT_LABEL_MAPPING_PATH,
    PHONE_PILOT_SPLIT_CSV_PATH,
    TARGET_FRAMES,
    WEAK_LABELS,
    split_for_phone_repetition,
)


def parse_args() -> argparse.Namespace:
    """Parse dataset preparation controls."""
    parser = argparse.ArgumentParser(
        description="Prepare Sprint 2.16A mixed laptop + phone landmark dataset."
    )
    parser.add_argument("--participant", default=PARTICIPANT_ID)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def write_pending_report(phone_counts: Counter[str], reason: str) -> None:
    """Write a dataset report when the mixed dataset cannot be created yet."""
    DATASET_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["item", "value"])
        writer.writeheader()
        writer.writerow({"item": "status", "value": "PENDING"})
        writer.writerow({"item": "reason", "value": reason})
        for label in WEAK_LABELS:
            writer.writerow({"item": f"phone_{label}", "value": str(phone_counts[label])})

    count_rows = "\n".join(f"| {label} | {phone_counts[label]} |" for label in WEAK_LABELS)
    content = f"""# Sprint 2.16A Dataset Report

## Result
PENDING

## Reason
{reason}

## Phone Sample Counts
| Label | Valid Samples |
| --- | ---: |
{count_rows}

## Dataset Status
The old laptop-camera dataset was kept unchanged. The mixed phone pilot dataset was not created because the phone sample target has not been reached yet.
"""
    DATASET_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def prepare_dataset(overwrite: bool) -> bool:
    """Create the mixed sequence dataset if the phone sample target is reached."""
    samples, invalid_rows = validate_all_samples()
    counts = summarize_counts(samples)
    if invalid_rows:
        write_pending_report(counts, "Invalid phone sample files were found.")
        raise ValueError("Invalid phone sample files were found.")
    if not target_reached(counts):
        write_pending_report(counts, "Phone sample target not reached.")
        return False
    if PHONE_PILOT_DATASET_PATH.exists() and not overwrite:
        raise FileExistsError(
            f"Dataset already exists: {PHONE_PILOT_DATASET_PATH.as_posix()}. Use --overwrite."
        )
    if not OLD_EXPANDED_DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing old dataset: {OLD_EXPANDED_DATASET_PATH.as_posix()}")

    import numpy as np

    with np.load(OLD_EXPANDED_DATASET_PATH, allow_pickle=False) as old_dataset:
        required = {"X", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(old_dataset.files)
        if missing:
            raise ValueError(f"Old dataset missing arrays: {sorted(missing)}")
        old_arrays = {key: old_dataset[key] for key in old_dataset.files}

    mapping = json.loads(OLD_LABEL_MAPPING_PATH.read_text(encoding="utf-8"))
    phone_X = np.asarray([sample.frames for sample in samples], dtype=np.float32)
    if phone_X.shape[1:] != (TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(f"Unexpected phone X shape: {phone_X.shape}")
    phone_y = np.asarray([mapping[sample.label] for sample in samples], dtype=np.int64)
    phone_sample_ids = np.asarray([sample.sample_id for sample in samples])
    phone_labels = np.asarray([sample.label for sample in samples])
    phone_splits = np.asarray([split_for_phone_repetition(sample.repetition) for sample in samples])

    mixed = {
        "X": np.concatenate([old_arrays["X"], phone_X], axis=0).astype(np.float32, copy=False),
        "y": np.concatenate([old_arrays["y"], phone_y], axis=0).astype(np.int64, copy=False),
        "sample_ids": np.concatenate([old_arrays["sample_ids"], phone_sample_ids], axis=0),
        "labels": np.concatenate([old_arrays["labels"], phone_labels], axis=0),
        "splits": np.concatenate([old_arrays["splits"], phone_splits], axis=0),
        "label_names": old_arrays["label_names"],
        "source_dataset": np.asarray("signsync_expanded_v2_plus_phone_pilot"),
    }

    PHONE_PILOT_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PHONE_PILOT_DATASET_PATH, **mixed)
    PHONE_PILOT_LABEL_MAPPING_PATH.write_text(
        OLD_LABEL_MAPPING_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    PHONE_PILOT_LABEL_GROUPS_PATH.write_text(
        OLD_LABEL_GROUPS_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    write_split_csv(mixed)
    write_created_report(old_count=len(old_arrays["X"]), phone_count=len(samples), mixed=mixed)
    return True


def write_split_csv(dataset: dict[str, np.ndarray]) -> None:
    """Write split CSV for the mixed dataset."""
    with PHONE_PILOT_SPLIT_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["sample_id", "label", "split"])
        writer.writeheader()
        for sample_id, label, split in zip(
            dataset["sample_ids"].astype(str),
            dataset["labels"].astype(str),
            dataset["splits"].astype(str),
        ):
            writer.writerow({"sample_id": sample_id, "label": label, "split": split})


def write_created_report(old_count: int, phone_count: int, mixed: dict[str, np.ndarray]) -> None:
    """Write evidence for created mixed dataset."""
    split_counts = Counter(mixed["splits"].astype(str))
    DATASET_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["item", "value"])
        writer.writeheader()
        writer.writerow({"item": "status", "value": "CREATED"})
        writer.writerow({"item": "old_laptop_samples", "value": str(old_count)})
        writer.writerow({"item": "phone_samples", "value": str(phone_count)})
        writer.writerow({"item": "mixed_samples", "value": str(len(mixed["X"]))})
        for split, count in sorted(split_counts.items()):
            writer.writerow({"item": f"split_{split}", "value": str(count)})

    content = f"""# Sprint 2.16A Dataset Report

## Result
CREATED

## Summary
- Old laptop samples kept: {old_count}
- New phone samples added: {phone_count}
- Final mixed samples: {len(mixed['X'])}
- Mixed dataset: {PHONE_PILOT_DATASET_PATH.as_posix()}
- Split CSV: {PHONE_PILOT_SPLIT_CSV_PATH.as_posix()}

## Split Counts
{dict(split_counts)}
"""
    DATASET_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Prepare mixed dataset if phone samples are ready."""
    args = parse_args()
    if args.participant != PARTICIPANT_ID:
        print(f"Error: Sprint 2.16A participant must be {PARTICIPANT_ID}.")
        return 1
    try:
        created = prepare_dataset(overwrite=args.overwrite)
    except (FileNotFoundError, FileExistsError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1

    print("Sprint 2.16A Phone-Augmented Dataset Preparation")
    print("------------------------------------------------")
    if created:
        print(f"dataset: {PHONE_PILOT_DATASET_PATH.as_posix()}")
        print("Mixed dataset created successfully.")
    else:
        print("PENDING: phone sample target not reached. Mixed dataset was not created.")
    print(f"report: {DATASET_REPORT_MD_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

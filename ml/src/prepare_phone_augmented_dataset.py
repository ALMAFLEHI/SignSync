"""Prepare the V3 76-class laptop + phone dataset when phone samples exist."""

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
from labels import (
    ALL_LABELS_V3_76,
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)
from phone_dataset_config import (
    DATASET_REPORT_CSV_PATH,
    DATASET_REPORT_MD_PATH,
    LANDMARK_DIMENSION,
    OLD_EXPANDED_DATASET_PATH,
    OLD_SPLIT_CSV_PATH,
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
        description="Prepare Sprint 2.16A V3 mixed laptop + phone dataset."
    )
    parser.add_argument("--participant", default=PARTICIPANT_ID)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def inspect_historical_manifest() -> dict[str, object]:
    """Calculate active/removed counts without modifying the historical dataset."""
    if not OLD_SPLIT_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing old split manifest: {OLD_SPLIT_CSV_PATH.as_posix()}")

    rows: list[dict[str, str]] = []
    with OLD_SPLIT_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"sample_id", "label", "split"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Old split manifest must contain {sorted(required)}.")
        rows = list(reader)

    sample_ids = [row["sample_id"] for row in rows]
    duplicate_count = len(sample_ids) - len(set(sample_ids))
    if duplicate_count:
        raise ValueError(f"Old split manifest contains {duplicate_count} duplicate sample IDs.")

    active_set = set(ALL_LABELS_V3_76)
    removed_set = set(REMOVED_BANKING_INTENTS_V3_10)
    active_rows = [row for row in rows if row["label"] in active_set]
    removed_rows = [row for row in rows if row["label"] in removed_set]
    unknown_rows = [
        row for row in rows if row["label"] not in active_set and row["label"] not in removed_set
    ]
    if unknown_rows:
        unknown_labels = sorted({row["label"] for row in unknown_rows})
        raise ValueError(f"Historical manifest contains labels outside V2/V3 scope: {unknown_labels}")

    return {
        "total": len(rows),
        "active": len(active_rows),
        "removed": len(removed_rows),
        "removed_label_counts": Counter(row["label"] for row in removed_rows),
    }


def write_pending_report(
    phone_counts: Counter[str],
    reason: str,
    historical: dict[str, object],
) -> None:
    """Write actual historical counts while mixed-dataset creation is pending."""
    DATASET_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["item", "value"])
        writer.writeheader()
        writer.writerow({"item": "status", "value": "PENDING"})
        writer.writerow({"item": "reason", "value": reason})
        writer.writerow({"item": "historical_total", "value": historical["total"]})
        writer.writerow({"item": "historical_active", "value": historical["active"]})
        writer.writerow({"item": "historical_removed", "value": historical["removed"]})
        for label in WEAK_LABELS:
            writer.writerow({"item": f"phone_{label}", "value": phone_counts[label]})

    count_rows = "\n".join(f"| {label} | {phone_counts[label]} |" for label in WEAK_LABELS)
    content = f"""# Sprint 2.16A Dataset Report

## Result

PENDING

## Reason

{reason}

## Historical Scope Calculation

- Existing expanded dataset manifest: {historical['total']} samples
- Active V3 historical samples retained: {historical['active']}
- Historical samples excluded from future training: {historical['removed']}
- Historical files deleted: 0

## Phone Sample Counts

| Label | Valid Samples |
| --- | ---: |
{count_rows}

## Dataset Status

The historical 86-class dataset remains unchanged. The future 76-class mixed dataset was not created because the four-label phone sample target has not been reached.
"""
    DATASET_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def prepare_dataset(overwrite: bool) -> bool:
    """Create the active 76-class mixed sequence dataset when samples are ready."""
    historical = inspect_historical_manifest()
    samples, invalid_rows = validate_all_samples()
    counts = summarize_counts(samples)
    if invalid_rows:
        write_pending_report(counts, "Invalid phone sample files were found.", historical)
        raise ValueError("Invalid phone sample files were found.")
    if not target_reached(counts):
        write_pending_report(counts, "Phone sample target not reached.", historical)
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

    row_count = len(old_arrays["X"])
    aligned_keys = ("y", "sample_ids", "labels", "splits")
    if any(len(old_arrays[key]) != row_count for key in aligned_keys):
        raise ValueError("Historical dataset arrays do not have matching row counts.")

    old_labels = old_arrays["labels"].astype(str)
    active_mask = np.isin(old_labels, np.asarray(ALL_LABELS_V3_76))
    active_X = old_arrays["X"][active_mask].astype(np.float32, copy=False)
    active_labels = old_labels[active_mask]
    active_sample_ids = old_arrays["sample_ids"][active_mask].astype(str)
    active_splits = old_arrays["splits"][active_mask].astype(str)

    if len(active_X) != historical["active"]:
        raise ValueError("Historical NPZ active count does not match the split manifest.")
    if active_X.shape[1:] != (TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(f"Unexpected historical X shape: {active_X.shape}")
    if not np.isfinite(active_X).all():
        raise ValueError("Historical active samples contain NaN or infinite values.")

    phone_X = np.asarray([sample.frames for sample in samples], dtype=np.float32)
    if phone_X.shape[1:] != (TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(f"Unexpected phone X shape: {phone_X.shape}")
    if not np.isfinite(phone_X).all():
        raise ValueError("Phone samples contain NaN or infinite values.")

    phone_sample_ids = np.asarray([sample.sample_id for sample in samples])
    phone_labels = np.asarray([sample.label for sample in samples])
    phone_splits = np.asarray(
        [split_for_phone_repetition(sample.repetition) for sample in samples]
    )
    all_sample_ids = np.concatenate([active_sample_ids, phone_sample_ids])
    if len(all_sample_ids) != len(set(all_sample_ids.astype(str))):
        raise ValueError("Duplicate sample IDs found across historical and phone samples.")

    mapping = {label: index for index, label in enumerate(ALL_LABELS_V3_76)}
    mixed_labels = np.concatenate([active_labels, phone_labels])
    mixed_y = np.asarray([mapping[label] for label in mixed_labels], dtype=np.int64)
    mixed = {
        "X": np.concatenate([active_X, phone_X], axis=0).astype(np.float32, copy=False),
        "y": mixed_y,
        "sample_ids": all_sample_ids,
        "labels": mixed_labels,
        "splits": np.concatenate([active_splits, phone_splits]),
        "label_names": np.asarray(ALL_LABELS_V3_76),
        "source_dataset": np.asarray("signsync_scope_v3_40_phone_pilot_v1"),
    }
    if set(mixed_labels.astype(str)) != set(ALL_LABELS_V3_76):
        raise ValueError("Mixed dataset must contain all 76 active classes exactly.")

    PHONE_PILOT_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PHONE_PILOT_DATASET_PATH, **mixed)
    PHONE_PILOT_LABEL_MAPPING_PATH.write_text(
        json.dumps(mapping, indent=2) + "\n", encoding="utf-8"
    )
    PHONE_PILOT_LABEL_GROUPS_PATH.write_text(
        json.dumps(
            {
                "all_labels": ALL_LABELS_V3_76,
                "alphabet_mode": ALPHABET_LABELS,
                "number_mode": DIGIT_LABELS,
                "banking_intent_mode": BANKING_INTENTS_V3_40,
                "removed_banking_intents": REMOVED_BANKING_INTENTS_V3_10,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_split_csv(mixed)
    write_created_report(historical=historical, phone_count=len(samples), mixed=mixed)
    return True


def write_split_csv(dataset: dict[str, object]) -> None:
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


def write_created_report(
    historical: dict[str, object], phone_count: int, mixed: dict[str, object]
) -> None:
    """Write evidence for a created 76-class mixed dataset."""
    split_counts = Counter(mixed["splits"].astype(str))
    DATASET_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["item", "value"])
        writer.writeheader()
        writer.writerow({"item": "status", "value": "CREATED"})
        writer.writerow({"item": "historical_total", "value": historical["total"]})
        writer.writerow({"item": "historical_active", "value": historical["active"]})
        writer.writerow({"item": "historical_removed", "value": historical["removed"]})
        writer.writerow({"item": "phone_samples", "value": phone_count})
        writer.writerow({"item": "mixed_samples", "value": len(mixed["X"])})
        for split, count in sorted(split_counts.items()):
            writer.writerow({"item": f"split_{split}", "value": count})

    content = f"""# Sprint 2.16A Dataset Report

## Result

CREATED

## Summary

- Historical samples inspected: {historical['total']}
- Active historical samples retained: {historical['active']}
- Historical removed-label samples excluded: {historical['removed']}
- New phone samples added: {phone_count}
- Final mixed samples: {len(mixed['X'])}
- Active classes: {len(ALL_LABELS_V3_76)}
- Mixed dataset: {PHONE_PILOT_DATASET_PATH.as_posix()}
- Split CSV: {PHONE_PILOT_SPLIT_CSV_PATH.as_posix()}

Historical data remains physically unchanged.
"""
    DATASET_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Prepare the mixed dataset only after valid phone samples are ready."""
    args = parse_args()
    if args.participant != PARTICIPANT_ID:
        print(f"Error: Sprint 2.16A participant must be {PARTICIPANT_ID}.")
        return 1
    try:
        created = prepare_dataset(overwrite=args.overwrite)
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1

    print("Sprint 2.16A V3 Phone-Augmented Dataset Preparation")
    print("---------------------------------------------------")
    if created:
        print(f"dataset: {PHONE_PILOT_DATASET_PATH.as_posix()}")
        print("Mixed 76-class dataset created successfully.")
    else:
        print("PENDING: phone sample target not reached. Mixed dataset was not created.")
    print(f"report: {DATASET_REPORT_MD_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

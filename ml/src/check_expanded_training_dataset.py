"""Verify the prepared Sprint 2.12 expanded V2 training dataset and metadata files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter

import numpy as np

from expanded_dataset_config import (
    DATASET_CHECK_CSV_PATH,
    DATASET_CHECK_MD_PATH,
    DATASET_PATH,
    EXPECTED_LABELS,
    EXPECTED_SAMPLES,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    EXPANDED_DATASET_PARTICIPANT,
    LABEL_GROUPS_PATH,
    LANDMARK_DIMENSION,
    MASK_DIMENSION,
    SPLIT_CSV_PATH,
    TARGET_FRAMES,
)


def parse_args() -> argparse.Namespace:
    """Parse the participant argument retained for consistent Sprint commands."""
    parser = argparse.ArgumentParser(
        description="Verify the Sprint 2.12 expanded ML-ready training dataset."
    )
    parser.add_argument("--participant", default=EXPANDED_DATASET_PARTICIPANT)
    return parser.parse_args()


def add_check(rows: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    """Add one report-ready PASS or FAIL row."""
    rows.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def read_split_rows() -> list[dict[str, str]]:
    """Read the written split file with a clear required-column check."""
    if not SPLIT_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing split CSV: {SPLIT_CSV_PATH.as_posix()}")
    with SPLIT_CSV_PATH.open("r", newline="", encoding="utf-8") as split_file:
        rows = list(csv.DictReader(split_file))
    if not rows or set(rows[0]) != {"sample_id", "label", "label_index", "split"}:
        raise ValueError("Split CSV headers are incorrect.")
    return rows


def write_reports(rows: list[dict[str, str]], passed: bool) -> None:
    """Write the requested dataset-check CSV and Markdown evidence reports."""
    DATASET_CHECK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_CHECK_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    failed_text = "\n".join(
        f"- {row['check']}: {row['detail']}" for row in rows if row["status"] == "FAIL"
    )
    table_rows = "\n".join(
        f"| {row['check']} | {row['status']} | {row['detail']} |" for row in rows
    )
    content = f"""# Sprint 2.12 Expanded Training Dataset Check

## Result
{'PASS' if passed else 'FAIL'}

## Checks
| Check | Status | Detail |
| --- | --- | --- |
{table_rows}

## Failed Checks
{failed_text if failed_text else '- None'}

## Report Files
- CSV report: {DATASET_CHECK_CSV_PATH.as_posix()}
- Markdown report: {DATASET_CHECK_MD_PATH.as_posix()}
"""
    DATASET_CHECK_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Validate expanded tensors, splits, labels, and saved mode-group metadata."""
    parse_args()
    rows: list[dict[str, str]] = []
    if not DATASET_PATH.exists():
        add_check(rows, "dataset file", False, f"missing {DATASET_PATH.as_posix()}")
        write_reports(rows, False)
        print("FAIL: expanded training dataset file is missing.")
        return 1

    try:
        with np.load(DATASET_PATH, allow_pickle=False) as dataset:
            required_keys = {"X", "mask", "y", "sample_ids", "labels", "label_names", "splits"}
            missing_keys = required_keys.difference(dataset.files)
            if missing_keys:
                raise ValueError(f"Dataset is missing required arrays: {sorted(missing_keys)}")
            X = dataset["X"]
            mask = dataset["mask"]
            y = dataset["y"]
            sample_ids = dataset["sample_ids"].astype(str)
            labels = dataset["labels"].astype(str)
            label_names = dataset["label_names"].astype(str)
            splits = dataset["splits"].astype(str)

        add_check(rows, "X shape", X.shape == (EXPECTED_SAMPLES, TARGET_FRAMES, LANDMARK_DIMENSION), str(X.shape))
        add_check(rows, "mask shape", mask.shape == (EXPECTED_SAMPLES, TARGET_FRAMES, MASK_DIMENSION), str(mask.shape))
        add_check(rows, "y shape", y.shape == (EXPECTED_SAMPLES,), str(y.shape))
        add_check(rows, "label count", len(label_names) == EXPECTED_LABELS, str(len(label_names)))
        add_check(rows, "payment included", "payment" in label_names, str("payment" in label_names))
        add_check(rows, "receipt excluded", "receipt" not in label_names, str("receipt" not in label_names))
        add_check(rows, "document included", "document" in label_names, str("document" in label_names))
        add_check(rows, "signature included", "signature" in label_names, str("signature" in label_names))
        add_check(rows, "transaction_history excluded", "transaction_history" not in label_names, str("transaction_history" not in label_names))
        add_check(rows, "dispute_transaction excluded", "dispute_transaction" not in label_names, str("dispute_transaction" not in label_names))
        add_check(rows, "unique sample IDs", len(set(sample_ids)) == EXPECTED_SAMPLES, str(len(set(sample_ids))))
        add_check(rows, "finite landmark values", bool(np.isfinite(X).all()), "no NaN or infinity" if np.isfinite(X).all() else "NaN or infinity found")
        add_check(rows, "finite mask values", bool(np.isfinite(mask).all()), "no NaN or infinity" if np.isfinite(mask).all() else "NaN or infinity found")

        split_rows = read_split_rows()
        csv_split_counts = Counter(row["split"] for row in split_rows)
        expected_splits = {
            "train": EXPECTED_TRAIN_SAMPLES,
            "val": EXPECTED_VAL_SAMPLES,
            "test": EXPECTED_TEST_SAMPLES,
        }
        dataset_split_counts = Counter(splits)
        add_check(rows, "split CSV exists", True, SPLIT_CSV_PATH.as_posix())
        add_check(rows, "split CSV count", len(split_rows) == EXPECTED_SAMPLES, str(len(split_rows)))
        add_check(rows, "train split count", csv_split_counts["train"] == EXPECTED_TRAIN_SAMPLES, str(csv_split_counts["train"]))
        add_check(rows, "validation split count", csv_split_counts["val"] == EXPECTED_VAL_SAMPLES, str(csv_split_counts["val"]))
        add_check(rows, "test split count", csv_split_counts["test"] == EXPECTED_TEST_SAMPLES, str(csv_split_counts["test"]))
        add_check(rows, "dataset split counts", dict(dataset_split_counts) == expected_splits, str(dict(dataset_split_counts)))
        add_check(rows, "split sample ID match", {row["sample_id"] for row in split_rows} == set(sample_ids), "matches dataset" if {row["sample_id"] for row in split_rows} == set(sample_ids) else "does not match dataset")

        labels_per_split = {
            split: set(labels[splits == split])
            for split in ("train", "val", "test")
        }
        all_labels_present = set(label_names)
        every_label_in_each_split = all(
            labels_per_split[split] == all_labels_present for split in labels_per_split
        )
        add_check(rows, "every label has train/val/test samples", every_label_in_each_split, "all 86 labels represented" if every_label_in_each_split else "one or more labels missing from a split")

        if not LABEL_GROUPS_PATH.exists():
            add_check(rows, "label groups JSON", False, f"missing {LABEL_GROUPS_PATH.as_posix()}")
        else:
            groups = json.loads(LABEL_GROUPS_PATH.read_text(encoding="utf-8"))
            required_groups = {"all_labels", "normal_mode", "number_mode"}
            add_check(rows, "label groups JSON", required_groups.issubset(groups), ", ".join(sorted(groups)))
            add_check(rows, "all labels group count", len(groups.get("all_labels", [])) == EXPECTED_LABELS, str(len(groups.get("all_labels", []))))
            add_check(rows, "normal mode group", len(groups.get("normal_mode", [])) == 76, str(len(groups.get("normal_mode", []))))
            add_check(rows, "number mode group", len(groups.get("number_mode", [])) == 10, str(len(groups.get("number_mode", []))))
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        add_check(rows, "dataset verification execution", False, str(exc))

    passed = all(row["status"] == "PASS" for row in rows)
    write_reports(rows, passed)
    print("Sprint 2.12 Expanded Training Dataset Check")
    print("--------------------------------------------")
    print(f"checks passed: {sum(row['status'] == 'PASS' for row in rows)}/{len(rows)}")
    print(f"CSV report: {DATASET_CHECK_CSV_PATH.as_posix()}")
    print(f"Markdown report: {DATASET_CHECK_MD_PATH.as_posix()}")
    print("PASS: expanded training dataset check passed." if passed else "FAIL: expanded training dataset check failed.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

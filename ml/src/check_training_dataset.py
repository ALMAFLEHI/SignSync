"""Verify the prepared Sprint 2.5 training dataset."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict

import numpy as np

from dataset_config import (
    DATASET_PATH,
    EXPECTED_SAMPLES,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    LANDMARK_DIM,
    LABEL_MAPPING_PATH,
    SPLIT_CSV_PATH,
    TARGET_FRAMES,
    TRAINING_CHECK_CSV_PATH,
    TRAINING_CHECK_MD_PATH,
)
from trial_config import TRIAL_LABELS


def parse_args() -> argparse.Namespace:
    """Parse verification options."""
    parser = argparse.ArgumentParser(
        description="Verify the Sprint 2.5 prepared training dataset."
    )
    return parser.parse_args()


def add_check(rows: list[dict[str, str]], check_name: str, passed: bool, detail: str) -> None:
    """Append one CSV-ready verification check row."""
    rows.append(
        {
            "check": check_name,
            "passed": "yes" if passed else "no",
            "detail": detail,
        }
    )


def load_split_csv_rows() -> list[dict[str, str]]:
    """Read the generated split CSV."""
    if not SPLIT_CSV_PATH.exists():
        return []
    with SPLIT_CSV_PATH.open("r", newline="", encoding="utf-8") as split_file:
        return list(csv.DictReader(split_file))


def run_checks() -> list[dict[str, str]]:
    """Run all Sprint 2.5 dataset verification checks."""
    rows: list[dict[str, str]] = []

    add_check(rows, "dataset exists", DATASET_PATH.exists(), DATASET_PATH.as_posix())
    if not DATASET_PATH.exists():
        return rows

    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        required_keys = [
            "X",
            "y",
            "sample_ids",
            "labels",
            "label_names",
            "splits",
        ]
        for key in required_keys:
            add_check(rows, f"{key} exists", key in dataset.files, ", ".join(dataset.files))

        if not all(key in dataset.files for key in required_keys):
            return rows

        X = dataset["X"]
        y = dataset["y"]
        sample_ids = dataset["sample_ids"]
        labels = dataset["labels"]
        label_names = dataset["label_names"]
        splits = dataset["splits"]

        add_check(rows, "X shape", X.shape == (EXPECTED_SAMPLES, TARGET_FRAMES, LANDMARK_DIM), str(X.shape))
        add_check(rows, "y shape", y.shape == (EXPECTED_SAMPLES,), str(y.shape))
        add_check(rows, "sample_ids count", len(sample_ids) == EXPECTED_SAMPLES, str(len(sample_ids)))
        add_check(rows, "labels count", len(labels) == EXPECTED_SAMPLES, str(len(labels)))
        add_check(rows, "splits count", len(splits) == EXPECTED_SAMPLES, str(len(splits)))
        add_check(rows, "label count", len(label_names) == len(TRIAL_LABELS), str(len(label_names)))
        add_check(rows, "train count", int(np.count_nonzero(splits == "train")) == EXPECTED_TRAIN_SAMPLES, str(int(np.count_nonzero(splits == "train"))))
        add_check(rows, "val count", int(np.count_nonzero(splits == "val")) == EXPECTED_VAL_SAMPLES, str(int(np.count_nonzero(splits == "val"))))
        add_check(rows, "test count", int(np.count_nonzero(splits == "test")) == EXPECTED_TEST_SAMPLES, str(int(np.count_nonzero(splits == "test"))))
        add_check(rows, "X has no NaN", not np.isnan(X).any(), "checked")
        add_check(rows, "X has no infinite values", not np.isinf(X).any(), "checked")

        label_counts = Counter(str(label) for label in labels)
        per_label_sample_pass = all(label_counts[label] == 5 for label in TRIAL_LABELS)
        add_check(rows, "each label has 5 samples", per_label_sample_pass, str(dict(label_counts)))

        split_counts_by_label: dict[str, Counter[str]] = defaultdict(Counter)
        for label, split in zip(labels, splits):
            split_counts_by_label[str(label)][str(split)] += 1
        per_label_split_pass = all(
            split_counts_by_label[label]["train"] == 3
            and split_counts_by_label[label]["val"] == 1
            and split_counts_by_label[label]["test"] == 1
            for label in TRIAL_LABELS
        )
        add_check(rows, "each label has 3 train 1 val 1 test", per_label_split_pass, str({label: dict(split_counts_by_label[label]) for label in TRIAL_LABELS}))

    mapping_ok = False
    mapping_detail = "missing label mapping JSON"
    if LABEL_MAPPING_PATH.exists():
        mapping = json.loads(LABEL_MAPPING_PATH.read_text(encoding="utf-8"))
        expected_mapping = {label: index for index, label in enumerate(TRIAL_LABELS)}
        mapping_ok = mapping == expected_mapping
        mapping_detail = str(mapping)
    add_check(rows, "label mapping JSON", mapping_ok, mapping_detail)

    split_rows = load_split_csv_rows()
    split_csv_ok = len(split_rows) == EXPECTED_SAMPLES
    add_check(rows, "split CSV row count", split_csv_ok, str(len(split_rows)))

    return rows


def write_reports(rows: list[dict[str, str]]) -> None:
    """Save CSV and Markdown verification reports."""
    TRAINING_CHECK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRAINING_CHECK_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["check", "passed", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failed_rows = [row for row in rows if row["passed"] == "no"]
    failed_text = (
        "\n".join(f"- {row['check']}: {row['detail']}" for row in failed_rows)
        if failed_rows
        else "- None"
    )
    content = f"""# Sprint 2.5 Training Dataset Check

## Result
{"PASS" if not failed_rows else "FAIL"}

## Failed Checks
{failed_text}

## Report Files
- CSV report: {TRAINING_CHECK_CSV_PATH.as_posix()}
- Markdown report: {TRAINING_CHECK_MD_PATH.as_posix()}
"""
    TRAINING_CHECK_MD_PATH.write_text(content, encoding="utf-8")


def print_summary(rows: list[dict[str, str]]) -> None:
    """Print a clear verification summary."""
    failed_rows = [row for row in rows if row["passed"] == "no"]
    print("Sprint 2.5 Training Dataset Verification Summary")
    print("------------------------------------------------")
    print(f"checks run: {len(rows)}")
    print(f"passed checks: {len(rows) - len(failed_rows)}")
    print(f"failed checks: {len(failed_rows)}")
    print(f"CSV report path: {TRAINING_CHECK_CSV_PATH.as_posix()}")
    print(f"Markdown report path: {TRAINING_CHECK_MD_PATH.as_posix()}")
    if failed_rows:
        print("Sprint 2.5 training dataset verification failed.")
        for row in failed_rows:
            print(f"- {row['check']}: {row['detail']}")
    else:
        print("Sprint 2.5 training dataset verification passed.")


def main() -> int:
    """Run the prepared dataset verification."""
    parse_args()
    rows = run_checks()
    write_reports(rows)
    print_summary(rows)
    return 0 if all(row["passed"] == "yes" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

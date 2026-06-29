"""Verify the Sprint 2.13 756-feature training dataset."""

from __future__ import annotations

import csv
import json
from collections import Counter

import numpy as np

from tflite_model_config import (
    EXPECTED_TOTAL_SAMPLES,
    EXPECTED_TRAIN,
    EXPECTED_VAL,
    EXPECTED_TEST,
    FEATURE_CHECK_CSV_PATH,
    FEATURE_CHECK_MD_PATH,
    FEATURE_DATASET_PATH,
    INPUT_FEATURE_WIDTH,
    OUTPUT_CLASSES,
    SOURCE_LABEL_GROUPS_PATH,
    SOURCE_LABEL_MAPPING_PATH,
)


def add_check(rows: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    """Add one feature-dataset check result."""
    rows.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def write_reports(rows: list[dict[str, str]], passed: bool) -> None:
    """Write CSV and Markdown check reports."""
    FEATURE_CHECK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEATURE_CHECK_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    table = "\n".join(f"| {row['check']} | {row['status']} | {row['detail']} |" for row in rows)
    failures = "\n".join(f"- {row['check']}: {row['detail']}" for row in rows if row["status"] == "FAIL")
    content = f"""# Sprint 2.13 TFLite Feature Dataset Check

## Result
{'PASS' if passed else 'FAIL'}

## Checks
| Check | Status | Detail |
| --- | --- | --- |
{table}

## Failed Checks
{failures if failures else '- None'}
"""
    FEATURE_CHECK_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Validate the prepared 756-feature dataset."""
    rows: list[dict[str, str]] = []
    if not FEATURE_DATASET_PATH.exists():
        add_check(rows, "feature dataset exists", False, FEATURE_DATASET_PATH.as_posix())
        write_reports(rows, False)
        print("FAIL: TFLite feature dataset is missing.")
        return 1

    try:
        with np.load(FEATURE_DATASET_PATH, allow_pickle=False) as dataset:
            required = {"X_features", "y", "sample_ids", "labels", "splits", "label_names"}
            missing = required.difference(dataset.files)
            if missing:
                raise ValueError(f"Missing arrays: {sorted(missing)}")
            X_features = dataset["X_features"]
            y = dataset["y"]
            splits = dataset["splits"].astype(str)
            label_names = dataset["label_names"].astype(str)
            normal_mode_labels = dataset["normal_mode_labels"].astype(str)
            number_mode_labels = dataset["number_mode_labels"].astype(str)

        add_check(rows, "feature dataset exists", True, FEATURE_DATASET_PATH.as_posix())
        add_check(rows, "X_features shape", X_features.shape == (EXPECTED_TOTAL_SAMPLES, INPUT_FEATURE_WIDTH), str(X_features.shape))
        add_check(rows, "y shape", y.shape == (EXPECTED_TOTAL_SAMPLES,), str(y.shape))
        add_check(rows, "label count", len(label_names) == OUTPUT_CLASSES, str(len(label_names)))
        add_check(rows, "finite feature values", bool(np.isfinite(X_features).all()), "no NaN or infinity" if np.isfinite(X_features).all() else "NaN or infinity found")
        split_counts = Counter(splits)
        add_check(rows, "train split count", split_counts["train"] == EXPECTED_TRAIN, str(split_counts["train"]))
        add_check(rows, "validation split count", split_counts["val"] == EXPECTED_VAL, str(split_counts["val"]))
        add_check(rows, "test split count", split_counts["test"] == EXPECTED_TEST, str(split_counts["test"]))
        add_check(rows, "label mapping exists", SOURCE_LABEL_MAPPING_PATH.exists(), SOURCE_LABEL_MAPPING_PATH.as_posix())
        add_check(rows, "label groups exists", SOURCE_LABEL_GROUPS_PATH.exists(), SOURCE_LABEL_GROUPS_PATH.as_posix())
        mapping = json.loads(SOURCE_LABEL_MAPPING_PATH.read_text(encoding="utf-8"))
        groups = json.loads(SOURCE_LABEL_GROUPS_PATH.read_text(encoding="utf-8"))
        add_check(rows, "label mapping count", len(mapping) == OUTPUT_CLASSES, str(len(mapping)))
        add_check(rows, "normal mode count", len(normal_mode_labels) == 76 and len(groups.get("normal_mode", [])) == 76, str(len(normal_mode_labels)))
        add_check(rows, "number mode count", len(number_mode_labels) == 10 and len(groups.get("number_mode", [])) == 10, str(len(number_mode_labels)))
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        add_check(rows, "feature verification execution", False, str(exc))

    passed = all(row["status"] == "PASS" for row in rows)
    write_reports(rows, passed)
    print("Sprint 2.13 TFLite Feature Dataset Check")
    print("-----------------------------------------")
    print(f"checks passed: {sum(row['status'] == 'PASS' for row in rows)}/{len(rows)}")
    print(f"CSV report: {FEATURE_CHECK_CSV_PATH.as_posix()}")
    print(f"Markdown report: {FEATURE_CHECK_MD_PATH.as_posix()}")
    print("PASS: TFLite feature dataset check passed." if passed else "FAIL: TFLite feature dataset check failed.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

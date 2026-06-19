"""Analyze the limits of the small Sprint 2.5/Sprint 2.6 trial dataset."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from pipeline_validation_config import (
    DATASET_LIMITATION_REPORT_JSON,
    DATASET_LIMITATION_REPORT_MD,
    DATASET_PATH,
    SPLIT_CSV_PATH,
    report_path,
)


def participant_from_sample_id(sample_id: str) -> str:
    """Return the participant segment from a stable Sprint 2.5 sample ID."""
    return sample_id.split("_", 1)[0]


def repetition_from_sample_id(sample_id: str) -> str:
    """Return the repetition segment from a stable Sprint 2.5 sample ID."""
    if "_R" not in sample_id:
        raise ValueError(f"Sample ID does not contain a repetition suffix: {sample_id}")
    return sample_id.rsplit("_R", 1)[1]


def load_split_rows() -> list[dict[str, str]]:
    """Load split information without changing the existing split CSV."""
    with Path(SPLIT_CSV_PATH).open("r", newline="", encoding="utf-8") as split_file:
        rows = list(csv.DictReader(split_file))
    required_fields = {"sample_id", "label", "label_index", "split"}
    if not rows or not required_fields.issubset(rows[0]):
        raise ValueError("Sprint 2.5 split CSV has missing required columns.")
    return rows


def build_analysis() -> dict[str, object]:
    """Calculate reproducible trial-dataset counts and conservative risk findings."""
    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        X = dataset["X"]
        y = dataset["y"]
        label_names = [str(label) for label in dataset["label_names"]]

    rows = load_split_rows()
    if len(rows) != len(y):
        raise ValueError("Sprint 2.5 split CSV row count does not match the dataset sample count.")

    samples_per_label = Counter(row["label"] for row in rows)
    split_counts = Counter(row["split"] for row in rows)
    participants = sorted({participant_from_sample_id(row["sample_id"]) for row in rows})
    repetitions_by_label: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        repetitions_by_label[row["label"]].append(repetition_from_sample_id(row["sample_id"]))

    repetition_counts = {
        label: len(set(repetitions))
        for label, repetitions in sorted(repetitions_by_label.items())
    }
    test_samples_per_label = Counter(
        row["label"] for row in rows if row["split"] == "test"
    )
    one_test_sample_per_class = all(
        test_samples_per_label[label] == 1 for label in label_names
    )
    only_one_participant = len(participants) == 1

    risks = [
        "Small sample size: the trial dataset contains only 55 samples.",
        "Same participant: all trial samples are from one participant (P02).",
        "Limited environmental variation: recordings do not represent varied cameras, rooms, or capture conditions.",
        "Limited lighting and background variation: the trial data is not designed to test robustness to those changes.",
        "No cross-participant test has been performed.",
        "No full label coverage yet: only 11 of the 56 scoped labels are present.",
        "Trial labels only: the saved model was trained and evaluated on the early trial vocabulary.",
        "One test sample per class: an 11-sample test split cannot establish final production accuracy.",
    ]
    return {
        "dataset_path": DATASET_PATH,
        "x_shape": list(X.shape),
        "y_shape": list(y.shape),
        "total_samples": int(len(y)),
        "label_count": int(len(label_names)),
        "labels": label_names,
        "samples_per_label": dict(sorted(samples_per_label.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "participants": participants,
        "participant_count": len(participants),
        "repetitions_per_label": repetition_counts,
        "test_samples_per_label": dict(sorted(test_samples_per_label.items())),
        "small_dataset_detected": len(y) < 200,
        "one_participant_detected": only_one_participant,
        "one_test_sample_per_class_detected": one_test_sample_per_class,
        "production_accuracy_claim_supported": False,
        "risks": risks,
        "conclusion": (
            "Sprint 2.6 validates the machine learning pipeline, but the current result "
            "should not be interpreted as final production accuracy. More samples, more "
            "labels, and ideally more participants are required before final model evaluation."
        ),
    }


def write_reports(analysis: dict[str, object]) -> None:
    """Save FYP-ready JSON and Markdown limitation reports."""
    json_path = report_path(DATASET_LIMITATION_REPORT_JSON)
    md_path = report_path(DATASET_LIMITATION_REPORT_MD)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    samples_rows = "\n".join(
        f"| {label} | {count} | {analysis['repetitions_per_label'][label]} |"
        for label, count in analysis["samples_per_label"].items()
    )
    risk_rows = "\n".join(f"- {risk}" for risk in analysis["risks"])
    content = f"""# Sprint 2.7 Trial Dataset Limitation Report

## Dataset Summary
- Total samples: {analysis['total_samples']}
- Labels: {analysis['label_count']}
- Participants: {analysis['participant_count']} ({', '.join(analysis['participants'])})
- Train/validation/test samples: {analysis['split_counts'].get('train', 0)}/{analysis['split_counts'].get('val', 0)}/{analysis['split_counts'].get('test', 0)}
- One test sample per class: {'yes' if analysis['one_test_sample_per_class_detected'] else 'no'}
- Production accuracy claim supported: no

## Samples and Repetitions Per Label
| Label | Samples | Unique repetitions |
| --- | ---: | ---: |
{samples_rows}

## Why the 100% Trial Result Is Limited
{risk_rows}

## Conclusion
{analysis['conclusion']}

## Output Files
- JSON report: {json_path.as_posix()}
- Markdown report: {md_path.as_posix()}
"""
    md_path.write_text(content, encoding="utf-8")


def main() -> int:
    """Analyze the trial data limits without changing any dataset or model artifact."""
    analysis = build_analysis()
    write_reports(analysis)
    print("Sprint 2.7 Trial Dataset Limitation Analysis")
    print("---------------------------------------------")
    print(f"total samples: {analysis['total_samples']}")
    print(f"labels: {analysis['label_count']}")
    print(f"participants: {analysis['participant_count']} ({', '.join(analysis['participants'])})")
    print(
        "train/val/test: "
        f"{analysis['split_counts'].get('train', 0)}/"
        f"{analysis['split_counts'].get('val', 0)}/"
        f"{analysis['split_counts'].get('test', 0)}"
    )
    print(
        "one test sample per class: "
        f"{'yes' if analysis['one_test_sample_per_class_detected'] else 'no'}"
    )
    print(f"report: {report_path(DATASET_LIMITATION_REPORT_MD).as_posix()}")
    print("PASS: Dataset limitation analysis completed without changing the dataset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Analyze weak or confusing labels after Sprint 2.12 expanded evaluation."""

from __future__ import annotations

import csv

from expanded_dataset_config import (
    CONFUSION_MATRIX_CSV_PATH,
    EVALUATION_REPORT_CSV_PATH,
    WEAK_LABEL_ANALYSIS_CSV_PATH,
    WEAK_LABEL_ANALYSIS_MD_PATH,
)


LOW_F1_THRESHOLD = 0.70
LOW_RECALL_THRESHOLD = 0.70


def read_evaluation_rows() -> tuple[list[dict[str, str]], float]:
    """Read per-label metrics and the overall accuracy row."""
    if not EVALUATION_REPORT_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing evaluation report: {EVALUATION_REPORT_CSV_PATH.as_posix()}")
    with EVALUATION_REPORT_CSV_PATH.open("r", newline="", encoding="utf-8") as report_file:
        rows = list(csv.DictReader(report_file))
    accuracy_rows = [row for row in rows if row["label"] == "accuracy"]
    if not accuracy_rows:
        raise ValueError("Evaluation report does not contain an accuracy row.")
    accuracy = float(accuracy_rows[0]["f1_score"])
    per_label_rows = [
        row for row in rows
        if row["label"] not in {"accuracy", "macro avg", "weighted avg"}
    ]
    return per_label_rows, accuracy


def read_confusion_lookup() -> dict[str, tuple[str, int]]:
    """Return each true label's strongest off-diagonal confusion."""
    if not CONFUSION_MATRIX_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing confusion matrix: {CONFUSION_MATRIX_CSV_PATH.as_posix()}")
    with CONFUSION_MATRIX_CSV_PATH.open("r", newline="", encoding="utf-8") as matrix_file:
        reader = csv.DictReader(matrix_file)
        labels = [field for field in reader.fieldnames or [] if field != "true_label"]
        lookup: dict[str, tuple[str, int]] = {}
        for row in reader:
            true_label = row["true_label"]
            off_diagonal = [
                (label, int(row[label]))
                for label in labels
                if label != true_label
            ]
            predicted_label, count = max(off_diagonal, key=lambda item: item[1])
            lookup[true_label] = (predicted_label, count)
    return lookup


def build_analysis_rows(
    metric_rows: list[dict[str, str]], confusion_lookup: dict[str, tuple[str, int]]
) -> list[dict[str, str]]:
    """Identify low-F1, low-recall, and high-confusion labels."""
    analysis_rows: list[dict[str, str]] = []
    for row in metric_rows:
        label = row["label"]
        precision = float(row["precision"])
        recall = float(row["recall"])
        f1_score = float(row["f1_score"])
        support = int(row["support"])
        confused_with, confusion_count = confusion_lookup.get(label, ("", 0))
        issues: list[str] = []
        if f1_score < LOW_F1_THRESHOLD:
            issues.append("low F1")
        if recall < LOW_RECALL_THRESHOLD:
            issues.append("low recall")
        if confusion_count > 0:
            issues.append(f"confused with {confused_with}")
        analysis_rows.append(
            {
                "label": label,
                "precision": f"{precision:.6f}",
                "recall": f"{recall:.6f}",
                "f1_score": f"{f1_score:.6f}",
                "support": str(support),
                "top_confused_with": confused_with,
                "top_confusion_count": str(confusion_count),
                "weak_or_confusing": "yes" if issues else "no",
                "issues": "; ".join(issues),
            }
        )
    return analysis_rows


def write_reports(analysis_rows: list[dict[str, str]], accuracy: float) -> None:
    """Save weak-label analysis CSV and Markdown evidence."""
    WEAK_LABEL_ANALYSIS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WEAK_LABEL_ANALYSIS_CSV_PATH.open("w", newline="", encoding="utf-8") as analysis_file:
        writer = csv.DictWriter(analysis_file, fieldnames=list(analysis_rows[0]))
        writer.writeheader()
        writer.writerows(analysis_rows)

    weak_rows = [row for row in analysis_rows if row["weak_or_confusing"] == "yes"]
    weak_text = (
        "\n".join(f"- {row['label']}: {row['issues']}" for row in weak_rows)
        if weak_rows else "- None"
    )
    recommendation = (
        "Sprint 2.13 may be skipped or kept optional if the listed weak labels are acceptable."
        if accuracy >= 0.90
        else "Sprint 2.13 is recommended: add +10 recordings for weak or confusing banking intents only."
    )
    content = f"""# Sprint 2.12 Weak Label Analysis

## Summary
- Test accuracy: {accuracy:.4f}
- Weak or confusing labels found: {len(weak_rows)}
- Recommendation: {recommendation}

## Weak Or Confusing Labels
{weak_text}

## Scope Boundary
This script analyzes evaluation outputs only. It does not record data, extract landmarks, train models, or modify raw videos.

## Output Files
- CSV report: {WEAK_LABEL_ANALYSIS_CSV_PATH.as_posix()}
- Markdown report: {WEAK_LABEL_ANALYSIS_MD_PATH.as_posix()}
"""
    WEAK_LABEL_ANALYSIS_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Run weak-label analysis from saved Sprint 2.12 evaluation outputs."""
    try:
        metric_rows, accuracy = read_evaluation_rows()
        confusion_lookup = read_confusion_lookup()
        analysis_rows = build_analysis_rows(metric_rows, confusion_lookup)
        write_reports(analysis_rows, accuracy)
        print("Sprint 2.12 Weak Label Analysis Summary")
        print("---------------------------------------")
        print(f"test accuracy: {accuracy:.4f}")
        print(f"weak or confusing labels: {sum(row['weak_or_confusing'] == 'yes' for row in analysis_rows)}")
        print(f"CSV report: {WEAK_LABEL_ANALYSIS_CSV_PATH.as_posix()}")
        print(f"Markdown report: {WEAK_LABEL_ANALYSIS_MD_PATH.as_posix()}")
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate Sprint 2.19 figures only after validated physical analysis exists."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from sprint_2_19_config import FINAL_LABELS, REPORT_ROOT, WEAK_CLASSES


def _require(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required physical evaluation artifact is missing: {path}"
        )
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with _require(path).open("r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(_require(path).read_text(encoding="utf-8"))


def _write_figure_data(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate_figures(output_root: Path = REPORT_ROOT) -> list[Path]:
    """Create ten evidence figures from validated physical outputs."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    validation = _read_json(output_root / "validated" / "validation_report.json")
    if validation.get("status") != "PASS" or not validation.get(
        "physical_results_validated"
    ):
        raise ValueError("Figures require a PASS physical export validation.")
    trials = _read_csv(output_root / "validated" / "validated_trials.csv")
    per_class = _read_csv(output_root / "metrics" / "per_class_metrics.csv")
    conditions = _read_csv(output_root / "metrics" / "condition_metrics.csv")
    operational = _read_json(output_root / "metrics" / "operational_metrics.json")
    account_savings = _read_json(
        output_root / "metrics" / "account_vs_savings_metrics.json"
    )
    weak = _read_csv(output_root / "metrics" / "weak_class_metrics.csv")
    figures_dir = output_root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    def save(name: str) -> None:
        path = figures_dir / name
        plt.tight_layout()
        plt.savefig(path, dpi=180, bbox_inches="tight")
        plt.close()
        outputs.append(path)

    for normalized, source, filename in (
        (False, "confusion_matrix.csv", "confusion_matrix.png"),
        (True, "confusion_matrix_normalized.csv", "confusion_matrix_normalized.png"),
    ):
        rows = _read_csv(output_root / "confusion" / source)
        matrix = np.array(
            [[float(row[label]) for label in FINAL_LABELS] for row in rows]
        )
        plt.figure(figsize=(14, 12))
        plt.imshow(matrix, cmap="Blues", aspect="auto", vmin=0)
        plt.colorbar(label="Proportion" if normalized else "Count")
        plt.xticks(range(40), FINAL_LABELS, rotation=90, fontsize=7)
        plt.yticks(range(40), FINAL_LABELS, fontsize=7)
        plt.xlabel("Predicted label")
        plt.ylabel("Intended label")
        plt.title("Normalized confusion matrix" if normalized else "Raw confusion matrix")
        save(filename)

    labels = [row["label"] for row in per_class]
    for field, title, filename in (
        ("recall", "Per-class live recall", "per_class_recall.png"),
        ("acceptance_rate", "Per-class acceptance rate at 0.80", "per_class_acceptance.png"),
    ):
        plt.figure(figsize=(14, 5))
        plt.bar(labels, [float(row[field]) for row in per_class])
        plt.ylim(0, 1.0)
        plt.xticks(rotation=90, fontsize=8)
        plt.ylabel("Rate")
        plt.title(title)
        save(filename)

    confidence_rows = [
        {
            "confidence": row["confidence"],
            "correct_top1": row["correct_top1"],
            "accepted": row["accepted"],
        }
        for row in trials
    ]
    _write_figure_data(
        figures_dir / "confidence_distribution_data.csv",
        ["confidence", "correct_top1", "accepted"],
        confidence_rows,
    )
    plt.figure(figsize=(8, 5))
    correct = [float(row["confidence"]) for row in trials if row["correct_top1"].lower() == "true"]
    incorrect = [float(row["confidence"]) for row in trials if row["correct_top1"].lower() == "false"]
    plt.hist([correct, incorrect], bins=20, range=(0, 1), label=["Correct", "Incorrect"], alpha=0.75)
    plt.axvline(0.80, color="black", linestyle="--", label="Frozen threshold 0.80")
    plt.xlabel("Top-1 confidence")
    plt.ylabel("Trials")
    plt.legend()
    plt.title("Live confidence distribution")
    save("confidence_distribution.png")

    policy_rows = [
        {"metric": "coverage", "value": operational["coverage"]},
        {"metric": "accepted_accuracy", "value": operational["accepted_accuracy"]},
    ]
    _write_figure_data(
        figures_dir / "coverage_vs_accepted_accuracy_data.csv",
        ["metric", "value"],
        policy_rows,
    )
    plt.figure(figsize=(6, 5))
    plt.bar([row["metric"] for row in policy_rows], [row["value"] for row in policy_rows])
    plt.ylim(0, 1.0)
    plt.ylabel("Rate")
    plt.title("Frozen 0.80 policy: coverage and accepted accuracy")
    save("coverage_vs_accepted_accuracy.png")

    latency_columns = [
        "feature_computation_ms",
        "tflite_inference_ms",
        "prediction_processing_ms",
    ]
    latency_rows = [
        {column: row[column] for column in latency_columns} for row in trials
    ]
    _write_figure_data(
        figures_dir / "latency_distribution_data.csv", latency_columns, latency_rows
    )
    plt.figure(figsize=(9, 5))
    plt.boxplot(
        [[float(row[column]) for row in trials] for column in latency_columns],
        tick_labels=["Feature", "TFLite", "Prediction"],
        showfliers=True,
    )
    plt.ylabel("Milliseconds")
    plt.title("Samsung A55 post-capture latency")
    save("latency_distribution.png")

    _write_figure_data(
        figures_dir / "condition_comparison_data.csv",
        list(conditions[0]),
        conditions,
    )
    plt.figure(figsize=(8, 5))
    x = np.arange(2)
    width = 0.25
    plt.bar(x - width, [float(row["accuracy"]) for row in conditions], width, label="Accuracy")
    plt.bar(x, [float(row["macro_f1"]) for row in conditions], width, label="Macro F1")
    plt.bar(x + width, [float(row["coverage"]) for row in conditions], width, label="Coverage")
    plt.xticks(x, [row["condition"] for row in conditions])
    plt.ylim(0, 1.0)
    plt.legend()
    plt.title("Standard versus mild variation")
    save("condition_comparison.png")

    account_rows = [
        {
            "label": label,
            "raw_accuracy": account_savings[label]["raw_accuracy"],
            "accepted_accuracy": account_savings[label]["accepted_accuracy"],
            "rejection_rate": account_savings[label]["rejection_rate"],
        }
        for label in ("account", "savings")
    ]
    _write_figure_data(
        figures_dir / "account_vs_savings_data.csv", list(account_rows[0]), account_rows
    )
    plt.figure(figsize=(7, 5))
    x = np.arange(2)
    plt.bar(x - 0.18, [row["raw_accuracy"] for row in account_rows], 0.36, label="Raw accuracy")
    plt.bar(x + 0.18, [row["accepted_accuracy"] for row in account_rows], 0.36, label="Accepted accuracy")
    plt.xticks(x, ["account", "savings"])
    plt.ylim(0, 1.0)
    plt.legend()
    plt.title("Corrected account versus savings")
    save("account_vs_savings.png")

    _write_figure_data(figures_dir / "weak_class_comparison_data.csv", list(weak[0]), weak)
    weak_by_label = {row["label"]: row for row in weak}
    plt.figure(figsize=(9, 5))
    plt.bar(WEAK_CLASSES, [float(weak_by_label[label]["recall"]) for label in WEAK_CLASSES])
    plt.ylim(0, 1.0)
    plt.ylabel("Recall")
    plt.title("Predefined weaker-class live comparison")
    save("weak_class_comparison.png")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=REPORT_ROOT)
    args = parser.parse_args()
    outputs = generate_figures(args.output_root)
    print(f"PASS: generated {len(outputs)} physical-evaluation figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

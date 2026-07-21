"""Analyze a validated Sprint 2.19 live-device evaluation export."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from sprint_2_19_config import (
    CONFIDENCE_THRESHOLD,
    CONFUSION_DIR,
    DOC_SCHEDULE,
    FINAL_LABELS,
    METRICS_DIR,
    REPORTS_DIR,
    REPORT_ROOT,
    STANDARD_CONDITION,
    VARIATION_CONDITION,
    WEAK_CLASSES,
)
from sprint_2_19_evaluation import (
    classification_metrics,
    confusion_matrix,
    latency_summary,
    read_csv_rows,
    wilson_interval,
    write_csv,
    write_json,
)
from validate_sprint_2_19_live_export import validate_export


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def operational_metrics(rows: Sequence[dict[str, object]]) -> dict[str, Any]:
    """Calculate fixed-threshold operational metrics."""
    total = len(rows)
    accepted = sum(bool(row["accepted"]) for row in rows)
    correct = sum(bool(row["correct_top1"]) for row in rows)
    correct_accepted = sum(
        bool(row["correct_top1"]) and bool(row["accepted"]) for row in rows
    )
    wrong_accepted = sum(bool(row["incorrect_and_accepted"]) for row in rows)
    correct_rejected = sum(bool(row["correct_but_rejected"]) for row in rows)
    incorrect_rejected = total - correct_accepted - wrong_accepted - correct_rejected
    coverage_interval = wilson_interval(accepted, total)
    accepted_interval = wilson_interval(correct_accepted, accepted) if accepted else (0.0, 0.0)
    success_interval = wilson_interval(correct_accepted, total)
    return {
        "threshold": CONFIDENCE_THRESHOLD,
        "trial_count": total,
        "accepted_count": accepted,
        "rejected_count": total - accepted,
        "raw_correct_count": correct,
        "coverage": _rate(accepted, total),
        "coverage_wilson_95_low": coverage_interval[0],
        "coverage_wilson_95_high": coverage_interval[1],
        "rejection_rate": _rate(total - accepted, total),
        "accepted_accuracy": _rate(correct_accepted, accepted),
        "accepted_accuracy_wilson_95_low": accepted_interval[0],
        "accepted_accuracy_wilson_95_high": accepted_interval[1],
        "operational_success": _rate(correct_accepted, total),
        "operational_success_wilson_95_low": success_interval[0],
        "operational_success_wilson_95_high": success_interval[1],
        "correct_and_accepted_rate": _rate(correct_accepted, total),
        "incorrect_and_accepted_rate": _rate(wrong_accepted, total),
        "correct_but_rejected_rate": _rate(correct_rejected, total),
        "wrong_acceptance_count": wrong_accepted,
        "correct_rejection_count": incorrect_rejected,
        "try_again_count": total - accepted,
    }


def condition_metrics(
    rows: Sequence[dict[str, object]],
    technical_events: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    """Calculate metrics independently for both controlled conditions."""
    output: list[dict[str, Any]] = []
    for condition in (STANDARD_CONDITION, VARIATION_CONDITION):
        subset = [row for row in rows if row["condition"] == condition]
        overall, _ = classification_metrics(subset)
        operational = operational_metrics(subset)
        accuracy_interval = wilson_interval(int(overall["correct_count"]), len(subset))
        output.append(
            {
                "condition": condition,
                "trial_count": len(subset),
                "accuracy": overall["accuracy"],
                "accuracy_wilson_95_low": accuracy_interval[0],
                "accuracy_wilson_95_high": accuracy_interval[1],
                "macro_f1": overall["macro_f1"],
                "accepted_accuracy": operational["accepted_accuracy"],
                "coverage": operational["coverage"],
                "rejection_rate": operational["rejection_rate"],
                "wrong_acceptance_rate": operational[
                    "incorrect_and_accepted_rate"
                ],
                "mean_confidence": statistics.fmean(
                    float(row["confidence"]) for row in subset
                ),
                "median_confidence": statistics.median(
                    float(row["confidence"]) for row in subset
                ),
                "capture_duration_mean_ms": statistics.fmean(
                    float(row["capture_duration_ms"]) for row in subset
                ),
                "feature_computation_mean_ms": statistics.fmean(
                    float(row["feature_computation_ms"]) for row in subset
                ),
                "tflite_inference_mean_ms": statistics.fmean(
                    float(row["tflite_inference_ms"]) for row in subset
                ),
                "prediction_processing_mean_ms": statistics.fmean(
                    float(row["prediction_processing_ms"]) for row in subset
                ),
                "technical_failure_count": sum(
                    event.get("condition") == condition
                    and int(event.get("trial_number", "0")) > 0
                    for event in technical_events
                ),
            }
        )
    return output


def account_savings_metrics(rows: Sequence[dict[str, object]]) -> dict[str, Any]:
    """Create the dedicated corrected account-versus-savings result."""
    result: dict[str, Any] = {
        "account_to_savings_count": sum(
            row["intended_label"] == "account" and row["predicted_label"] == "savings"
            for row in rows
        ),
        "savings_to_account_count": sum(
            row["intended_label"] == "savings" and row["predicted_label"] == "account"
            for row in rows
        ),
    }
    for label in ("account", "savings"):
        subset = [row for row in rows if row["intended_label"] == label]
        accepted = [row for row in subset if bool(row["accepted"])]
        result[label] = {
            "support": len(subset),
            "raw_accuracy": _rate(
                sum(bool(row["correct_top1"]) for row in subset), len(subset)
            ),
            "accepted_accuracy": _rate(
                sum(bool(row["correct_top1"]) for row in accepted), len(accepted)
            ),
            "rejection_rate": _rate(len(subset) - len(accepted), len(subset)),
            "mean_confidence": statistics.fmean(
                float(row["confidence"]) for row in subset
            ),
            "standard_accuracy": _rate(
                sum(
                    bool(row["correct_top1"])
                    for row in subset
                    if row["condition"] == STANDARD_CONDITION
                ),
                5,
            ),
            "mild_variation_accuracy": _rate(
                sum(
                    bool(row["correct_top1"])
                    for row in subset
                    if row["condition"] == VARIATION_CONDITION
                ),
                5,
            ),
            "other_confusions": dict(
                Counter(
                    str(row["predicted_label"])
                    for row in subset
                    if not bool(row["correct_top1"])
                )
            ),
        }
    return result


def weak_class_metrics(
    rows: Sequence[dict[str, object]],
    per_class: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add condition and confusion details for the five predefined weak classes."""
    base = {str(row["label"]): row for row in per_class}
    output: list[dict[str, Any]] = []
    for label in WEAK_CLASSES:
        subset = [row for row in rows if row["intended_label"] == label]
        incorrect = [row for row in subset if not bool(row["correct_top1"])]
        output.append(
            {
                **base[label],
                "accuracy": _rate(
                    sum(bool(row["correct_top1"]) for row in subset), len(subset)
                ),
                "standard_accuracy": _rate(
                    sum(
                        bool(row["correct_top1"])
                        for row in subset
                        if row["condition"] == STANDARD_CONDITION
                    ),
                    5,
                ),
                "mild_variation_accuracy": _rate(
                    sum(
                        bool(row["correct_top1"])
                        for row in subset
                        if row["condition"] == VARIATION_CONDITION
                    ),
                    5,
                ),
                "main_confusions": json.dumps(
                    Counter(str(row["predicted_label"]) for row in incorrect),
                    sort_keys=True,
                ),
                "high_confidence_incorrect_count": sum(
                    float(row["confidence"]) >= 0.90 for row in incorrect
                ),
            }
        )
    return output


def _load_technical_events(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    _, rows = read_csv_rows(path)
    return rows


def _write_matrix(path: Path, matrix: Sequence[Sequence[float | int]]) -> None:
    rows = [
        {"intended_label": label, **{predicted: values[index] for index, predicted in enumerate(FINAL_LABELS)}}
        for label, values in zip(FINAL_LABELS, matrix)
    ]
    write_csv(path, ["intended_label", *FINAL_LABELS], rows)


def analyze(
    live_trials: Path,
    session_metadata: Path,
    technical_events_path: Path | None,
    schedule: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Validate first, then create every machine-readable metric artifact."""
    validated_dir = output_root / "validated"
    metrics_dir = output_root / "metrics"
    confusion_dir = output_root / "confusion"
    reports_dir = output_root / "reports"
    rows = validate_export(
        live_trials,
        session_metadata,
        schedule,
        validated_dir,
        technical_events_path,
    )
    technical_events = _load_technical_events(technical_events_path)

    overall, per_class = classification_metrics(rows)
    operational = operational_metrics(rows)
    conditions = condition_metrics(rows, technical_events)
    account_savings = account_savings_metrics(rows)
    weak = weak_class_metrics(rows, per_class)
    raw_matrix = confusion_matrix(rows)
    normalized = [
        [value / sum(matrix_row) if sum(matrix_row) else 0.0 for value in matrix_row]
        for matrix_row in raw_matrix
    ]
    confusion_pairs = [
        {
            "intended_label": FINAL_LABELS[row_index],
            "predicted_label": FINAL_LABELS[column_index],
            "count": raw_matrix[row_index][column_index],
        }
        for row_index in range(len(FINAL_LABELS))
        for column_index in range(len(FINAL_LABELS))
        if row_index != column_index and raw_matrix[row_index][column_index] > 0
    ]
    confusion_pairs.sort(key=lambda row: (-int(row["count"]), str(row["intended_label"])))

    latency_fields = {
        "capture_duration_ms": "capture_duration_ms",
        "average_capture_fps": "average_capture_fps",
        "feature_computation_ms": "feature_computation_ms",
        "tflite_inference_ms": "tflite_inference_ms",
        "prediction_processing_ms": "prediction_processing_ms",
        "model_load_ms": "model_load_ms",
    }
    latency = {
        output_name: latency_summary([float(row[field]) for row in rows])
        for output_name, field in latency_fields.items()
    }
    incorrect = [row for row in rows if not bool(row["correct_top1"])]
    def distribution(values: list[float]) -> dict[str, float | int]:
        return latency_summary(values) if values else {"count": 0}

    confidence = {
        "correct": latency_summary(
            [float(row["confidence"]) for row in rows if bool(row["correct_top1"])]
        ),
        "incorrect": distribution([float(row["confidence"]) for row in incorrect]),
        "accepted": distribution(
            [float(row["confidence"]) for row in rows if bool(row["accepted"])]
        ),
        "rejected": distribution(
            [float(row["confidence"]) for row in rows if not bool(row["accepted"])]
        ),
        "margin": latency_summary([float(row["confidence_margin"]) for row in rows]),
        "incorrect_at_or_above_0_95": sum(
            float(row["confidence"]) >= 0.95 for row in incorrect
        ),
        "incorrect_at_or_above_0_90": sum(
            float(row["confidence"]) >= 0.90 for row in incorrect
        ),
        "incorrect_at_or_above_0_80": sum(
            float(row["confidence"]) >= 0.80 for row in incorrect
        ),
        "correct_below_0_80": sum(
            bool(row["correct_top1"]) and float(row["confidence"]) < 0.80
            for row in rows
        ),
        "high_confidence_errors": [
            {
                "trial_number": row["trial_number"],
                "condition": row["condition"],
                "intended_label": row["intended_label"],
                "predicted_label": row["predicted_label"],
                "confidence": row["confidence"],
            }
            for row in incorrect
            if float(row["confidence"]) >= 0.90
        ],
    }
    event_counts = Counter(row.get("event_type", "unknown") for row in technical_events)
    technical = {
        "total_scheduled_trials": 400,
        "valid_inference_trials": len(rows),
        "technical_capture_failures": len(technical_events),
        "event_type_counts": dict(event_counts),
        "camera_failures": sum(
            event_counts[key]
            for key in ("camera_error", "camera_unavailable", "camera_permission_issue")
        ),
        "no_hand_failures": event_counts["no_hands_detected"],
        "insufficient_frame_failures": event_counts["insufficient_valid_frames"],
        "model_load_failures": event_counts["model_load_failure"],
        "non_finite_output_failures": event_counts["non_finite_output"],
        "app_crashes": event_counts["app_crash"],
        "forced_restarts": event_counts["forced_restart"],
        "evaluation_resumptions": event_counts["evaluation_resumed"],
        "export_failures": event_counts["export_failure"],
        "data_integrity_failures": event_counts["data_integrity_failure"],
        "capture_attempts": len(rows) + len(technical_events),
        "operational_completion_rate": _rate(
            len(rows), len(rows) + len(technical_events)
        ),
    }

    write_json(metrics_dir / "overall_metrics.json", overall)
    write_csv(metrics_dir / "per_class_metrics.csv", list(per_class[0]), per_class)
    write_json(metrics_dir / "operational_metrics.json", operational)
    write_csv(metrics_dir / "condition_metrics.csv", list(conditions[0]), conditions)
    write_json(metrics_dir / "latency_metrics.json", latency)
    write_json(metrics_dir / "confidence_metrics.json", confidence)
    write_json(metrics_dir / "account_vs_savings_metrics.json", account_savings)
    write_csv(metrics_dir / "weak_class_metrics.csv", list(weak[0]), weak)
    write_json(metrics_dir / "technical_stability_metrics.json", technical)
    _write_matrix(confusion_dir / "confusion_matrix.csv", raw_matrix)
    _write_matrix(confusion_dir / "confusion_matrix_normalized.csv", normalized)
    write_csv(
        confusion_dir / "confusion_pairs.csv",
        ["intended_label", "predicted_label", "count"],
        confusion_pairs,
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_human_reports(
        reports_dir,
        overall,
        operational,
        conditions,
        account_savings,
        weak,
        latency,
        confidence,
        technical,
        confusion_pairs,
    )
    return {
        "overall": overall,
        "operational": operational,
        "conditions": conditions,
        "technical": technical,
    }


def _percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def _write_human_reports(
    reports_dir: Path,
    overall: dict[str, Any],
    operational: dict[str, Any],
    conditions: Sequence[dict[str, Any]],
    account_savings: dict[str, Any],
    weak: Sequence[dict[str, Any]],
    latency: dict[str, Any],
    confidence: dict[str, Any],
    technical: dict[str, Any],
    confusion_pairs: Sequence[dict[str, Any]],
) -> None:
    final_report = (
        "# Sprint 2.19 Final Live Technical Evaluation\n\n"
        f"- Valid trials: {overall['trial_count']}\n"
        f"- Live top-1 accuracy: {_percentage(float(overall['accuracy']))}\n"
        f"- Macro precision: {_percentage(float(overall['macro_precision']))}\n"
        f"- Macro recall: {_percentage(float(overall['macro_recall']))}\n"
        f"- Macro F1: {_percentage(float(overall['macro_f1']))}\n"
        f"- Weighted F1: {_percentage(float(overall['weighted_f1']))}\n"
        f"- Coverage at 0.80: {_percentage(float(operational['coverage']))}\n"
        f"- Accepted accuracy: {_percentage(float(operational['accepted_accuracy']))}\n"
        "\nThe corrected model, label order, feature contract, and 0.80 threshold "
        "were frozen. No training or threshold tuning occurred.\n"
    )
    (reports_dir / "final_live_evaluation_report.md").write_text(final_report, encoding="utf-8")
    (reports_dir / "operational_performance_report.md").write_text(
        "# Operational Performance\n\n```json\n"
        + json.dumps({"operational": operational, "technical": technical}, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    (reports_dir / "latency_report.md").write_text(
        "# Samsung A55 Latency\n\n```json\n"
        + json.dumps(latency, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    (reports_dir / "account_vs_savings_report.md").write_text(
        "# Account Versus Savings\n\n```json\n"
        + json.dumps(account_savings, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    (reports_dir / "error_analysis.md").write_text(
        "# Error Analysis\n\n"
        "Observed confusion pairs and high-confidence errors are reported without "
        "assigning unsupported causes.\n\n```json\n"
        + json.dumps(
            {
                "top_confusion_pairs": list(confusion_pairs[:20]),
                "weak_classes": list(weak),
                "confidence": confidence,
                "conditions": list(conditions),
            },
            indent=2,
        )
        + "\n```\n",
        encoding="utf-8",
    )
    (reports_dir / "limitations.md").write_text(
        "# Limitations\n\n"
        "- One primary signer and one Samsung Galaxy A55 were evaluated.\n"
        "- Per-class support is 10, so class-level estimates are imprecise.\n"
        "- Results do not establish generalization to all ASL users or devices.\n"
        "- This was a technical evaluation, not usability or banking field testing.\n"
        "- Sprint 2.20 was not started.\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-trials", type=Path, required=True)
    parser.add_argument("--session-metadata", type=Path, required=True)
    parser.add_argument("--technical-events", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, default=DOC_SCHEDULE)
    parser.add_argument("--output-root", type=Path, default=REPORT_ROOT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = analyze(
        args.live_trials,
        args.session_metadata,
        args.technical_events,
        args.schedule,
        args.output_root,
    )
    print(f"PASS: analyzed {result['overall']['trial_count']} validated live trials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

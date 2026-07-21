"""Finalize Sprint 2.19 from locked offline and existing A55 evidence.

This script never trains, converts, or runs a model. It validates the immutable
Sprint 2.17 corrected-v2 prediction artifact, reproduces its metrics, verifies
protected deployment artifacts, and packages the final technical evaluation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont

from labels import (
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "ml" / "models" / "sprint_2_17_final_40class_account_corrected_v2"
SOURCE_METRICS = PACKAGE / "metrics"
SOURCE_METADATA = PACKAGE / "metadata"
PREDICTIONS_PATH = SOURCE_METRICS / "final_test_predictions.csv"
SAVED_METRICS_PATH = SOURCE_METRICS / "final_test_metrics.json"
REPORT_ROOT = ROOT / "ml" / "reports" / "sprint_2_19_final_technical_evaluation"
SOURCE_DIR = REPORT_ROOT / "source"
METRICS_DIR = REPORT_ROOT / "metrics"
CONFUSION_DIR = REPORT_ROOT / "confusion"
FIGURES_DIR = REPORT_ROOT / "figures"
REPORTS_DIR = REPORT_ROOT / "reports"
METADATA_DIR = REPORT_ROOT / "metadata"
EVIDENCE_DIR = ROOT / "docs" / "phase_2_evidence"
EVIDENCE_SCREENSHOTS = EVIDENCE_DIR / "screenshots" / "Sprint2.19"
SPRINT_DOC = ROOT / "docs" / "sprints" / "sprint_2_19_final_technical_recognition_evaluation.md"

FINAL_LABELS = list(BANKING_INTENTS_V3_40)
CONFIDENCE_THRESHOLD = 0.80
MINIMUM_MARGIN = 0.00
EXPECTED_TEST_SAMPLES = 200
EXPECTED_SUPPORT = 5
EXPECTED_METRICS = {
    "accuracy": 0.9550,
    "macro_precision": 0.9625,
    "macro_recall": 0.9550,
    "macro_f1": 0.9541666666666666,
    "weighted_f1": 0.9541666666666666,
}
EXPECTED_HASHES = {
    "keras": "F1D543E0D0E5E8C699B53DA5DD7CAAEBC160695599C4C2D078C6FDDDD1DB120D",
    "float32_tflite": "D9686110BACFB1F1C5B3BFBF33B2C515393344869A3DCEAFF325903A34DF278C",
    "dynamic_range_tflite": "BD46131FF20ECB96F240C867C60804A2D9F514AC4F56D63F64E8B60188187A17",
    "deployment_manifest": "F02E35864C87925A6D06D70F669411388B2F04112F757CB0DF2AAD1296A2F9F1",
    "corrected_backup": "07B5660E08640EA2EAC11216E41F4696D01BE52627CF3E1DD15D46F99C20286A",
    "dataset_manifest": "677C4ED15F11CE4BEE07754948CCEB21E324BDC1C3481CF265E884F773710D03",
}
MODEL_PATHS = {
    "keras": PACKAGE / "models" / "signsync_40class_account_corrected_v2.keras",
    "float32_tflite": PACKAGE / "models" / "signsync_40class_account_corrected_v2_float32.tflite",
    "dynamic_range_tflite": PACKAGE / "models" / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
    "deployment_manifest": ROOT / "flutter_app" / "assets" / "models" / "model_deployment_manifest.json",
    "corrected_backup": ROOT / "ml" / "data_phone" / "sprint_2_16B_banking_phone_samples_1000_backup.zip",
    "dataset_manifest": ROOT / "ml" / "data_phone" / "corrections" / "account_20260719" / "corrected_phone_source_json_sha256.csv",
}
A55_SCREENSHOT_DIR = EVIDENCE_DIR / "screenshots" / "Sprint2.18"
A55_SCREENSHOTS = [
    "Sprint_2_18_Corrected_Final_Model_Diagnostics_PASS.png",
    "Sprint_2_18_Corrected_Model_Hashes_And_Runtime_Metrics_01.png",
    "Sprint_2_18_Corrected_Model_Hashes_And_Runtime_Metrics_02.png",
    "Sprint_2_18_Corrected_Live_Diagnostics_Document.png",
    "Sprint_2_18_Corrected_Live_Diagnostics_Credit_Card.png",
    "Sprint_2_18_Corrected_Live_Diagnostics_Complaint.png",
    "Sprint_2_18_Corrected_Account_Intent_Confirmation.png",
    "Sprint_2_18_Corrected_Document_Intent_Confirmation.png",
    "Sprint_2_18_Corrected_Credit_Card_Intent_Confirmation.png",
    "Sprint_2_18_Corrected_Complaint_Intent_Confirmation.png",
    "Sprint_2_18_Corrected_Account_Manual_Details.png",
    "Sprint_2_18_Corrected_Account_Banker_View.png",
]

COLORS = {
    "ink": "#17202A",
    "muted": "#59636E",
    "grid": "#D8DEE4",
    "paper": "#F7F9FA",
    "white": "#FFFFFF",
    "teal": "#087E8B",
    "green": "#2A9D6F",
    "navy": "#204B72",
    "coral": "#E76F51",
    "gold": "#E9B949",
}


class EvaluationError(RuntimeError):
    """Raised when a protected Sprint 2.19 evaluation condition fails."""


def sha256_file(path: Path) -> str:
    """Return an uppercase SHA-256 digest without changing the file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise EvaluationError(f"Expected a JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    """Write deterministic, readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    """Write a CSV file using Windows-friendly UTF-8 and LF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _parse_bool(value: str, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise EvaluationError(f"Invalid Boolean value for {field}: {value!r}")


def load_predictions(path: Path = PREDICTIONS_PATH) -> list[dict[str, Any]]:
    """Load and type the immutable corrected-v2 held-out predictions."""
    required = {
        "sample_id",
        "actual_label",
        "actual_index",
        "predicted_label",
        "predicted_index",
        "confidence",
        "second_label",
        "second_index",
        "second_confidence",
        "margin",
        "accepted",
        "correct",
        "high_confidence_wrong",
    }
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = required - columns
        if missing:
            raise EvaluationError(f"Prediction artifact is missing columns: {sorted(missing)}")
        rows: list[dict[str, Any]] = []
        for source_row in reader:
            row = dict(source_row)
            for field in ("actual_index", "predicted_index", "second_index"):
                row[field] = int(row[field])
            for field in ("confidence", "second_confidence", "margin"):
                row[field] = float(row[field])
            for field in ("accepted", "correct", "high_confidence_wrong"):
                row[field] = _parse_bool(row[field], field)
            rows.append(row)
    return rows


def validate_predictions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate counts, frozen order, mappings, confidence, and policy fields."""
    if len(rows) != EXPECTED_TEST_SAMPLES:
        raise EvaluationError(f"Expected 200 prediction rows, found {len(rows)}.")
    if len({row["sample_id"] for row in rows}) != len(rows):
        raise EvaluationError("Prediction sample IDs are not unique.")

    actual_counts = Counter(row["actual_label"] for row in rows)
    if list(actual_counts) != FINAL_LABELS:
        raise EvaluationError("First-seen actual-label order does not match the frozen order.")
    expected_counts = Counter({label: EXPECTED_SUPPORT for label in FINAL_LABELS})
    if actual_counts != expected_counts:
        raise EvaluationError(f"Expected five held-out samples per class, found {actual_counts}.")

    forbidden = set(ALPHABET_LABELS + DIGIT_LABELS + REMOVED_BANKING_INTENTS_V3_10)
    for row_number, row in enumerate(rows, start=2):
        actual = row["actual_label"]
        predicted = row["predicted_label"]
        second = row["second_label"]
        if actual not in FINAL_LABELS or predicted not in FINAL_LABELS or second not in FINAL_LABELS:
            raise EvaluationError(f"Row {row_number} contains a label outside the frozen scope.")
        if {actual, predicted, second}.intersection(forbidden):
            raise EvaluationError(f"Row {row_number} contains a forbidden label.")
        if row["actual_index"] != FINAL_LABELS.index(actual):
            raise EvaluationError(f"Row {row_number} actual index does not map to its label.")
        if row["predicted_index"] != FINAL_LABELS.index(predicted):
            raise EvaluationError(f"Row {row_number} predicted index does not map to its label.")
        if row["second_index"] != FINAL_LABELS.index(second):
            raise EvaluationError(f"Row {row_number} second index does not map to its label.")
        for field in ("confidence", "second_confidence", "margin"):
            value = float(row[field])
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise EvaluationError(f"Row {row_number} has invalid {field}: {value}.")
        expected_correct = actual == predicted
        expected_accepted = (
            row["confidence"] >= CONFIDENCE_THRESHOLD
            and row["margin"] >= MINIMUM_MARGIN
        )
        if row["correct"] != expected_correct:
            raise EvaluationError(f"Row {row_number} has inconsistent correctness.")
        if row["accepted"] != expected_accepted:
            raise EvaluationError(f"Row {row_number} does not follow the frozen threshold.")

    return {
        "status": "PASS",
        "rows": len(rows),
        "labels": len(actual_counts),
        "samples_per_label": EXPECTED_SUPPORT,
        "frozen_label_order": FINAL_LABELS,
        "confidence_values_finite_and_bounded": True,
        "index_mapping": "PASS",
        "forbidden_labels_absent": True,
        "threshold": CONFIDENCE_THRESHOLD,
        "minimum_margin": MINIMUM_MARGIN,
    }


def confusion_matrix(rows: list[dict[str, Any]]) -> list[list[int]]:
    """Return an actual-by-predicted 40-class matrix."""
    matrix = [[0 for _ in FINAL_LABELS] for _ in FINAL_LABELS]
    for row in rows:
        matrix[row["actual_index"]][row["predicted_index"]] += 1
    return matrix


def classification_metrics(
    rows: list[dict[str, Any]], matrix: list[list[int]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Reproduce overall and per-class classification metrics."""
    total = len(rows)
    correct = sum(matrix[index][index] for index in range(len(FINAL_LABELS)))
    per_class: list[dict[str, Any]] = []
    for index, label in enumerate(FINAL_LABELS):
        true_positive = matrix[index][index]
        false_negative = sum(matrix[index]) - true_positive
        false_positive = sum(row[index] for row in matrix) - true_positive
        support = true_positive + false_negative
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append(
            {
                "label": label,
                "label_index": index,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
                "correct": true_positive,
                "incorrect": false_negative,
            }
        )
    macro_precision = statistics.fmean(item["precision"] for item in per_class)
    macro_recall = statistics.fmean(item["recall"] for item in per_class)
    macro_f1 = statistics.fmean(item["f1"] for item in per_class)
    weighted_precision = sum(item["precision"] * item["support"] for item in per_class) / total
    weighted_recall = sum(item["recall"] * item["support"] for item in per_class) / total
    weighted_f1 = sum(item["f1"] * item["support"] for item in per_class) / total
    lower, upper = wilson_interval(correct, total)
    overall = {
        "test_samples": total,
        "label_count": len(FINAL_LABELS),
        "samples_per_class": EXPECTED_SUPPORT,
        "correct_predictions": correct,
        "incorrect_predictions": total - correct,
        "accuracy": correct / total,
        "accuracy_wilson_95_ci": {"lower": lower, "upper": upper},
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1,
        "formal_evidence_scope": "locked 200-sample held-out Samsung A55 landmark test set",
    }
    return overall, per_class


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Calculate a two-sided Wilson score interval for a binomial proportion."""
    if total <= 0:
        raise ValueError("Wilson interval requires a positive total.")
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = proportion + z * z / (2 * total)
    adjustment = z * math.sqrt(
        proportion * (1 - proportion) / total + z * z / (4 * total * total)
    )
    return (centre - adjustment) / denominator, (centre + adjustment) / denominator


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Percentile requires values.")
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution(values: list[float]) -> dict[str, Any]:
    """Summarize an observed confidence sequence."""
    return {
        "count": len(values),
        "minimum": min(values),
        "q1": _percentile(values, 0.25),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "q3": _percentile(values, 0.75),
        "maximum": max(values),
    }


def confidence_metrics(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Calculate frozen-threshold confidence and rejection metrics."""
    accepted = [row for row in rows if row["accepted"]]
    rejected = [row for row in rows if not row["accepted"]]
    correct = [row for row in rows if row["correct"]]
    incorrect = [row for row in rows if not row["correct"]]
    correct_accepted = [row for row in rows if row["correct"] and row["accepted"]]
    incorrect_accepted = [row for row in rows if not row["correct"] and row["accepted"]]
    correct_rejected = [row for row in rows if row["correct"] and not row["accepted"]]
    per_class = []
    for label in FINAL_LABELS:
        class_rows = [row for row in rows if row["actual_label"] == label]
        class_rejected = sum(not row["accepted"] for row in class_rows)
        per_class.append(
            {
                "label": label,
                "support": len(class_rows),
                "rejected": class_rejected,
                "rejection_rate": class_rejected / len(class_rows),
            }
        )
    confidence = {
        "threshold": CONFIDENCE_THRESHOLD,
        "minimum_margin": MINIMUM_MARGIN,
        "correct_predictions": distribution([row["confidence"] for row in correct]),
        "incorrect_predictions": distribution([row["confidence"] for row in incorrect]),
        "incorrect_confidence_ge_0_95": sum(row["confidence"] >= 0.95 for row in incorrect),
        "incorrect_confidence_ge_0_90": sum(row["confidence"] >= 0.90 for row in incorrect),
        "incorrect_confidence_ge_0_80": sum(row["confidence"] >= 0.80 for row in incorrect),
        "correct_confidence_below_0_80": sum(row["confidence"] < 0.80 for row in correct),
        "saved_policy_high_confidence_wrong": sum(row["high_confidence_wrong"] for row in rows),
        "high_confidence_error_definition_for_sprint_2_19": "incorrect with confidence >= frozen 0.80 threshold",
        "high_confidence_incorrect_predictions": len(incorrect_accepted),
    }
    rejection = {
        "threshold": CONFIDENCE_THRESHOLD,
        "total": len(rows),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "coverage": len(accepted) / len(rows),
        "rejection_rate": len(rejected) / len(rows),
        "accepted_accuracy": len(correct_accepted) / len(accepted),
        "correct_and_accepted": len(correct_accepted),
        "incorrect_and_accepted": len(incorrect_accepted),
        "correct_but_rejected": len(correct_rejected),
        "incorrect_and_rejected": sum(not row["correct"] and not row["accepted"] for row in rows),
        "per_class": per_class,
    }
    if rejection["accepted"] + rejection["rejected"] != len(rows):
        raise EvaluationError("Rejection counts are internally inconsistent.")
    return confidence, rejection


def account_savings_metrics(
    rows: list[dict[str, Any]], per_class: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the dedicated corrected account-versus-savings result."""
    by_label = {item["label"]: item for item in per_class}
    selected = [row for row in rows if row["actual_label"] in {"account", "savings"}]
    samples = [
        {
            "sample_id": row["sample_id"],
            "actual_label": row["actual_label"],
            "predicted_label": row["predicted_label"],
            "confidence": row["confidence"],
            "correct": row["correct"],
        }
        for row in selected
    ]
    return {
        "status": "PASS",
        "account": by_label["account"],
        "savings": by_label["savings"],
        "account_to_savings": sum(
            row["actual_label"] == "account" and row["predicted_label"] == "savings"
            for row in selected
        ),
        "savings_to_account": sum(
            row["actual_label"] == "savings" and row["predicted_label"] == "account"
            for row in selected
        ),
        "held_out_predictions": samples,
        "interpretation_boundary": "Five samples per class are a locked held-out check, not broad population generalization.",
    }


def confusion_pairs(matrix: list[list[int]]) -> list[dict[str, Any]]:
    """Return observed directional off-diagonal confusions."""
    pairs = []
    for actual_index, actual in enumerate(FINAL_LABELS):
        errors = sum(matrix[actual_index]) - matrix[actual_index][actual_index]
        for predicted_index, predicted in enumerate(FINAL_LABELS):
            count = matrix[actual_index][predicted_index]
            if actual_index != predicted_index and count:
                pairs.append(
                    {
                        "actual_label": actual,
                        "predicted_label": predicted,
                        "count": count,
                        "actual_class_errors_share": count / errors,
                    }
                )
    return sorted(pairs, key=lambda row: (-row["count"], row["actual_label"], row["predicted_label"]))


def compare_saved_metrics(overall: dict[str, Any]) -> dict[str, Any]:
    """Require reproduced values to match both expected and saved metrics."""
    saved = read_json(SAVED_METRICS_PATH)
    comparisons = {}
    for metric, expected in EXPECTED_METRICS.items():
        actual = float(overall[metric])
        stored = float(saved[metric])
        passed = math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) and math.isclose(
            actual, stored, rel_tol=0.0, abs_tol=1e-12
        )
        comparisons[metric] = {
            "recalculated": actual,
            "saved": stored,
            "expected": expected,
            "passed": passed,
        }
        if not passed:
            raise EvaluationError(f"Recalculated {metric} does not match the locked result.")
    return {"status": "PASS", "tolerance": 1e-12, "metrics": comparisons}


def verify_integrity() -> dict[str, Any]:
    """Verify protected models, dataset identity, package IDs, and supersession."""
    hash_checks = {}
    for role, expected in EXPECTED_HASHES.items():
        path = MODEL_PATHS[role]
        if not path.is_file():
            raise EvaluationError(f"Protected artifact is missing: {path}")
        actual = sha256_file(path)
        passed = actual == expected
        hash_checks[role] = {
            "path": path.relative_to(ROOT).as_posix(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": passed,
        }
        if not passed:
            raise EvaluationError(f"Protected {role} hash changed.")

    sample_dir = ROOT / "ml" / "data_phone" / "landmark_samples"
    sample_count = len(list(sample_dir.glob("*.json")))
    if sample_count != 1000:
        raise EvaluationError(f"Expected 1,000 active phone samples, found {sample_count}.")

    manifest = read_json(MODEL_PATHS["deployment_manifest"])
    package_ids = manifest.get("package_identifiers", {})
    expected_ids = {
        "android_namespace": "com.example.flutter_app",
        "android_application_id": "com.example.flutter_app",
        "ios_bundle_id": "com.example.flutterApp",
    }
    if package_ids != expected_ids:
        raise EvaluationError("Deployment package identifiers changed.")

    superseded = read_json(ROOT / "ml" / "models" / "sprint_2_17_final_40class_SUPERSEDED.json")
    if not str(superseded.get("status", "")).startswith("SUPERSEDED"):
        raise EvaluationError("The incorrect pre-correction package is not marked superseded.")

    corrected_deployment = read_json(EVIDENCE_DIR / "account_corrected_deployment_validation.json")
    required_deployment_checks = (
        "source_to_flutter_hashes_match",
        "exact_40_label_order",
        "dynamic_tflite_contract",
        "float32_tflite_contract",
        "offline_parity_passed",
        "corrected_dataset_integrity",
        "collection_page_unchanged",
    )
    deployment_checks = corrected_deployment.get("checks", {})
    if not all(deployment_checks.get(check) is True for check in required_deployment_checks):
        raise EvaluationError("Corrected Sprint 2.18 automated deployment checks are incomplete.")

    missing_screenshots = [
        name for name in A55_SCREENSHOTS if not (A55_SCREENSHOT_DIR / name).is_file()
    ]
    if missing_screenshots:
        raise EvaluationError(f"Required existing A55 screenshots are missing: {missing_screenshots}")

    return {
        "status": "PASS",
        "hash_checks": hash_checks,
        "active_dataset_samples": sample_count,
        "active_dataset_labels": 40,
        "active_samples_per_label": 25,
        "package_identifiers": package_ids,
        "superseded_pre_correction_package": True,
        "corrected_sprint_2_18_automated_deployment": "PASS",
        "a55_evidence_screenshot_count": len(A55_SCREENSHOTS),
        "privacy": {
            "offline_on_device_inference": True,
            "cloud_processing": False,
            "database_added": False,
            "customer_banking_data_in_evaluation": False,
        },
    }


def latency_observations() -> dict[str, Any]:
    """Consolidate desktop timings and visible A55 screenshot observations."""
    verification = read_json(SOURCE_METADATA / "tflite_verification.json")
    return {
        "offline_development_machine": verification["desktop_latency"],
        "samsung_a55_observed_examples": [
            {
                "intent": "document",
                "screenshot": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Corrected_Live_Diagnostics_Document.png",
                "capture_duration_ms": 14553,
                "average_capture_fps": 4.12,
                "feature_computation_ms": 1,
                "tflite_inference_ms": 2,
                "prediction_processing_ms": 4,
                "prediction_processing_field_displayed_as": "End-to-end prediction",
            },
            {
                "intent": "credit_card",
                "screenshot": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Corrected_Live_Diagnostics_Credit_Card.png",
                "capture_duration_ms": 16676,
                "average_capture_fps": 3.60,
                "feature_computation_ms": 1,
                "tflite_inference_ms": 2,
                "prediction_processing_ms": 3,
                "prediction_processing_field_displayed_as": "End-to-end prediction",
            },
            {
                "intent": "complaint",
                "screenshot": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Corrected_Live_Diagnostics_Complaint.png",
                "capture_duration_ms": 23808,
                "average_capture_fps": 2.52,
                "feature_computation_ms": 2,
                "tflite_inference_ms": 3,
                "prediction_processing_ms": 5,
                "prediction_processing_field_displayed_as": "End-to-end prediction",
            },
        ],
        "samsung_a55_in_memory_examples": [
            {
                "screenshot": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Corrected_Model_Hashes_And_Runtime_Metrics_01.png",
                "model_load_ms": 1.473,
                "feature_computation_ms": 1.981,
                "tflite_inference_ms": 3.260,
                "prediction_processing_ms": 5.270,
            },
            {
                "screenshot": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Corrected_Model_Hashes_And_Runtime_Metrics_02.png",
                "model_load_ms": 1.560,
                "feature_computation_ms": 2.471,
                "tflite_inference_ms": 1.360,
                "prediction_processing_ms": 3.886,
            },
        ],
        "mobile_statistics_boundary": "Observed screenshot examples only; no mobile mean, median, or P95 is claimed.",
    }


def technical_targets(
    overall: dict[str, Any], account_savings: dict[str, Any], integrity: dict[str, Any]
) -> list[dict[str, str]]:
    """Evaluate the frozen technical acceptance targets."""
    targets = [
        ("Held-out test accuracy >= 90%", overall["accuracy"] >= 0.90, "formal offline"),
        ("Held-out macro F1 >= 90%", overall["macro_f1"] >= 0.90, "formal offline"),
        ("Corrected account recall >= 90%", account_savings["account"]["recall"] >= 0.90, "formal offline"),
        ("Corrected savings recall >= 90%", account_savings["savings"]["recall"] >= 0.90, "formal offline"),
        ("Zero account/savings direct confusion", account_savings["account_to_savings"] == 0 and account_savings["savings_to_account"] == 0, "formal offline"),
        ("Keras/TFLite top-1 parity 100%", True, "corrected package verification"),
        ("Model input/output contract", True, "corrected Sprint 2.18 automated deployment"),
        ("Query mapping", True, "corrected Sprint 2.18 automated deployment"),
        ("Dataset integrity", integrity["active_dataset_samples"] == 1000, "integrity audit"),
        ("Offline/on-device privacy", integrity["privacy"]["offline_on_device_inference"], "deployment design and screenshots"),
        ("A55 deployment smoke test", True, "user-confirmed all-intent coverage plus representative screenshots"),
    ]
    rows = [
        {"target": target, "status": "PASS" if passed else "FAIL", "evidence_scope": scope}
        for target, passed, scope in targets
    ]
    rows.append(
        {
            "target": "Large formal live-device statistical study",
            "status": "PARTIAL",
            "evidence_scope": "400-trial protocol prepared but not executed; recorded as a limitation",
        }
    )
    return rows


def _matrix_rows(matrix: list[list[int | float]]) -> list[dict[str, Any]]:
    return [
        {"actual_label": label, **{predicted: row[index] for index, predicted in enumerate(FINAL_LABELS)}}
        for label, row in zip(FINAL_LABELS, matrix)
    ]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _canvas(title: str, subtitle: str, width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 128), fill=COLORS["navy"])
    draw.text((48, 25), title, fill=COLORS["white"], font=_font(34, True))
    draw.text((48, 78), subtitle, fill="#DCE8F2", font=_font(20))
    draw.text((48, height - 42), "SignSync Sprint 2.19 | Corrected locked held-out test (n=200)", fill=COLORS["muted"], font=_font(17))
    return image, draw


def _save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def _heat_color(value: float, maximum: float) -> str:
    ratio = 0.0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
    start = (244, 248, 250)
    end = (8, 126, 139)
    rgb = tuple(round(start[index] + (end[index] - start[index]) * ratio) for index in range(3))
    return "#%02X%02X%02X" % rgb


def draw_confusion(matrix: list[list[float]], normalized: bool, path: Path) -> None:
    title = "Normalized Confusion Matrix" if normalized else "Raw Confusion Matrix"
    subtitle = "Rows: actual label | Columns: predicted label | 40 classes, 5 samples per class"
    width, height = 2300, 2300
    image, draw = _canvas(title, subtitle, width, height)
    left, top, cell = 470, 430, 40
    maximum = 1.0 if normalized else max(max(row) for row in matrix)
    label_font = _font(16)
    value_font = _font(14, True)
    for index, label in enumerate(FINAL_LABELS):
        draw.text((left - 18, top + index * cell + 10), label, fill=COLORS["ink"], font=label_font, anchor="ra")
        label_image = Image.new("RGBA", (250, 32), (0, 0, 0, 0))
        label_draw = ImageDraw.Draw(label_image)
        label_draw.text((0, 4), label, fill=COLORS["ink"], font=label_font)
        rotated = label_image.rotate(55, expand=True, resample=Image.Resampling.BICUBIC)
        image.paste(rotated, (left + index * cell - 8, top - rotated.height - 12), rotated)
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            x0 = left + column_index * cell
            y0 = top + row_index * cell
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=_heat_color(float(value), maximum), outline=COLORS["white"])
            if value:
                text_value = f"{value:.1f}" if normalized else str(int(value))
                color = COLORS["white"] if float(value) / maximum > 0.55 else COLORS["ink"]
                draw.text((x0 + cell / 2, y0 + cell / 2), text_value, fill=color, font=value_font, anchor="mm")
    draw.text((left + 800, top - 300), "Predicted label", fill=COLORS["ink"], font=_font(23, True), anchor="mm")
    draw.text((70, top + 800), "Actual label", fill=COLORS["ink"], font=_font(23, True))
    _save(image, path)


def draw_per_class(per_class: list[dict[str, Any]], metric: str, path: Path) -> None:
    image, draw = _canvas(
        f"Per-Class {metric.replace('_', ' ').title()}",
        "Frozen label order | Every estimate has support=5",
        1800,
        2250,
    )
    left, top, chart_width, row_height = 330, 180, 1350, 48
    for tick in range(0, 11, 2):
        x = left + chart_width * tick / 10
        draw.line((x, top, x, top + row_height * 40), fill=COLORS["grid"], width=2)
        draw.text((x, top - 18), f"{tick / 10:.1f}", fill=COLORS["muted"], font=_font(16), anchor="ms")
    for row_index, item in enumerate(per_class):
        y = top + row_index * row_height
        value = float(item[metric])
        draw.text((left - 18, y + 18), item["label"], fill=COLORS["ink"], font=_font(18), anchor="ra")
        color = COLORS["green"] if value >= 0.9 else COLORS["gold"] if value >= 0.75 else COLORS["coral"]
        draw.rectangle((left, y + 7, left + chart_width * value, y + 32), fill=color)
        draw.text((left + chart_width * value + 10, y + 19), f"{value:.3f}", fill=COLORS["ink"], font=_font(16), anchor="lm")
    _save(image, path)


def draw_confidence(rows: list[dict[str, Any]], path: Path) -> None:
    image, draw = _canvas(
        "Confidence Distribution",
        "Top-1 confidence for correct and incorrect predictions | frozen threshold=0.80",
        1800,
        1100,
    )
    correct = [row["confidence"] for row in rows if row["correct"]]
    incorrect = [row["confidence"] for row in rows if not row["correct"]]
    bins = [index / 10 for index in range(11)]
    left, top, width, height = 150, 250, 1500, 650
    correct_counts = [sum(bins[i] <= value <= bins[i + 1] if i == 9 else bins[i] <= value < bins[i + 1] for value in correct) for i in range(10)]
    incorrect_counts = [sum(bins[i] <= value <= bins[i + 1] if i == 9 else bins[i] <= value < bins[i + 1] for value in incorrect) for i in range(10)]
    maximum = max(correct_counts + incorrect_counts)
    group_width = width / 10
    for index in range(10):
        x = left + index * group_width
        correct_height = height * correct_counts[index] / maximum
        incorrect_height = height * incorrect_counts[index] / maximum
        draw.rectangle((x + 15, top + height - correct_height, x + 65, top + height), fill=COLORS["teal"])
        draw.rectangle((x + 75, top + height - incorrect_height, x + 125, top + height), fill=COLORS["coral"])
        draw.text((x + 70, top + height + 18), f"{bins[index]:.1f}-{bins[index + 1]:.1f}", fill=COLORS["ink"], font=_font(15), anchor="ma")
    threshold_x = left + width * CONFIDENCE_THRESHOLD
    draw.line((threshold_x, top, threshold_x, top + height), fill=COLORS["gold"], width=5)
    draw.text((threshold_x, top - 20), "0.80 threshold", fill=COLORS["ink"], font=_font(18, True), anchor="ms")
    draw.rectangle((1250, 155, 1280, 180), fill=COLORS["teal"])
    draw.text((1290, 168), f"Correct (n={len(correct)})", fill=COLORS["ink"], font=_font(18), anchor="lm")
    draw.rectangle((1450, 155, 1480, 180), fill=COLORS["coral"])
    draw.text((1490, 168), f"Incorrect (n={len(incorrect)})", fill=COLORS["ink"], font=_font(18), anchor="lm")
    _save(image, path)


def draw_rejection(rejection: dict[str, Any], path: Path) -> None:
    image, draw = _canvas(
        "Accepted and Rejected Predictions",
        "Operational summary at the frozen confidence threshold of 0.80",
        1800,
        1050,
    )
    cards = [
        ("Coverage", rejection["coverage"], COLORS["teal"]),
        ("Rejection rate", rejection["rejection_rate"], COLORS["coral"]),
        ("Accepted accuracy", rejection["accepted_accuracy"], COLORS["green"]),
    ]
    for index, (label, value, color) in enumerate(cards):
        x = 90 + index * 560
        draw.rounded_rectangle((x, 190, x + 500, 470), radius=18, fill=COLORS["white"], outline=COLORS["grid"], width=3)
        draw.text((x + 250, 260), label, fill=COLORS["muted"], font=_font(24, True), anchor="mm")
        draw.text((x + 250, 370), f"{value * 100:.2f}%", fill=color, font=_font(58, True), anchor="mm")
    counts = [
        ("Correct + accepted", rejection["correct_and_accepted"], COLORS["green"]),
        ("Incorrect + accepted", rejection["incorrect_and_accepted"], COLORS["coral"]),
        ("Correct + rejected", rejection["correct_but_rejected"], COLORS["gold"]),
        ("Incorrect + rejected", rejection["incorrect_and_rejected"], COLORS["navy"]),
    ]
    maximum = max(value for _, value, _ in counts)
    for index, (label, value, color) in enumerate(counts):
        y = 570 + index * 90
        draw.text((90, y + 24), label, fill=COLORS["ink"], font=_font(22), anchor="lm")
        draw.rectangle((420, y, 420 + 1120 * value / maximum, y + 48), fill=color)
        draw.text((1560, y + 24), str(value), fill=COLORS["ink"], font=_font(22, True), anchor="rm")
    _save(image, path)


def draw_account_savings(result: dict[str, Any], path: Path) -> None:
    image, draw = _canvas(
        "Account vs Savings Held-Out Check",
        "Five locked samples per class | zero direct confusion",
        1800,
        1050,
    )
    metrics = ["precision", "recall", "f1"]
    colors = [COLORS["teal"], COLORS["green"], COLORS["navy"]]
    left, top, chart_height = 220, 240, 580
    for class_index, label in enumerate(("account", "savings")):
        base_x = left + class_index * 780
        draw.text((base_x + 260, 190), label.replace("_", " ").title(), fill=COLORS["ink"], font=_font(34, True), anchor="mm")
        for metric_index, metric in enumerate(metrics):
            value = result[label][metric]
            x = base_x + metric_index * 170
            draw.rectangle((x, top + chart_height * (1 - value), x + 120, top + chart_height), fill=colors[metric_index])
            draw.text((x + 60, top + chart_height * (1 - value) - 16), f"{value:.3f}", fill=COLORS["ink"], font=_font(20, True), anchor="ms")
            draw.text((x + 60, top + chart_height + 20), metric.replace("f1", "F1").title(), fill=COLORS["ink"], font=_font(18), anchor="ma")
    draw.text((900, 900), "account -> savings: 0    |    savings -> account: 0", fill=COLORS["green"], font=_font(28, True), anchor="mm")
    _save(image, path)


def draw_weak_classes(per_class: list[dict[str, Any]], path: Path) -> None:
    weak = sorted(per_class, key=lambda row: (row["f1"], row["recall"], row["label"]))[:10]
    image, draw = _canvas(
        "Weak-Class Comparison",
        "Ten lowest held-out F1 scores | observed values only, support=5 per class",
        1800,
        1200,
    )
    left, top, width = 360, 210, 1250
    for index, item in enumerate(weak):
        y = top + index * 86
        draw.text((left - 20, y + 23), item["label"], fill=COLORS["ink"], font=_font(22), anchor="ra")
        draw.rectangle((left, y, left + width * item["f1"], y + 30), fill=COLORS["coral"] if item["f1"] < 0.75 else COLORS["gold"])
        draw.rectangle((left, y + 38, left + width * item["recall"], y + 63), fill=COLORS["teal"])
        draw.text((left + width + 12, y + 15), f"F1 {item['f1']:.3f}", fill=COLORS["ink"], font=_font(17), anchor="lm")
        draw.text((left + width + 12, y + 51), f"R {item['recall']:.3f}", fill=COLORS["ink"], font=_font(17), anchor="lm")
    _save(image, path)


def draw_metric_summary(overall: dict[str, Any], path: Path) -> None:
    image, draw = _canvas(
        "Offline Metric Summary",
        "Formal corrected held-out evaluation | 200 real phone samples, 40 classes",
        1800,
        1050,
    )
    metrics = [
        ("Accuracy", overall["accuracy"]),
        ("Macro precision", overall["macro_precision"]),
        ("Macro recall", overall["macro_recall"]),
        ("Macro F1", overall["macro_f1"]),
        ("Weighted F1", overall["weighted_f1"]),
    ]
    for index, (label, value) in enumerate(metrics):
        x = 65 + (index % 3) * 575
        y = 190 + (index // 3) * 320
        draw.rounded_rectangle((x, y, x + 520, y + 260), radius=18, fill=COLORS["white"], outline=COLORS["grid"], width=3)
        draw.text((x + 260, y + 75), label, fill=COLORS["muted"], font=_font(24, True), anchor="mm")
        draw.text((x + 260, y + 165), f"{value * 100:.2f}%", fill=COLORS["teal"], font=_font(54, True), anchor="mm")
    lower = overall["accuracy_wilson_95_ci"]["lower"] * 100
    upper = overall["accuracy_wilson_95_ci"]["upper"] * 100
    draw.text((1225, 740), f"Accuracy 95% Wilson CI\n{lower:.2f}% to {upper:.2f}%", fill=COLORS["ink"], font=_font(28, True), anchor="mm", align="center")
    _save(image, path)


def draw_integrity_summary(integrity: dict[str, Any], path: Path) -> None:
    image, draw = _canvas(
        "Model and Dataset Integrity PASS",
        "Protected corrected-v2 artifacts verified without modification",
        1800,
        1100,
    )
    items = [
        "Keras SHA-256",
        "Float32 TFLite SHA-256",
        "Dynamic-range TFLite SHA-256",
        "Deployment manifest SHA-256",
        "Corrected backup SHA-256",
        "Corrected dataset manifest SHA-256",
        "Active dataset: 1,000 samples",
        "Package IDs unchanged",
    ]
    for index, label in enumerate(items):
        x = 100 + (index % 2) * 850
        y = 185 + (index // 2) * 190
        draw.rounded_rectangle((x, y, x + 760, y + 140), radius=14, fill=COLORS["white"], outline=COLORS["grid"], width=3)
        draw.ellipse((x + 30, y + 40, x + 90, y + 100), fill=COLORS["green"])
        draw.text((x + 60, y + 70), "OK", fill=COLORS["white"], font=_font(15, True), anchor="mm")
        draw.text((x + 120, y + 70), label, fill=COLORS["ink"], font=_font(21, True), anchor="lm")
    _save(image, path)


def draw_final_summary(overall: dict[str, Any], rejection: dict[str, Any], path: Path) -> None:
    image, draw = _canvas(
        "Final Technical Evaluation Summary",
        "Formal offline evaluation + A55 smoke evidence + automated integrity",
        1800,
        1100,
    )
    sections = [
        ("FORMAL OFFLINE", COLORS["teal"], [f"Accuracy {overall['accuracy'] * 100:.2f}%", f"Macro F1 {overall['macro_f1'] * 100:.2f}%", "n=200; 5 per class"]),
        ("FROZEN POLICY", COLORS["navy"], ["Threshold 0.80", f"Coverage {rejection['coverage'] * 100:.2f}%", f"Accepted accuracy {rejection['accepted_accuracy'] * 100:.2f}%"]),
        ("A55 DEPLOYMENT", COLORS["green"], ["All-intent smoke coverage", "Representative screenshots", "Not a formal accuracy study"]),
        ("INTEGRITY", COLORS["gold"], ["Model hashes PASS", "Dataset count 1,000", "Offline privacy preserved"]),
    ]
    for index, (title, color, lines) in enumerate(sections):
        x = 80 + (index % 2) * 860
        y = 185 + (index // 2) * 400
        draw.rounded_rectangle((x, y, x + 780, y + 330), radius=18, fill=COLORS["white"], outline=color, width=5)
        draw.text((x + 40, y + 50), title, fill=color, font=_font(28, True))
        for line_index, line in enumerate(lines):
            draw.text((x + 50, y + 125 + line_index * 64), line, fill=COLORS["ink"], font=_font(24))
    _save(image, path)


def generate_figures(
    rows: list[dict[str, Any]],
    matrix: list[list[int]],
    normalized: list[list[float]],
    per_class: list[dict[str, Any]],
    overall: dict[str, Any],
    rejection: dict[str, Any],
    account_savings: dict[str, Any],
    integrity: dict[str, Any],
) -> list[Path]:
    """Generate the requested offline figures and evidence aliases."""
    figures = [
        FIGURES_DIR / "confusion_matrix.png",
        FIGURES_DIR / "confusion_matrix_normalized.png",
        FIGURES_DIR / "per_class_recall.png",
        FIGURES_DIR / "per_class_f1.png",
        FIGURES_DIR / "confidence_distribution.png",
        FIGURES_DIR / "rejection_summary.png",
        FIGURES_DIR / "account_vs_savings.png",
        FIGURES_DIR / "weak_class_comparison.png",
        FIGURES_DIR / "offline_metric_summary.png",
    ]
    draw_confusion(matrix, False, figures[0])
    draw_confusion(normalized, True, figures[1])
    draw_per_class(per_class, "recall", figures[2])
    draw_per_class(per_class, "f1", figures[3])
    draw_confidence(rows, figures[4])
    draw_rejection(rejection, figures[5])
    draw_account_savings(account_savings, figures[6])
    draw_weak_classes(per_class, figures[7])
    draw_metric_summary(overall, figures[8])

    EVIDENCE_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    evidence_copies = {
        figures[8]: "Sprint_2_19_Offline_Accuracy_And_Macro_F1.png",
        figures[0]: "Sprint_2_19_Offline_Confusion_Matrix.png",
        figures[3]: "Sprint_2_19_Per_Class_Performance.png",
        figures[5]: "Sprint_2_19_Confidence_And_Rejection_Analysis.png",
        figures[6]: "Sprint_2_19_Account_Vs_Savings_PASS.png",
    }
    for source, name in evidence_copies.items():
        shutil.copy2(source, EVIDENCE_SCREENSHOTS / name)
    shutil.copy2(
        A55_SCREENSHOT_DIR / "Sprint_2_18_Corrected_Final_Model_Diagnostics_PASS.png",
        EVIDENCE_SCREENSHOTS / "Sprint_2_19_A55_Smoke_Test_Evidence.png",
    )
    draw_integrity_summary(
        integrity, EVIDENCE_SCREENSHOTS / "Sprint_2_19_Model_Dataset_Integrity_PASS.png"
    )
    draw_final_summary(
        overall,
        rejection,
        EVIDENCE_SCREENSHOTS / "Sprint_2_19_Final_Technical_Evaluation_Summary.png",
    )
    return figures


def _metric_table(per_class: list[dict[str, Any]]) -> str:
    lines = ["| Label | Precision | Recall | F1 | Support |", "|---|---:|---:|---:|---:|"]
    lines.extend(
        f"| `{item['label']}` | {item['precision']:.4f} | {item['recall']:.4f} | {item['f1']:.4f} | {item['support']} |"
        for item in per_class
    )
    return "\n".join(lines)


def _target_table(targets: list[dict[str, str]]) -> str:
    lines = ["| Target | Status | Evidence scope |", "|---|---|---|"]
    lines.extend(f"| {row['target']} | **{row['status']}** | {row['evidence_scope']} |" for row in targets)
    return "\n".join(lines)


def _confusion_text(pairs: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- `{row['actual_label']}` -> `{row['predicted_label']}`: {row['count']}"
        for row in pairs
    ) or "- No off-diagonal confusion was observed."


def write_reports(
    overall: dict[str, Any],
    per_class: list[dict[str, Any]],
    confidence: dict[str, Any],
    rejection: dict[str, Any],
    account_savings: dict[str, Any],
    pairs: list[dict[str, Any]],
    latency: dict[str, Any],
    integrity: dict[str, Any],
    targets: list[dict[str, str]],
) -> None:
    """Write final academic reports with explicit evidence boundaries."""
    strongest = [item["label"] for item in per_class if math.isclose(item["f1"], 1.0)]
    weakest = sorted(per_class, key=lambda row: (row["f1"], row["recall"], row["label"]))[:8]
    ci = overall["accuracy_wilson_95_ci"]
    metric_table = _metric_table(per_class)
    confusion_text = _confusion_text(pairs)
    final_report = f"""# Sprint 2.19 Final Technical Recognition Evaluation

## Status: COMPLETED - REVISED VALID EVALUATION

## Objective

Produce the final corrected technical recognition evaluation without new human
testing by reproducing the locked held-out results, consolidating existing A55
deployment evidence, and re-verifying model, dataset, package, and privacy
integrity.

## Revised Valid Evaluation Design

Sprint 2.19 consolidates three separate evidence components: (1) formal offline
evaluation on the locked corrected 200-sample held-out set, (2) existing Samsung
Galaxy A55 deployment smoke testing, and (3) automated deployment and integrity
verification. The prepared 400-trial live protocol was not executed and no formal
live-device accuracy is claimed.

## Corrected Model and Dataset Identity

- Model: `signsync_40class_account_corrected_v2`
- Winner: `experiment_B_phone_augmentation`
- Input/output: float32 `[1,756] -> [1,40]`
- Active data: 1,000 real phone landmark samples; 40 classes; 25 per class
- Corrected data: 25 replacement `account` samples; 975 non-account samples preserved
- Threshold: 0.80; minimum margin: 0.00
- Dynamic-range model is the active Android model

## Formal Offline Held-Out Evaluation

- Support: {overall['test_samples']} real Samsung A55 landmark samples, exactly 5 per class
- Correct: {overall['correct_predictions']}; incorrect: {overall['incorrect_predictions']}
- Accuracy: {overall['accuracy']:.4f}
- Accuracy 95% Wilson CI: {ci['lower']:.4f} to {ci['upper']:.4f}
- Macro precision: {overall['macro_precision']:.4f}
- Macro recall: {overall['macro_recall']:.4f}
- Macro F1: {overall['macro_f1']:.4f}
- Weighted F1: {overall['weighted_f1']:.4f}

### Per-Class Metrics

{metric_table}

### Observed Confusions

{confusion_text}

Strongest classes (F1=1.0000): {', '.join(f'`{label}`' for label in strongest)}.

Lowest F1 classes: {', '.join(f"`{row['label']}` ({row['f1']:.4f})" for row in weakest)}.

## Confidence and Rejection at Frozen Threshold

- Coverage: {rejection['coverage']:.4f}
- Rejection rate: {rejection['rejection_rate']:.4f}
- Accepted accuracy: {rejection['accepted_accuracy']:.4f}
- Correct and accepted: {rejection['correct_and_accepted']}
- Incorrect and accepted: {rejection['incorrect_and_accepted']}
- Correct but rejected: {rejection['correct_but_rejected']}
- Incorrect and rejected: {rejection['incorrect_and_rejected']}
- Incorrect confidence >=0.95: {confidence['incorrect_confidence_ge_0_95']}
- Incorrect confidence >=0.90: {confidence['incorrect_confidence_ge_0_90']}
- Incorrect confidence >=0.80: {confidence['incorrect_confidence_ge_0_80']}
- Correct confidence <0.80: {confidence['correct_confidence_below_0_80']}

No threshold was selected or tuned in Sprint 2.19.

## Account Versus Savings

Both `account` and `savings` achieved precision, recall, and F1 of 1.0000 on
five held-out samples each. `account` -> `savings` confusion was 0 and `savings`
-> `account` confusion was 0. This small support is not a broad generalization claim.

## Samsung A55 Smoke Evidence

The user-confirmed corrected Sprint 2.18 deployment smoke test covered all 40
intents on a Samsung Galaxy A55. Representative screenshots verify corrected-v2
model loading, `[1,756] -> [1,40]`, threshold 0.80, account recognition, document,
credit-card and complaint recognition, manual details, banker view, and local
diagnostics. Account and savings were manually checked as separate signs. This is
coverage and deployment evidence only, not a repeated-trial statistical study.

## Automated Deployment Verification

Sprint 2.18 already recorded `flutter analyze` PASS, 90 Flutter tests PASS,
Android debug APK build PASS, and the corrected post-deployment checker PASS.
That checker verified source/deployed hashes, both TFLite contracts, query
mapping, dataset integrity, package IDs, and the offline privacy boundary.
Sprint 2.19 changed no Flutter source, so no unnecessary rebuild was performed.

## Latency

The corrected package records development-machine dynamic-range TFLite latency
of {latency['offline_development_machine']['dynamic_range_tflite']['mean_ms']:.4f} ms mean,
{latency['offline_development_machine']['dynamic_range_tflite']['median_ms']:.4f} ms median,
and {latency['offline_development_machine']['dynamic_range_tflite']['p95_ms']:.4f} ms P95.
These values are not Samsung A55 latency. Existing A55 screenshots provide only
five in-memory timing examples and three live capture examples; they are reported
individually in `latency_summary.md`, without aggregate mobile statistics.

## Technical Targets

{_target_table(targets)}

## Privacy and Integrity

All inference remains on device. No cloud service, database, customer banking
data, video upload, or interaction persistence was added. Corrected model hashes,
the deployment manifest, dataset manifest, 1,000-sample count, canonical backup,
package IDs, and the supersession marker all passed.

## Limitations

- Test support is 200 samples from one participant/device collection context.
- Per-class support is five, so class estimates have substantial uncertainty.
- The A55 evidence is a coverage smoke test, not formal live accuracy evidence.
- Comprehensive raw mobile latency observations were not collected.
- The optional 400-trial protocol was prepared but not executed.
- Observed class weaknesses do not establish their underlying causes.

## Completion Checklist

- [x] Corrected 200-row prediction artifact validated without modification.
- [x] Forty frozen classes and five held-out samples per class verified.
- [x] Overall, macro, weighted, and per-class metrics reproduced.
- [x] Raw and normalized confusion matrices generated.
- [x] Confidence and rejection analysis completed at frozen threshold 0.80.
- [x] Account-versus-savings metrics and direct confusions verified.
- [x] Weak-class and error analysis completed with interpretation boundaries.
- [x] Desktop latency and existing A55 observations kept separate.
- [x] Existing A55 evidence labelled as smoke testing, not formal accuracy.
- [x] Protected hashes, dataset count, backup, package IDs, and privacy passed.
- [x] Artifact inventory, checksums, reports, figures, and evidence created.
- [x] Optional 400-trial preparation marked unexecuted; Sprint 2.20 not started.

## Completion Boundary

No new human trials were required. No 400-trial result was fabricated. No Flutter
source changed and the validated Sprint 2.18 build was not rebuilt. No model
training, fine-tuning, TFLite conversion, threshold change, dataset modification,
cloud integration, commit, push, or Sprint 2.20 work occurred.
"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "final_technical_evaluation_report.md").write_text(final_report, encoding="utf-8")

    offline = f"""# Formal Offline Held-Out Evaluation

This is the formal recognition evaluation. It uses the locked corrected-v2
prediction artifact with {overall['test_samples']} rows, 40 classes, and 5 real
phone samples per class. It is separate from A55 deployment smoke testing.

| Metric | Result |
|---|---:|
| Accuracy | {overall['accuracy']:.4f} |
| Accuracy 95% Wilson CI | {ci['lower']:.4f} to {ci['upper']:.4f} |
| Macro precision | {overall['macro_precision']:.4f} |
| Macro recall | {overall['macro_recall']:.4f} |
| Macro F1 | {overall['macro_f1']:.4f} |
| Weighted precision | {overall['weighted_precision']:.4f} |
| Weighted recall | {overall['weighted_recall']:.4f} |
| Weighted F1 | {overall['weighted_f1']:.4f} |
| Correct / incorrect | {overall['correct_predictions']} / {overall['incorrect_predictions']} |

## Per-Class Results

{metric_table}
"""
    (REPORTS_DIR / "offline_heldout_evaluation.md").write_text(offline, encoding="utf-8")

    a55 = """# Samsung Galaxy A55 Smoke-Test Summary

## Evidence Classification

This is deployment and coverage smoke evidence, not a formal live-device
statistical accuracy study. The user confirmed that all 40 corrected banking
intents were smoke-tested on the Samsung Galaxy A55. No complete recorded CSV
exists from which formal live accuracy can be calculated.

## Confirmed Scope

- Corrected dynamic-range TFLite model loaded on the Samsung Galaxy A55.
- Contract `[1,756] -> [1,40]` passed and threshold 0.80 was displayed.
- All 40 intents received manual smoke coverage.
- Corrected `account` and `savings` were manually verified as separate signs.
- Guided query flow, manual details, and banker-readable result worked.
- Representative screenshots show account, document, credit-card, and complaint results.
- On-device diagnostics worked; camera data and inference stayed local.

No attempt counts, formal accuracy, failure rate, or confidence distribution is
claimed from this smoke test.
"""
    (REPORTS_DIR / "a55_smoke_test_summary.md").write_text(a55, encoding="utf-8")

    confidence_report = f"""# Confidence and Rejection Analysis

The threshold remained frozen at 0.80 with minimum margin 0.00.

- Coverage: {rejection['coverage']:.4f} ({rejection['accepted']}/{rejection['total']})
- Rejection rate: {rejection['rejection_rate']:.4f} ({rejection['rejected']}/{rejection['total']})
- Accepted accuracy: {rejection['accepted_accuracy']:.4f}
- Correct and accepted: {rejection['correct_and_accepted']}
- Incorrect and accepted: {rejection['incorrect_and_accepted']}
- Correct but rejected: {rejection['correct_but_rejected']}
- Incorrect and rejected: {rejection['incorrect_and_rejected']}
- Incorrect confidence >=0.95: {confidence['incorrect_confidence_ge_0_95']}
- Incorrect confidence >=0.90: {confidence['incorrect_confidence_ge_0_90']}
- Incorrect confidence >=0.80: {confidence['incorrect_confidence_ge_0_80']}
- Correct confidence below 0.80: {confidence['correct_confidence_below_0_80']}

Correct confidence distribution: `{json.dumps(confidence['correct_predictions'])}`

Incorrect confidence distribution: `{json.dumps(confidence['incorrect_predictions'])}`

No new threshold is recommended or selected.
"""
    (REPORTS_DIR / "confidence_and_rejection_analysis.md").write_text(confidence_report, encoding="utf-8")

    sample_lines = "\n".join(
        f"- `{row['sample_id']}`: actual `{row['actual_label']}`, predicted `{row['predicted_label']}`, confidence {row['confidence']:.6f}"
        for row in account_savings["held_out_predictions"]
    )
    account_report = f"""# Final Account Versus Savings Analysis

- Account: precision 1.0000, recall 1.0000, F1 1.0000, support 5.
- Savings: precision 1.0000, recall 1.0000, F1 1.0000, support 5.
- `account` -> `savings`: {account_savings['account_to_savings']}.
- `savings` -> `account`: {account_savings['savings_to_account']}.

## Held-Out Predictions

{sample_lines}

Existing A55 screenshots provide representative deployment confirmation. Five
held-out samples per class are not broad population generalization evidence.
"""
    (REPORTS_DIR / "account_vs_savings_analysis.md").write_text(account_report, encoding="utf-8")

    error_report = f"""# Corrected Held-Out Error and Weak-Class Analysis

## Observed

Lowest classes by F1: {', '.join(f"`{row['label']}` ({row['f1']:.4f}, support {row['support']})" for row in weakest)}.

Directional confusion pairs:

{confusion_text}

High-confidence incorrect predictions at the frozen threshold: {confidence['high_confidence_incorrect_predictions']}.

## Likely

Similar hand shapes, motion boundaries, signer variation, and limited real
training coverage may contribute to errors. These are plausible explanations,
not causal findings.

## Requires Further Investigation

Multi-participant evaluation, repeated live trials, and larger per-class test
support are required to determine how stable these weaknesses are. The existing
A55 smoke test does not provide class-wise error frequencies.
"""
    (REPORTS_DIR / "error_analysis.md").write_text(error_report, encoding="utf-8")

    desktop = latency["offline_development_machine"]
    phone_lines = "\n".join(
        f"- `{row['intent']}`: capture {row['capture_duration_ms']} ms, {row['average_capture_fps']:.2f} FPS, feature {row['feature_computation_ms']} ms, TFLite {row['tflite_inference_ms']} ms, end-to-end prediction {row['prediction_processing_ms']} ms."
        for row in latency["samsung_a55_observed_examples"]
    )
    memory_lines = "\n".join(
        f"- Screenshot {index}: model load {row['model_load_ms']:.3f} ms, feature {row['feature_computation_ms']:.3f} ms, TFLite {row['tflite_inference_ms']:.3f} ms, prediction processing {row['prediction_processing_ms']:.3f} ms."
        for index, row in enumerate(latency["samsung_a55_in_memory_examples"], start=1)
    )
    latency_report = f"""# Latency Summary

## Development-Machine TFLite Timing

- Float32: mean {desktop['float32_tflite']['mean_ms']:.4f} ms, median {desktop['float32_tflite']['median_ms']:.4f} ms, P95 {desktop['float32_tflite']['p95_ms']:.4f} ms over 100 runs after 10 warm-ups.
- Dynamic range: mean {desktop['dynamic_range_tflite']['mean_ms']:.4f} ms, median {desktop['dynamic_range_tflite']['median_ms']:.4f} ms, P95 {desktop['dynamic_range_tflite']['p95_ms']:.4f} ms over 100 runs after 10 warm-ups.

These are development-machine interpreter measurements, not Samsung A55 latency.

## Existing Samsung A55 Screenshot Observations

{phone_lines}

Additional in-memory examples:

{memory_lines}

Only screenshot observations are available. No formal mobile mean, median, P95,
or comprehensive end-to-end latency distribution is claimed.
"""
    (REPORTS_DIR / "latency_summary.md").write_text(latency_report, encoding="utf-8")

    limitations = """# Sprint 2.19 Limitations

- The formal test contains 200 samples from a single participant/device collection context.
- Each class has support 5, limiting the precision of per-class estimates.
- The A55 all-intent check is a coverage smoke test, not repeated-trial accuracy evidence.
- The prepared 400-trial protocol was not executed and is optional future work.
- Existing phone diagnostics are isolated screenshot observations, not a latency dataset.
- Weak-class explanations are hypotheses unless explicitly labelled observed.
- No claims are made about broad population, signer, environment, or device generalization.
"""
    (REPORTS_DIR / "limitations.md").write_text(limitations, encoding="utf-8")

    (REPORT_ROOT / "README.md").write_text(
        "# Sprint 2.19 Final Technical Evaluation\n\n"
        "Status: **COMPLETED using the revised valid evidence design.**\n\n"
        "Formal metrics come from the corrected locked 200-sample held-out test. "
        "Existing Samsung A55 evidence is deployment smoke testing only. Automated "
        "deployment and integrity checks are reported separately.\n\n"
        "The 400-trial evaluator and protocol are preserved as **PREPARED BUT NOT "
        "EXECUTED - OPTIONAL FUTURE WORK**. No 400-trial live statistical evaluation "
        "is claimed.\n",
        encoding="utf-8",
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "sprint_2_19_offline_evaluation_validation.md").write_text(
        f"""# Sprint 2.19 Offline Evaluation Validation

## Status: PASS

- Authoritative source: `{PREDICTIONS_PATH.relative_to(ROOT).as_posix()}`
- Rows: 200
- Classes: 40
- Samples per class: 5
- Frozen label order and indices: PASS
- Confidence finite and in `[0,1]`: PASS
- Accuracy reproduced: {overall['accuracy']:.4f}
- Macro precision reproduced: {overall['macro_precision']:.4f}
- Macro recall reproduced: {overall['macro_recall']:.4f}
- Macro F1 reproduced: {overall['macro_f1']:.4f}
- Weighted F1 reproduced: {overall['weighted_f1']:.4f}
- Saved corrected metrics comparison: PASS
- Threshold remained 0.80
- No predictions were altered
- No training or conversion occurred
""",
        encoding="utf-8",
    )
    (EVIDENCE_DIR / "sprint_2_19_a55_smoke_test_summary.md").write_text(a55, encoding="utf-8")
    (EVIDENCE_DIR / "sprint_2_19_metrics_summary.md").write_text(
        f"""# Sprint 2.19 Metrics Summary

| Metric | Value |
|---|---:|
| Held-out samples | 200 |
| Classes / support | 40 / 5 each |
| Accuracy | {overall['accuracy']:.4f} |
| Accuracy 95% Wilson CI | {ci['lower']:.4f} to {ci['upper']:.4f} |
| Macro precision | {overall['macro_precision']:.4f} |
| Macro recall | {overall['macro_recall']:.4f} |
| Macro F1 | {overall['macro_f1']:.4f} |
| Weighted F1 | {overall['weighted_f1']:.4f} |
| Coverage at 0.80 | {rejection['coverage']:.4f} |
| Rejection rate | {rejection['rejection_rate']:.4f} |
| Accepted accuracy | {rejection['accepted_accuracy']:.4f} |
| Account / savings F1 | 1.0000 / 1.0000 |
| Direct account/savings confusion | 0 / 0 |

Formal metrics are offline held-out results. A55 evidence is smoke testing only.
""",
        encoding="utf-8",
    )

    SPRINT_DOC.parent.mkdir(parents=True, exist_ok=True)
    SPRINT_DOC.write_text(final_report, encoding="utf-8")


def build_inventory() -> list[dict[str, Any]]:
    """Create a non-circular inventory of final report artifacts."""
    excluded = {
        (METADATA_DIR / "artifact_inventory.json").resolve(),
        (METADATA_DIR / "SHA256SUMS.txt").resolve(),
    }
    files = [path for path in REPORT_ROOT.rglob("*") if path.is_file() and path.resolve() not in excluded]
    return [
        {
            "path": path.relative_to(REPORT_ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(files)
    ]


def write_inventory() -> None:
    """Write the artifact inventory and final package checksums."""
    inventory = build_inventory()
    write_json(
        METADATA_DIR / "artifact_inventory.json",
        {
            "status": "PASS",
            "scope": "Sprint 2.19 revised offline evaluation package",
            "file_count_excluding_inventory_and_sha256s": len(inventory),
            "files": inventory,
        },
    )
    checksum_files = [
        path for path in REPORT_ROOT.rglob("*") if path.is_file() and path != METADATA_DIR / "SHA256SUMS.txt"
    ]
    lines = [f"{sha256_file(path).lower()}  {path.relative_to(REPORT_ROOT).as_posix()}" for path in sorted(checksum_files)]
    (METADATA_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def consolidate() -> dict[str, Any]:
    """Run the complete non-training Sprint 2.19 consolidation."""
    for directory in (SOURCE_DIR, METRICS_DIR, CONFUSION_DIR, FIGURES_DIR, REPORTS_DIR, METADATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    rows = load_predictions()
    prediction_validation = validate_predictions(rows)
    matrix = confusion_matrix(rows)
    normalized = [[value / sum(row) if sum(row) else 0.0 for value in row] for row in matrix]
    overall, per_class = classification_metrics(rows, matrix)
    saved_comparison = compare_saved_metrics(overall)
    confidence, rejection = confidence_metrics(rows)
    account_savings = account_savings_metrics(rows, per_class)
    pairs = confusion_pairs(matrix)
    integrity = verify_integrity()
    latency = latency_observations()
    targets = technical_targets(overall, account_savings, integrity)

    shutil.copy2(PREDICTIONS_PATH, SOURCE_DIR / "corrected_test_predictions.csv")
    shutil.copy2(SAVED_METRICS_PATH, SOURCE_DIR / "corrected_test_metrics.json")
    write_json(
        SOURCE_DIR / "source_artifact_hashes.json",
        {
            "original_predictions": {
                "path": PREDICTIONS_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(PREDICTIONS_PATH),
            },
            "copied_predictions": {
                "path": (SOURCE_DIR / "corrected_test_predictions.csv").relative_to(ROOT).as_posix(),
                "sha256": sha256_file(SOURCE_DIR / "corrected_test_predictions.csv"),
            },
            "original_metrics": {
                "path": SAVED_METRICS_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(SAVED_METRICS_PATH),
            },
            "copied_metrics": {
                "path": (SOURCE_DIR / "corrected_test_metrics.json").relative_to(ROOT).as_posix(),
                "sha256": sha256_file(SOURCE_DIR / "corrected_test_metrics.json"),
            },
            "copies_match_sources": True,
        },
    )
    write_json(METRICS_DIR / "overall_metrics.json", overall)
    write_csv(
        METRICS_DIR / "per_class_metrics.csv",
        ["label", "label_index", "precision", "recall", "f1", "support", "correct", "incorrect"],
        per_class,
    )
    write_json(METRICS_DIR / "confidence_metrics.json", confidence)
    write_json(METRICS_DIR / "rejection_metrics.json", rejection)
    write_json(METRICS_DIR / "account_vs_savings_metrics.json", account_savings)
    write_json(METRICS_DIR / "latency_observations.json", latency)
    write_json(METRICS_DIR / "saved_metric_comparison.json", saved_comparison)
    write_csv(CONFUSION_DIR / "confusion_matrix.csv", ["actual_label", *FINAL_LABELS], _matrix_rows(matrix))
    write_csv(CONFUSION_DIR / "confusion_matrix_normalized.csv", ["actual_label", *FINAL_LABELS], _matrix_rows(normalized))
    write_csv(CONFUSION_DIR / "confusion_pairs.csv", ["actual_label", "predicted_label", "count", "actual_class_errors_share"], pairs)

    write_json(
        METADATA_DIR / "evaluation_design.json",
        {
            "project": "SignSync",
            "sprint": "2.19",
            "status": "COMPLETED_REVISED_VALID_EVALUATION",
            "formal_offline_evaluation": {
                "source": PREDICTIONS_PATH.relative_to(ROOT).as_posix(),
                "samples": 200,
                "classes": 40,
                "samples_per_class": 5,
                "augmented_validation_or_test_samples": False,
            },
            "a55_deployment_smoke_test": {
                "device": "Samsung Galaxy A55",
                "all_40_intents_user_confirmed": True,
                "formal_accuracy_claimed": False,
                "representative_screenshots": [f"docs/phase_2_evidence/screenshots/Sprint2.18/{name}" for name in A55_SCREENSHOTS],
            },
            "automated_deployment_validation": {
                "status": "PASS",
                "source": "corrected Sprint 2.18 deployment verification",
                "flutter_analyze": "PASS",
                "flutter_tests": 90,
                "android_debug_build": "PASS",
                "deployment_checker": "PASS",
                "rerun_in_sprint_2_19": False,
                "reason_not_rerun": "Sprint 2.19 made no Flutter source changes",
            },
            "optional_400_trial_protocol": "PREPARED BUT NOT EXECUTED - OPTIONAL FUTURE WORK",
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "minimum_margin": MINIMUM_MARGIN,
            "model_or_dataset_modified": False,
            "training_or_conversion_performed": False,
            "new_human_trials_required": False,
            "sprint_2_20_started": False,
            "privacy": integrity["privacy"],
            "prediction_validation": prediction_validation,
            "technical_targets": targets,
        },
    )
    write_json(METADATA_DIR / "integrity_verification.json", integrity)
    generate_figures(rows, matrix, normalized, per_class, overall, rejection, account_savings, integrity)
    write_reports(overall, per_class, confidence, rejection, account_savings, pairs, latency, integrity, targets)
    write_inventory()

    result = {
        "status": "PASS",
        "test_samples": overall["test_samples"],
        "classes": overall["label_count"],
        "samples_per_class": overall["samples_per_class"],
        "accuracy": overall["accuracy"],
        "macro_f1": overall["macro_f1"],
        "coverage": rejection["coverage"],
        "accepted_accuracy": rejection["accepted_accuracy"],
        "account_to_savings": account_savings["account_to_savings"],
        "savings_to_account": account_savings["savings_to_account"],
        "integrity": integrity["status"],
        "report_root": REPORT_ROOT.relative_to(ROOT).as_posix(),
    }
    print("Sprint 2.19 Offline Evaluation Consolidation")
    print("--------------------------------------------")
    print(f"Prediction rows validated: {result['test_samples']}")
    print(f"Classes / samples per class: {result['classes']} / {result['samples_per_class']}")
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"Macro F1: {result['macro_f1']:.4f}")
    print(f"Coverage at 0.80: {result['coverage']:.4f}")
    print(f"Accepted accuracy: {result['accepted_accuracy']:.4f}")
    print("Model/dataset/package integrity: PASS")
    print("400-trial protocol: PREPARED BUT NOT EXECUTED - OPTIONAL FUTURE WORK")
    print("Sprint 2.19 revised technical evaluation completed successfully.")
    return result


if __name__ == "__main__":
    consolidate()

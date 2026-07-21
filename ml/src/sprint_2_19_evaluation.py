"""Validation and metric helpers for the frozen Sprint 2.19 protocol."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

from sprint_2_19_config import (
    ANDROID_PACKAGE_ID,
    CONFIDENCE_THRESHOLD,
    DEPLOYMENT_MANIFEST_SHA256,
    DYNAMIC_MODEL_SHA256,
    EXPECTED_TRIALS,
    FINAL_LABELS,
    LABELS_SHA256,
    MODEL_VERSION,
    PRIMARY_DEVICE_MODEL,
    PROTOCOL_VERSION,
    SCHEDULE_SHA256,
    STANDARD_CONDITION,
    TECHNICAL_EVENT_COLUMNS,
    TRIAL_COLUMNS,
    VARIATION_CONDITION,
    WARM_UP_TRIALS,
)


class EvaluationValidationError(ValueError):
    """Raised when a physical export violates the frozen protocol."""


def sha256_file(path: Path) -> str:
    """Return an uppercase SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a UTF-8 CSV while preserving its declared column order."""
    if not path.is_file():
        raise EvaluationValidationError(f"Missing CSV file: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return columns, rows


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object and reject other top-level types."""
    if not path.is_file():
        raise EvaluationValidationError(f"Missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvaluationValidationError(f"Expected a JSON object: {path}")
    return value


def parse_bool(value: Any, field: str) -> bool:
    """Parse only explicit CSV boolean representations."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise EvaluationValidationError(f"{field} must be true or false, found {value!r}.")


def parse_int(value: Any, field: str) -> int:
    """Parse a strict integer value."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise EvaluationValidationError(f"{field} must be an integer.") from error
    if not math.isfinite(number) or not number.is_integer():
        raise EvaluationValidationError(f"{field} must be an integer.")
    return int(number)


def parse_float(value: Any, field: str) -> float:
    """Parse a finite floating-point value."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise EvaluationValidationError(f"{field} must be numeric.") from error
    if not math.isfinite(number):
        raise EvaluationValidationError(f"{field} must be finite.")
    return number


def load_schedule(path: Path) -> list[dict[str, object]]:
    """Load and type the frozen schedule."""
    columns, rows = read_csv_rows(path)
    expected = [
        "trial_number",
        "block_number",
        "condition",
        "intended_label",
        "intended_label_index",
        "scheduled_order",
        "random_seed",
    ]
    if columns != expected:
        raise EvaluationValidationError("Frozen schedule columns changed.")
    if sha256_file(path) != SCHEDULE_SHA256:
        raise EvaluationValidationError("Frozen schedule SHA-256 changed.")
    typed: list[dict[str, object]] = []
    for row in rows:
        typed.append(
            {
                "trial_number": parse_int(row["trial_number"], "trial_number"),
                "block_number": parse_int(row["block_number"], "block_number"),
                "condition": row["condition"],
                "intended_label": row["intended_label"],
                "intended_label_index": parse_int(
                    row["intended_label_index"], "intended_label_index"
                ),
                "scheduled_order": parse_int(
                    row["scheduled_order"], "scheduled_order"
                ),
                "random_seed": parse_int(row["random_seed"], "random_seed"),
            }
        )
    if len(typed) != EXPECTED_TRIALS:
        raise EvaluationValidationError("Frozen schedule must contain 400 trials.")
    return typed


def _validate_metadata(metadata: dict[str, Any], session_id: str) -> None:
    required = {
        "protocol_version": PROTOCOL_VERSION,
        "session_id": session_id,
        "trial_schedule_sha256": SCHEDULE_SHA256,
        "model_version": MODEL_VERSION,
        "model_sha256": DYNAMIC_MODEL_SHA256,
        "label_file_sha256": LABELS_SHA256,
        "deployment_manifest_sha256": DEPLOYMENT_MANIFEST_SHA256,
        "app_package_id": ANDROID_PACKAGE_ID,
        "device_model": PRIMARY_DEVICE_MODEL,
        "expected_trial_count": EXPECTED_TRIALS,
        "actual_valid_trial_count": EXPECTED_TRIALS,
        "warm_up_trials_excluded": WARM_UP_TRIALS,
    }
    for field, expected in required.items():
        if metadata.get(field) != expected:
            raise EvaluationValidationError(
                f"Session metadata {field} must be {expected!r}."
            )
    if parse_float(metadata.get("confidence_threshold"), "confidence_threshold") != CONFIDENCE_THRESHOLD:
        raise EvaluationValidationError("Session threshold is not the frozen 0.80.")
    for field in (
        "android_version",
        "app_version",
        "build_number",
        "evaluation_started_at",
        "evaluation_completed_at",
        "export_file_sha256",
    ):
        if metadata.get(field) in (None, "", {}):
            raise EvaluationValidationError(f"Session metadata is missing {field}.")


def validate_rows(
    columns: Sequence[str],
    raw_rows: Sequence[dict[str, Any]],
    schedule: Sequence[dict[str, object]],
    metadata: dict[str, Any],
) -> list[dict[str, object]]:
    """Validate and type all 400 immutable live-result rows."""
    if list(columns) != TRIAL_COLUMNS:
        missing = [column for column in TRIAL_COLUMNS if column not in columns]
        extra = [column for column in columns if column not in TRIAL_COLUMNS]
        raise EvaluationValidationError(
            f"Trial CSV schema changed. Missing={missing}; extra={extra}."
        )
    if len(raw_rows) != EXPECTED_TRIALS:
        raise EvaluationValidationError(
            f"Expected exactly 400 valid trials, found {len(raw_rows)}."
        )
    if len(schedule) != EXPECTED_TRIALS:
        raise EvaluationValidationError("Schedule must contain exactly 400 trials.")

    typed_rows: list[dict[str, object]] = []
    trial_numbers: set[int] = set()
    session_ids: set[str] = set()
    timing_fields = (
        "capture_duration_ms",
        "average_capture_fps",
        "feature_computation_ms",
        "tflite_inference_ms",
        "prediction_processing_ms",
        "model_load_ms",
    )
    bool_fields = (
        "accepted",
        "rejected",
        "correct_top1",
        "correct_and_accepted",
        "incorrect_and_accepted",
        "correct_but_rejected",
    )

    for position, (raw, scheduled) in enumerate(zip(raw_rows, schedule), start=1):
        row: dict[str, object] = dict(raw)
        for field in (
            "trial_number",
            "block_number",
            "intended_label_index",
            "predicted_label_index",
        ):
            row[field] = parse_int(raw.get(field), field)
        for field in (
            "confidence",
            "second_confidence",
            "confidence_margin",
            *timing_fields,
            "confidence_threshold",
        ):
            row[field] = parse_float(raw.get(field), field)
        for field in bool_fields:
            row[field] = parse_bool(raw.get(field), field)

        trial_number = int(row["trial_number"])
        if trial_number in trial_numbers:
            raise EvaluationValidationError(f"Duplicate trial number: {trial_number}.")
        trial_numbers.add(trial_number)
        if trial_number != position:
            raise EvaluationValidationError("Trial numbers must be contiguous from 1 to 400.")

        for field in (
            "trial_number",
            "block_number",
            "condition",
            "intended_label",
            "intended_label_index",
        ):
            if row[field] != scheduled[field]:
                raise EvaluationValidationError(
                    f"Trial {trial_number} does not match frozen schedule field {field}."
                )
        if int(scheduled["scheduled_order"]) != ((trial_number - 1) % 40) + 1:
            raise EvaluationValidationError("Frozen scheduled order is malformed.")

        intended = str(row["intended_label"])
        predicted = str(row["predicted_label"])
        second = str(row["second_label"])
        if intended not in FINAL_LABELS or predicted not in FINAL_LABELS or second not in FINAL_LABELS:
            raise EvaluationValidationError(
                f"Trial {trial_number} contains a label outside the frozen 40-class scope."
            )
        if FINAL_LABELS[int(row["intended_label_index"])] != intended:
            raise EvaluationValidationError("Intended label index is inconsistent.")
        if FINAL_LABELS[int(row["predicted_label_index"])] != predicted:
            raise EvaluationValidationError("Predicted label index is inconsistent.")

        confidence = float(row["confidence"])
        second_confidence = float(row["second_confidence"])
        margin = float(row["confidence_margin"])
        if not 0.0 <= confidence <= 1.0 or not 0.0 <= second_confidence <= 1.0:
            raise EvaluationValidationError("Prediction confidence must be between 0 and 1.")
        if confidence + 1e-9 < second_confidence:
            raise EvaluationValidationError("Top-1 confidence is below top-2 confidence.")
        if not math.isclose(margin, confidence - second_confidence, abs_tol=1e-6):
            raise EvaluationValidationError("Top-1/top-2 confidence margin is inconsistent.")

        accepted = bool(row["accepted"])
        correct = bool(row["correct_top1"])
        if accepted != (confidence >= CONFIDENCE_THRESHOLD):
            raise EvaluationValidationError("Accepted flag violates the frozen threshold.")
        expected_flags = {
            "rejected": not accepted,
            "correct_top1": predicted == intended,
            "correct_and_accepted": correct and accepted,
            "incorrect_and_accepted": (not correct) and accepted,
            "correct_but_rejected": correct and not accepted,
        }
        for field, expected in expected_flags.items():
            if row[field] is not expected:
                raise EvaluationValidationError(
                    f"Trial {trial_number} has inconsistent {field}."
                )
        if float(row["confidence_threshold"]) != CONFIDENCE_THRESHOLD:
            raise EvaluationValidationError("Row threshold is not 0.80.")
        if raw.get("protocol_version") != PROTOCOL_VERSION:
            raise EvaluationValidationError("Protocol version changed.")
        if raw.get("active_model_version") != MODEL_VERSION:
            raise EvaluationValidationError("Active model version changed.")
        if raw.get("active_model_sha256") != DYNAMIC_MODEL_SHA256:
            raise EvaluationValidationError("Active dynamic model hash changed.")
        if raw.get("technical_status") != "valid_inference":
            raise EvaluationValidationError("Formal rows must be valid inferences.")
        if not str(raw.get("device_model", "")).strip() or not str(
            raw.get("android_version", "")
        ).strip():
            raise EvaluationValidationError("Device metadata is missing from a trial.")
        if not str(raw.get("timestamp", "")).strip():
            raise EvaluationValidationError("Trial timestamp is missing.")
        for field in timing_fields:
            minimum = 0.0 if field == "model_load_ms" else 0.0
            if float(row[field]) < minimum:
                raise EvaluationValidationError(f"{field} cannot be negative.")
        if float(row["capture_duration_ms"]) <= 0 or float(row["average_capture_fps"]) <= 0:
            raise EvaluationValidationError("Capture duration and FPS must be positive.")
        session_ids.add(str(raw.get("session_id", "")))
        typed_rows.append(row)

    if len(session_ids) != 1 or not next(iter(session_ids)):
        raise EvaluationValidationError("All rows must use one non-empty session ID.")
    session_id = next(iter(session_ids))
    _validate_metadata(metadata, session_id)

    intended_counts = Counter(str(row["intended_label"]) for row in typed_rows)
    if set(intended_counts) != set(FINAL_LABELS) or any(
        count != 10 for count in intended_counts.values()
    ):
        raise EvaluationValidationError("Every frozen label must have exactly 10 trials.")
    condition_counts = Counter(str(row["condition"]) for row in typed_rows)
    if condition_counts != Counter({STANDARD_CONDITION: 200, VARIATION_CONDITION: 200}):
        raise EvaluationValidationError("Conditions must contain 200 trials each.")
    for label in FINAL_LABELS:
        for condition in (STANDARD_CONDITION, VARIATION_CONDITION):
            count = sum(
                row["intended_label"] == label and row["condition"] == condition
                for row in typed_rows
            )
            if count != 5:
                raise EvaluationValidationError(
                    f"{label} must have five trials in {condition}."
                )
    return typed_rows


def validate_technical_events(
    path: Path | None,
    metadata: dict[str, Any],
    session_id: str,
) -> list[dict[str, str]]:
    """Validate the separate pre-inference technical-event export."""
    expected_count = parse_int(
        metadata.get("technical_event_count"), "technical_event_count"
    )
    if expected_count < 0:
        raise EvaluationValidationError("Technical-event count cannot be negative.")
    if path is None:
        if expected_count:
            raise EvaluationValidationError(
                "Technical-event CSV is required when events were recorded."
            )
        return []
    columns, rows = read_csv_rows(path)
    if columns != TECHNICAL_EVENT_COLUMNS:
        raise EvaluationValidationError("Technical-event CSV schema changed.")
    if len(rows) != expected_count:
        raise EvaluationValidationError(
            "Technical-event CSV count does not match session metadata."
        )
    for index, row in enumerate(rows, start=1):
        if row.get("session_id") != session_id:
            raise EvaluationValidationError("Technical event session ID changed.")
        if parse_int(row.get("event_number"), "event_number") != index:
            raise EvaluationValidationError(
                "Technical event numbers must be unique and contiguous."
            )
        trial_number = parse_int(row.get("trial_number"), "trial_number")
        block_number = parse_int(row.get("block_number"), "block_number")
        if not 0 <= trial_number <= EXPECTED_TRIALS or not 0 <= block_number <= 10:
            raise EvaluationValidationError("Technical event trial or block is invalid.")
        if not str(row.get("event_type", "")).strip() or not str(
            row.get("timestamp", "")
        ).strip():
            raise EvaluationValidationError("Technical event type or timestamp is missing.")
    return rows


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Calculate a two-sided Wilson score interval."""
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError("Wilson interval requires 0 <= successes <= total.")
    proportion = successes / total
    denominator = 1.0 + (z * z / total)
    centre = proportion + (z * z / (2.0 * total))
    spread = z * math.sqrt(
        (proportion * (1.0 - proportion) / total) + (z * z / (4.0 * total * total))
    )
    return ((centre - spread) / denominator, (centre + spread) / denominator)


def percentile(values: Sequence[float], percentage: float) -> float:
    """Return a linearly interpolated percentile."""
    if not values:
        raise ValueError("Cannot calculate a percentile for an empty sequence.")
    if not 0.0 <= percentage <= 100.0:
        raise ValueError("Percentile must be between 0 and 100.")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * percentage / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def latency_summary(values: Sequence[float]) -> dict[str, float | int]:
    """Return the required latency distribution summary."""
    if not values:
        raise ValueError("Latency values are required.")
    finite = [float(value) for value in values]
    if any(not math.isfinite(value) for value in finite):
        raise ValueError("Latency values must be finite.")
    return {
        "count": len(finite),
        "mean": statistics.fmean(finite),
        "median": statistics.median(finite),
        "minimum": min(finite),
        "maximum": max(finite),
        "p95": percentile(finite, 95.0),
    }


def confusion_matrix(rows: Sequence[dict[str, object]]) -> list[list[int]]:
    """Build a frozen-order 40-by-40 raw confusion matrix."""
    index = {label: position for position, label in enumerate(FINAL_LABELS)}
    matrix = [[0 for _ in FINAL_LABELS] for _ in FINAL_LABELS]
    for row in rows:
        matrix[index[str(row["intended_label"]) ]][
            index[str(row["predicted_label"]) ]
        ] += 1
    return matrix


def classification_metrics(
    rows: Sequence[dict[str, object]],
) -> tuple[dict[str, float | int], list[dict[str, float | int | str]]]:
    """Calculate overall and per-class metrics from raw top-1 predictions."""
    matrix = confusion_matrix(rows)
    total = len(rows)
    correct = sum(matrix[index][index] for index in range(len(FINAL_LABELS)))
    per_class: list[dict[str, float | int | str]] = []
    for index, label in enumerate(FINAL_LABELS):
        true_positive = matrix[index][index]
        support = sum(matrix[index])
        predicted_count = sum(row[index] for row in matrix)
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / support if support else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        label_rows = [row for row in rows if row["intended_label"] == label]
        accepted_count = sum(bool(row["accepted"]) for row in label_rows)
        accepted_correct = sum(
            bool(row["accepted"]) and bool(row["correct_top1"]) for row in label_rows
        )
        per_class.append(
            {
                "label": label,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
                "acceptance_rate": accepted_count / support if support else 0.0,
                "accepted_accuracy": (
                    accepted_correct / accepted_count if accepted_count else 0.0
                ),
                "rejection_rate": 1.0 - (accepted_count / support if support else 0.0),
                "mean_confidence": statistics.fmean(
                    float(row["confidence"]) for row in label_rows
                )
                if label_rows
                else 0.0,
            }
        )
    macro_precision = statistics.fmean(float(row["precision"]) for row in per_class)
    macro_recall = statistics.fmean(float(row["recall"]) for row in per_class)
    macro_f1 = statistics.fmean(float(row["f1"]) for row in per_class)
    weighted_precision = sum(
        float(row["precision"]) * int(row["support"]) for row in per_class
    ) / total
    weighted_recall = sum(
        float(row["recall"]) * int(row["support"]) for row in per_class
    ) / total
    weighted_f1 = sum(
        float(row["f1"]) * int(row["support"]) for row in per_class
    ) / total
    accuracy_interval = wilson_interval(correct, total)
    overall: dict[str, float | int] = {
        "trial_count": total,
        "correct_count": correct,
        "accuracy": correct / total,
        "accuracy_wilson_95_low": accuracy_interval[0],
        "accuracy_wilson_95_high": accuracy_interval[1],
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1,
    }
    return overall, per_class


def write_json(path: Path, value: Any) -> None:
    """Write deterministic readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    """Write stable UTF-8 CSV output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

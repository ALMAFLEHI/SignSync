"""Validate complete or partial Sprint 2.16B banking phone samples."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from labels import (
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
    SPRINT_2_16A_PILOT_INTENTS_4,
    SPRINT_2_16B_REMAINING_BANKING_INTENTS_36,
)
from sprint_2_16B_phone_dataset_config import (
    DEVICE_NAME,
    FINAL_BANKING_PHONE_TARGET,
    FRAME_WIDTH,
    HAND_WIDTH,
    NEW_SAMPLE_TARGET,
    PARTICIPANT_ID,
    PHONE_SAMPLE_DIR,
    REPORT_CSV_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAMPLES_PER_LABEL,
    SOURCE_NAME,
    SPRINT_ID,
    TARGET_FRAMES,
)


SAMPLE_ID_PATTERN = re.compile(
    rf"^{re.escape(PARTICIPANT_ID)}_(?P<label>.+)_R(?P<repetition>\d{{2}})$"
)


@dataclass(frozen=True)
class ValidatedSample:
    """Validated sample and its quality diagnostics."""

    path: str
    sample_id: str
    participant_id: str
    label: str
    repetition: int
    source: str
    device: str
    sprint_id: str
    frame_count: int
    frame_width: int
    sequence_sha256: str
    rounded_sequence_sha256: str
    all_zero_frames: int
    zero_value_percentage: float
    left_hand_frames: int
    right_hand_frames: int
    one_hand_frames: int
    both_hand_frames: int
    minimum_value: float
    maximum_value: float
    obvious_outlier_values: int


def iter_json_files(sample_dir: Path = PHONE_SAMPLE_DIR) -> list[Path]:
    """Return all pulled JSON files in deterministic order."""
    if not sample_dir.exists():
        return []
    return sorted(path for path in sample_dir.rglob("*.json") if path.is_file())


def required_string(payload: dict[str, Any], key: str) -> str:
    """Read one required non-empty string."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def required_integer(payload: dict[str, Any], key: str) -> int:
    """Read one required integer while excluding booleans."""
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def load_sample(path: Path) -> ValidatedSample:
    """Parse one JSON sample and validate metadata, shape, and hand slots."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")

    sample_id = required_string(payload, "sample_id")
    participant_id = required_string(payload, "participant_id")
    label = required_string(payload, "label")
    source = required_string(payload, "source")
    device = required_string(payload, "device")
    repetition = required_integer(payload, "repetition")
    frame_count = required_integer(payload, "frame_count")
    frame_width = required_integer(payload, "frame_width")
    frames_value = payload.get("frames")

    if participant_id != PARTICIPANT_ID:
        raise ValueError(f"participant_id must be {PARTICIPANT_ID}")
    if label not in BANKING_INTENTS_V3_40:
        if label in REMOVED_BANKING_INTENTS_V3_10:
            raise ValueError(f"removed label is not allowed: {label}")
        if label in ALPHABET_LABELS or label in DIGIT_LABELS:
            raise ValueError(f"alphabet/digit label is not allowed: {label}")
        raise ValueError(f"unexpected label: {label}")
    if source != SOURCE_NAME:
        raise ValueError(f"source must be {SOURCE_NAME}")
    if not device:
        raise ValueError("device context is missing")
    if not 1 <= repetition <= SAMPLES_PER_LABEL:
        raise ValueError("repetition must be in R01-R25")
    expected_sample_id = f"{PARTICIPANT_ID}_{label}_R{repetition:02d}"
    if sample_id != expected_sample_id:
        raise ValueError(f"sample_id must be {expected_sample_id}")
    if path.name != f"{expected_sample_id}.json":
        raise ValueError("filename must match sample_id")
    match = SAMPLE_ID_PATTERN.fullmatch(sample_id)
    if match is None or match.group("label") != label:
        raise ValueError("sample_id format is invalid")
    if frame_count != TARGET_FRAMES or frame_width != FRAME_WIDTH:
        raise ValueError("metadata shape must be 60 x 126")
    if not isinstance(frames_value, list) or len(frames_value) != TARGET_FRAMES:
        raise ValueError("frames must contain exactly 60 rows")
    if label in SPRINT_2_16B_REMAINING_BANKING_INTENTS_36:
        sample_sprint_id = required_string(payload, "sprint_id")
        if sample_sprint_id != SPRINT_ID:
            raise ValueError(f"Sprint 2.16B samples must declare sprint_id {SPRINT_ID}")
    else:
        sample_sprint_id = str(payload.get("sprint_id", "2.16A"))

    frames: list[list[float]] = []
    for frame_index, frame_value in enumerate(frames_value):
        if not isinstance(frame_value, list) or len(frame_value) != FRAME_WIDTH:
            raise ValueError(f"frame {frame_index} must contain 126 values")
        frame: list[float] = []
        for value in frame_value:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"frame {frame_index} contains a non-numeric value")
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f"frame {frame_index} contains NaN or infinity")
            frame.append(number)
        frames.append(frame)

    sequence = np.asarray(frames, dtype=np.float32)
    left_active = np.any(sequence[:, :HAND_WIDTH] != 0.0, axis=1)
    right_active = np.any(sequence[:, HAND_WIDTH:] != 0.0, axis=1)
    no_hand = ~(left_active | right_active)
    one_hand = left_active ^ right_active
    both_hands = left_active & right_active
    all_zero_frames = int(np.count_nonzero(no_hand))
    if all_zero_frames:
        raise ValueError(f"sample contains {all_zero_frames} no-hand frames")
    outlier_count = int(np.count_nonzero(np.abs(sequence) > 5.0))
    if outlier_count:
        raise ValueError(f"sample contains {outlier_count} obvious coordinate outliers")

    return ValidatedSample(
        path=path.as_posix(),
        sample_id=sample_id,
        participant_id=participant_id,
        label=label,
        repetition=repetition,
        source=source,
        device=device,
        sprint_id=sample_sprint_id,
        frame_count=frame_count,
        frame_width=frame_width,
        sequence_sha256=hashlib.sha256(sequence.tobytes()).hexdigest(),
        rounded_sequence_sha256=hashlib.sha256(
            np.round(sequence, decimals=6).tobytes()
        ).hexdigest(),
        all_zero_frames=all_zero_frames,
        zero_value_percentage=float(np.mean(sequence == 0.0) * 100.0),
        left_hand_frames=int(np.count_nonzero(left_active)),
        right_hand_frames=int(np.count_nonzero(right_active)),
        one_hand_frames=int(np.count_nonzero(one_hand)),
        both_hand_frames=int(np.count_nonzero(both_hands)),
        minimum_value=float(sequence.min()),
        maximum_value=float(sequence.max()),
        obvious_outlier_values=outlier_count,
    )


def validate_samples() -> tuple[list[ValidatedSample], list[dict[str, str]], dict[str, Any]]:
    """Validate every pulled sample and collect uniqueness diagnostics."""
    valid_samples: list[ValidatedSample] = []
    invalid_rows: list[dict[str, str]] = []
    sample_ids: dict[str, str] = {}
    label_repetitions: dict[tuple[str, int], str] = {}
    sequence_hashes: dict[str, str] = {}
    rounded_hash_groups: dict[str, list[str]] = defaultdict(list)
    duplicate_sample_ids: list[list[str]] = []
    duplicate_label_repetitions: list[list[str]] = []
    duplicate_sequences: list[list[str]] = []

    for path in iter_json_files():
        try:
            sample = load_sample(path)
            if sample.sample_id in sample_ids:
                duplicate_sample_ids.append([sample_ids[sample.sample_id], path.as_posix()])
                raise ValueError(f"duplicate sample_id: {sample.sample_id}")
            key = (sample.label, sample.repetition)
            if key in label_repetitions:
                duplicate_label_repetitions.append(
                    [label_repetitions[key], path.as_posix()]
                )
                raise ValueError(f"duplicate label/repetition: {sample.label} R{sample.repetition:02d}")
            if sample.sequence_sha256 in sequence_hashes:
                duplicate_sequences.append(
                    [sequence_hashes[sample.sequence_sha256], path.as_posix()]
                )
                raise ValueError("duplicate landmark sequence hash")
            sample_ids[sample.sample_id] = path.as_posix()
            label_repetitions[key] = path.as_posix()
            sequence_hashes[sample.sequence_sha256] = path.as_posix()
            rounded_hash_groups[sample.rounded_sequence_sha256].append(sample.sample_id)
            valid_samples.append(sample)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            invalid_rows.append({"path": path.as_posix(), "error": str(exc)})

    suspicious_groups = [
        sample_ids_for_hash
        for sample_ids_for_hash in rounded_hash_groups.values()
        if len(sample_ids_for_hash) > 1
    ]
    diagnostics = {
        "duplicate_sample_ids": duplicate_sample_ids,
        "duplicate_label_repetitions": duplicate_label_repetitions,
        "duplicate_sequence_hashes": duplicate_sequences,
        "suspicious_rounded_sequence_groups": suspicious_groups,
    }
    return valid_samples, invalid_rows, diagnostics


def build_summary(
    samples: list[ValidatedSample],
    invalid_rows: list[dict[str, str]],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    """Build complete and partial collection status without fabricating progress."""
    counts = Counter(sample.label for sample in samples)
    repetitions = defaultdict(set)
    for sample in samples:
        repetitions[sample.label].add(sample.repetition)
    missing = {
        label: [
            repetition
            for repetition in range(1, SAMPLES_PER_LABEL + 1)
            if repetition not in repetitions[label]
        ]
        for label in BANKING_INTENTS_V3_40
    }
    pilot_integrity = all(
        counts[label] == SAMPLES_PER_LABEL and not missing[label]
        for label in SPRINT_2_16A_PILOT_INTENTS_4
    )
    remaining_counts = {
        label: counts[label] for label in SPRINT_2_16B_REMAINING_BANKING_INTENTS_36
    }
    new_valid_samples = sum(remaining_counts.values())
    completed_remaining = [
        label for label, count in remaining_counts.items() if count == SAMPLES_PER_LABEL
    ]
    below_target = [
        label for label, count in remaining_counts.items() if count < SAMPLES_PER_LABEL
    ]
    duplicate_count = sum(
        len(diagnostics[key])
        for key in (
            "duplicate_sample_ids",
            "duplicate_label_repetitions",
            "duplicate_sequence_hashes",
        )
    )
    has_failure = bool(invalid_rows or duplicate_count or not pilot_integrity)
    complete = (
        not has_failure
        and len(samples) == FINAL_BANKING_PHONE_TARGET
        and new_valid_samples == NEW_SAMPLE_TARGET
        and len(completed_remaining) == 36
        and all(counts[label] == SAMPLES_PER_LABEL for label in BANKING_INTENTS_V3_40)
    )
    status = "PASS" if complete else "FAIL" if has_failure else "PENDING"
    nonzero_values = [
        value
        for sample in samples
        for value in (sample.minimum_value, sample.maximum_value)
        if value != 0.0
    ]
    return {
        "status": status,
        "sample_directory": PHONE_SAMPLE_DIR.as_posix(),
        "json_files_found": len(iter_json_files()),
        "valid_banking_samples": len(samples),
        "invalid_samples": len(invalid_rows),
        "new_valid_samples": new_valid_samples,
        "new_sample_target": NEW_SAMPLE_TARGET,
        "final_banking_phone_target": FINAL_BANKING_PHONE_TARGET,
        "pilot_integrity": pilot_integrity,
        "pilot_counts": {
            label: counts[label] for label in SPRINT_2_16A_PILOT_INTENTS_4
        },
        "remaining_counts": remaining_counts,
        "missing_repetitions": {
            label: missing[label]
            for label in SPRINT_2_16B_REMAINING_BANKING_INTENTS_36
        },
        "completed_remaining_labels": completed_remaining,
        "completed_remaining_label_count": len(completed_remaining),
        "labels_below_25": below_target,
        "duplicate_count": duplicate_count,
        "diagnostics": diagnostics,
        "invalid_rows": invalid_rows,
        "quality": {
            "all_zero_frames": sum(sample.all_zero_frames for sample in samples),
            "left_hand_frames": sum(sample.left_hand_frames for sample in samples),
            "right_hand_frames": sum(sample.right_hand_frames for sample in samples),
            "one_hand_frames": sum(sample.one_hand_frames for sample in samples),
            "two_hand_frames": sum(sample.both_hand_frames for sample in samples),
            "samples_with_one_hand_only": sum(
                sample.both_hand_frames == 0 for sample in samples
            ),
            "samples_with_both_hands": sum(
                sample.both_hand_frames > 0 for sample in samples
            ),
            "coordinate_min": min(nonzero_values) if nonzero_values else 0.0,
            "coordinate_max": max(nonzero_values) if nonzero_values else 0.0,
            "obvious_outlier_values": sum(
                sample.obvious_outlier_values for sample in samples
            ),
        },
    }


def write_reports(samples: list[ValidatedSample], summary: dict[str, Any]) -> None:
    """Write sample-level CSV and summary JSON/Markdown evidence."""
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample_fields = list(ValidatedSample.__dataclass_fields__)
    with REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=[*sample_fields, "valid", "error"])
        writer.writeheader()
        for sample in samples:
            writer.writerow({**asdict(sample), "valid": True, "error": ""})
        for invalid in summary["invalid_rows"]:
            writer.writerow(
                {
                    **{field: "" for field in sample_fields},
                    "path": invalid["path"],
                    "valid": False,
                    "error": invalid["error"],
                }
            )
    REPORT_JSON_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    counts = Counter(sample.label for sample in samples)
    count_rows = "\n".join(
        f"| {label} | {'pilot' if label in SPRINT_2_16A_PILOT_INTENTS_4 else '2.16B'} "
        f"| {counts[label]} | 25 | {'complete' if counts[label] == 25 else 'pending'} | "
        f"{', '.join(f'R{rep:02d}' for rep in summary['missing_repetitions'].get(label, [])) or '-'} |"
        for label in BANKING_INTENTS_V3_40
    )
    invalid_text = "\n".join(
        f"- `{row['path']}`: {row['error']}" for row in summary["invalid_rows"]
    ) or "- None"
    REPORT_MD_PATH.write_text(
        f"""# Sprint 2.16B Banking Phone Sample Check Report

## Result

{summary['status']}

## Progress

- Existing pilot integrity: {'PASS' if summary['pilot_integrity'] else 'FAIL'}
- New valid Sprint 2.16B samples: {summary['new_valid_samples']} / 900
- Completed remaining labels: {summary['completed_remaining_label_count']} / 36
- Valid banking samples: {summary['valid_banking_samples']} / 1000
- Invalid samples: {summary['invalid_samples']}
- Duplicate issues: {summary['duplicate_count']}
- All-zero/no-hand frames in valid samples: {summary['quality']['all_zero_frames']}
- Obvious coordinate outliers: {summary['quality']['obvious_outlier_values']}

## Per-Label Counts

| Label | Scope | Valid | Target | Status | Missing Repetitions |
| --- | --- | ---: | ---: | --- | --- |
{count_rows}

## Invalid Or Unexpected Samples

{invalid_text}

## Interpretation

`PASS` is possible only after all 40 banking intents contain exactly 25 valid samples, the final total is 1,000, pilot integrity is preserved, and no invalid, duplicate, removed, alphabet, digit, or unexpected sample exists. `PENDING` is the expected state before manual Sprint 2.16B recording finishes.
""",
        encoding="utf-8",
    )


def main() -> int:
    """Validate current progress, write reports, and print a concise summary."""
    samples, invalid_rows, diagnostics = validate_samples()
    summary = build_summary(samples, invalid_rows, diagnostics)
    write_reports(samples, summary)
    print("Sprint 2.16B Banking Phone Sample Check")
    print("-----------------------------------------")
    print(f"sample folder: {PHONE_SAMPLE_DIR.as_posix()}")
    print(f"pilot integrity: {'PASS' if summary['pilot_integrity'] else 'FAIL'}")
    print(f"new valid samples: {summary['new_valid_samples']}/{NEW_SAMPLE_TARGET}")
    print(
        "completed remaining labels: "
        f"{summary['completed_remaining_label_count']}/36"
    )
    print(
        "final banking phone samples: "
        f"{summary['valid_banking_samples']}/{FINAL_BANKING_PHONE_TARGET}"
    )
    print(f"invalid samples: {summary['invalid_samples']}")
    print(f"duplicate issues: {summary['duplicate_count']}")
    print(f"Markdown report: {REPORT_MD_PATH.as_posix()}")
    print(f"CSV report: {REPORT_CSV_PATH.as_posix()}")
    print(f"JSON report: {REPORT_JSON_PATH.as_posix()}")
    if summary["status"] == "PASS":
        print("PASS: complete 1,000-sample banking phone dataset validated.")
        return 0
    if summary["status"] == "FAIL":
        print("FAIL: invalid, duplicate, or damaged pilot samples require review.")
        return 1
    print("PENDING: collection workflow is ready; 900 new samples are not yet complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate Sprint 2.16A phone-camera landmark JSON samples."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phone_dataset_config import (
    DEVICE_NAME,
    EXPECTED_SAMPLES_PER_LABEL,
    LANDMARK_DIMENSION,
    PARTICIPANT_ID,
    PHONE_SAMPLE_CHECK_CSV_PATH,
    PHONE_SAMPLE_CHECK_MD_PATH,
    PHONE_SAMPLE_DIR,
    SOURCE_NAME,
    TARGET_FRAMES,
    WEAK_LABELS,
    expected_total_phone_samples,
)


@dataclass(frozen=True)
class PhoneSample:
    """Validated phone landmark sample payload."""

    sample_id: str
    participant_id: str
    label: str
    repetition: int
    source: str
    device: str
    frames: list[list[float]]
    path: Path


def iter_sample_files(sample_dir: Path = PHONE_SAMPLE_DIR) -> list[Path]:
    """Return phone sample JSON files in stable order."""
    if not sample_dir.exists():
        return []
    return sorted(path for path in sample_dir.rglob("*.json") if path.is_file())


def load_and_validate_sample(path: Path) -> PhoneSample:
    """Load one sample JSON file and validate the 60 x 126 landmark contract."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("sample JSON root must be an object")

    sample_id = _required_str(payload, "sample_id")
    participant_id = _required_str(payload, "participant_id")
    label = _required_str(payload, "label")
    source = _required_str(payload, "source")
    device = _required_str(payload, "device")
    repetition = _required_int(payload, "repetition")
    frame_count = _required_int(payload, "frame_count")
    frame_width = _required_int(payload, "frame_width")
    frames = payload.get("frames")

    if participant_id != PARTICIPANT_ID:
        raise ValueError(f"participant_id must be {PARTICIPANT_ID}")
    if label not in WEAK_LABELS:
        raise ValueError(f"label must be one of {WEAK_LABELS}")
    if source != SOURCE_NAME:
        raise ValueError(f"source must be {SOURCE_NAME}")
    if device != DEVICE_NAME:
        raise ValueError(f"device must be {DEVICE_NAME}")
    expected_sample_id = f"{PARTICIPANT_ID}_{label}_R{repetition:02d}"
    if sample_id != expected_sample_id:
        raise ValueError(f"sample_id must be {expected_sample_id}")
    if frame_count != TARGET_FRAMES or frame_width != LANDMARK_DIMENSION:
        raise ValueError(
            f"expected frame_count/frame_width {TARGET_FRAMES}/{LANDMARK_DIMENSION}, "
            f"found {frame_count}/{frame_width}"
        )
    if not isinstance(frames, list) or len(frames) != TARGET_FRAMES:
        raise ValueError(f"frames must contain {TARGET_FRAMES} rows")

    parsed_frames: list[list[float]] = []
    for frame_index, frame in enumerate(frames):
        if not isinstance(frame, list) or len(frame) != LANDMARK_DIMENSION:
            raise ValueError(
                f"frame {frame_index} must contain {LANDMARK_DIMENSION} numeric values"
            )
        parsed_frame = [float(value) for value in frame]
        if not all(math.isfinite(value) for value in parsed_frame):
            raise ValueError(f"frame {frame_index} contains NaN or infinite values")
        parsed_frames.append(parsed_frame)

    return PhoneSample(
        sample_id=sample_id,
        participant_id=participant_id,
        label=label,
        repetition=repetition,
        source=source,
        device=device,
        frames=parsed_frames,
        path=path,
    )


def validate_all_samples(sample_dir: Path = PHONE_SAMPLE_DIR) -> tuple[list[PhoneSample], list[dict[str, str]]]:
    """Validate every phone sample and return valid samples plus invalid rows."""
    valid_samples: list[PhoneSample] = []
    invalid_rows: list[dict[str, str]] = []
    seen_sample_ids: set[str] = set()

    for path in iter_sample_files(sample_dir):
        try:
            sample = load_and_validate_sample(path)
            if sample.sample_id in seen_sample_ids:
                raise ValueError(f"duplicate sample_id: {sample.sample_id}")
            seen_sample_ids.add(sample.sample_id)
            valid_samples.append(sample)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            invalid_rows.append({"path": path.as_posix(), "error": str(exc)})

    return valid_samples, invalid_rows


def summarize_counts(samples: list[PhoneSample]) -> Counter[str]:
    """Count valid samples by weak label."""
    return Counter(sample.label for sample in samples)


def target_reached(counts: Counter[str]) -> bool:
    """Return whether every weak label has the minimum required phone samples."""
    return all(counts[label] >= EXPECTED_SAMPLES_PER_LABEL for label in WEAK_LABELS)


def write_reports(samples: list[PhoneSample], invalid_rows: list[dict[str, str]]) -> None:
    """Write CSV and Markdown phone sample validation reports."""
    counts = summarize_counts(samples)
    duplicate_count = len(samples) - len({sample.sample_id for sample in samples})
    status = "PASS" if target_reached(counts) and not invalid_rows else "PENDING"
    if invalid_rows or duplicate_count:
        status = "FAIL"

    PHONE_SAMPLE_CHECK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PHONE_SAMPLE_CHECK_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(
            report_file,
            fieldnames=["label", "valid_samples", "target", "status"],
        )
        writer.writeheader()
        for label in WEAK_LABELS:
            count = counts[label]
            writer.writerow(
                {
                    "label": label,
                    "valid_samples": count,
                    "target": EXPECTED_SAMPLES_PER_LABEL,
                    "status": "PASS" if count >= EXPECTED_SAMPLES_PER_LABEL else "PENDING",
                }
            )

    count_rows = "\n".join(
        f"| {label} | {counts[label]} | {EXPECTED_SAMPLES_PER_LABEL} | "
        f"{'PASS' if counts[label] >= EXPECTED_SAMPLES_PER_LABEL else 'PENDING'} |"
        for label in WEAK_LABELS
    )
    invalid_text = "\n".join(
        f"- {row['path']}: {row['error']}" for row in invalid_rows
    )
    content = f"""# Sprint 2.16A Phone Sample Check Report

## Result
{status}

## Summary
- Sample folder: {PHONE_SAMPLE_DIR.as_posix()}
- Valid samples found: {len(samples)}
- Minimum target: {expected_total_phone_samples()}
- Invalid samples: {len(invalid_rows)}
- Duplicate sample_id rows: {duplicate_count}

## Counts
| Label | Valid Samples | Target | Status |
| --- | ---: | ---: | --- |
{count_rows}

## Invalid Samples
{invalid_text if invalid_text else '- None'}

## Note
If the target is pending, do not retrain yet. Record and pull the missing phone-camera landmark samples first.
"""
    PHONE_SAMPLE_CHECK_MD_PATH.write_text(content, encoding="utf-8")


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def main() -> int:
    """Validate phone samples and write reports."""
    samples, invalid_rows = validate_all_samples()
    write_reports(samples, invalid_rows)
    counts = summarize_counts(samples)

    print("Sprint 2.16A Phone Landmark Sample Check")
    print("----------------------------------------")
    print(f"sample folder: {PHONE_SAMPLE_DIR.as_posix()}")
    print(f"valid samples found: {len(samples)}")
    for label in WEAK_LABELS:
        print(f"{label}: {counts[label]}/{EXPECTED_SAMPLES_PER_LABEL}")
    print(f"invalid samples: {len(invalid_rows)}")
    print(f"CSV report: {PHONE_SAMPLE_CHECK_CSV_PATH.as_posix()}")
    print(f"Markdown report: {PHONE_SAMPLE_CHECK_MD_PATH.as_posix()}")
    if invalid_rows:
        print("FAIL: invalid phone sample files were found.")
        return 1
    if target_reached(counts):
        print("PASS: phone sample target reached.")
    else:
        print("PENDING: phone sample target not reached yet. No fake data was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

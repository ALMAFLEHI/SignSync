"""Verify Sprint 2.9 full-dataset raw videos, landmarks, masks, and metadata."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from full_landmark_extraction_config import (
    CHECK_REPORT_CSV_PATH,
    CHECK_REPORT_MD_PATH,
    EXPECTED_TOTAL_RAW_VIDEOS,
    FULL_DATASET_PARTICIPANT,
    HAND_MASK_DIMENSION,
    LANDMARK_OUTPUT_DIMENSION,
    METADATA_PATH,
    iter_expected_samples,
)


METADATA_HEADERS = [
    "sample_id",
    "participant_id",
    "label",
    "repetition",
    "video_path",
    "landmark_path",
    "status",
    "notes",
]


def parse_args() -> argparse.Namespace:
    """Parse the participant whose complete landmark data is verified."""
    parser = argparse.ArgumentParser(
        description="Verify all Sprint 2.9 raw video, landmark, mask, and metadata outputs."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    return parser.parse_args()


def read_metadata_index() -> tuple[dict[str, list[dict[str, str]]], list[str], list[str]]:
    """Read metadata and identify duplicates without changing collection records."""
    errors: list[str] = []
    rows_by_id: dict[str, list[dict[str, str]]] = {}
    if not METADATA_PATH.exists():
        return rows_by_id, ["metadata.csv is missing"], []

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            errors.append(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
            return rows_by_id, errors, []
        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if sample_id:
                rows_by_id.setdefault(sample_id, []).append(row)
    duplicates = sorted(
        sample_id for sample_id, rows in rows_by_id.items() if len(rows) > 1
    )
    return rows_by_id, errors, duplicates


def validate_array_shapes(landmark_path: Path, mask_path: Path) -> tuple[str, str, str]:
    """Return landmark/mask shapes and a clear error message when invalid."""
    try:
        import numpy as np

        landmarks = np.load(landmark_path, allow_pickle=False)
        mask = np.load(mask_path, allow_pickle=False)
    except Exception as exc:  # noqa: BLE001 - report corrupt numpy outputs clearly.
        return "", "", f"could not load landmark or mask output: {exc}"

    landmark_shape = str(tuple(landmarks.shape))
    mask_shape = str(tuple(mask.shape))
    issues: list[str] = []
    if landmarks.ndim != 2 or landmarks.shape[1] != LANDMARK_OUTPUT_DIMENSION:
        issues.append(f"landmark shape must be frames x {LANDMARK_OUTPUT_DIMENSION}")
    if landmarks.ndim == 2 and landmarks.shape[0] < 1:
        issues.append("landmark array must contain at least one frame")
    if mask.ndim != 2 or mask.shape[1] != HAND_MASK_DIMENSION:
        issues.append(f"mask shape must be frames x {HAND_MASK_DIMENSION}")
    if landmarks.ndim == 2 and mask.ndim == 2 and landmarks.shape[0] != mask.shape[0]:
        issues.append("landmark and mask frame counts do not match")
    return landmark_shape, mask_shape, "; ".join(issues)


def build_report_rows(
    participant_id: str,
    rows_by_id: dict[str, list[dict[str, str]]],
    metadata_errors: list[str],
) -> list[dict[str, str]]:
    """Validate every configured Sprint 2.9 sample and return report-ready rows."""
    report_rows: list[dict[str, str]] = []
    for sample in iter_expected_samples(participant_id):
        sample_id = str(sample["sample_id"])
        video_path = Path(sample["video"])
        landmark_path = Path(sample["landmarks"])
        mask_path = Path(sample["mask"])
        metadata_rows = rows_by_id.get(sample_id, [])
        issues: list[str] = list(metadata_errors)

        if not video_path.exists():
            issues.append("missing raw video")
        elif video_path.stat().st_size <= 0:
            issues.append("raw video is empty")

        if not metadata_rows:
            issues.append("missing metadata row")
        elif len(metadata_rows) > 1:
            issues.append("duplicate metadata rows")
        else:
            row = metadata_rows[0]
            if row.get("participant_id") != participant_id:
                issues.append("metadata participant_id is incorrect")
            if row.get("label") != sample["label"]:
                issues.append("metadata label is incorrect")
            if row.get("repetition") != str(sample["repetition"]):
                issues.append("metadata repetition is incorrect")
            if row.get("video_path") != video_path.as_posix():
                issues.append("metadata video_path is incorrect")

        landmark_shape = ""
        mask_shape = ""
        if not landmark_path.exists():
            issues.append("missing landmark output")
        if not mask_path.exists():
            issues.append("missing mask output")
        if landmark_path.exists() and mask_path.exists():
            landmark_shape, mask_shape, shape_issue = validate_array_shapes(landmark_path, mask_path)
            if shape_issue:
                issues.append(shape_issue)

        report_rows.append(
            {
                "sample_id": sample_id,
                "label": str(sample["label"]),
                "repetition": str(sample["repetition"]),
                "video_path": video_path.as_posix(),
                "landmark_path": landmark_path.as_posix(),
                "mask_path": mask_path.as_posix(),
                "video_exists": "yes" if video_path.exists() else "no",
                "metadata_rows": str(len(metadata_rows)),
                "landmark_shape": landmark_shape,
                "mask_shape": mask_shape,
                "passed": "yes" if not issues else "no",
                "issues": "; ".join(issues),
            }
        )
    return report_rows


def write_reports(
    report_rows: list[dict[str, str]], duplicate_sample_ids: list[str], passed: bool
) -> None:
    """Save the requested Sprint 2.9 CSV and Markdown verification reports."""
    CHECK_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id", "label", "repetition", "video_path", "landmark_path", "mask_path",
        "video_exists", "metadata_rows", "landmark_shape", "mask_shape", "passed", "issues",
    ]
    with CHECK_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    missing_by_type = Counter()
    for row in failed_rows:
        for issue in row["issues"].split("; "):
            if issue:
                missing_by_type[issue] += 1
    failed_text = (
        "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows)
        if failed_rows else "- None"
    )
    summary_text = (
        "\n".join(f"- {issue}: {count}" for issue, count in sorted(missing_by_type.items()))
        if missing_by_type else "- None"
    )
    duplicate_text = (
        "\n".join(f"- {sample_id}" for sample_id in duplicate_sample_ids)
        if duplicate_sample_ids else "- None"
    )
    content = f"""# Sprint 2.9 Full Landmark Dataset Check

## Expected Scope
- Raw videos: {EXPECTED_TOTAL_RAW_VIDEOS}
- Landmark outputs: {EXPECTED_TOTAL_RAW_VIDEOS}
- Mask outputs: {EXPECTED_TOTAL_RAW_VIDEOS}
- Landmark dimension: {LANDMARK_OUTPUT_DIMENSION}
- Hand mask dimension: {HAND_MASK_DIMENSION}
- Payment expected: yes
- Receipt expected: no

## Result
{'PASS' if passed else 'FAIL'}

## Failure Summary
{summary_text}

## Failed Or Missing Items
{failed_text}

## Duplicate Metadata Sample IDs
{duplicate_text}

## Report Files
- CSV report: {CHECK_REPORT_CSV_PATH.as_posix()}
- Markdown report: {CHECK_REPORT_MD_PATH.as_posix()}
"""
    CHECK_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_summary(report_rows: list[dict[str, str]], duplicate_sample_ids: list[str], passed: bool) -> None:
    """Print a concise verification status for terminal evidence."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.9 Full Landmark Dataset Verification Summary")
    print("-----------------------------------------------------")
    print(f"expected raw videos: {EXPECTED_TOTAL_RAW_VIDEOS}")
    print(f"expected landmark outputs: {EXPECTED_TOTAL_RAW_VIDEOS}")
    print(f"failed, missing, or invalid items: {len(failed_rows)}")
    print(f"duplicate metadata sample IDs: {len(duplicate_sample_ids)}")
    print(f"CSV report: {CHECK_REPORT_CSV_PATH.as_posix()}")
    print(f"Markdown report: {CHECK_REPORT_MD_PATH.as_posix()}")
    print("PASS: full landmark dataset verification passed." if passed else "FAIL: full landmark dataset verification failed.")


def main() -> int:
    """Check all expected full-dataset outputs without modifying videos or arrays."""
    args = parse_args()
    rows_by_id, metadata_errors, duplicate_sample_ids = read_metadata_index()
    report_rows = build_report_rows(args.participant, rows_by_id, metadata_errors)
    passed = all(row["passed"] == "yes" for row in report_rows) and not duplicate_sample_ids
    write_reports(report_rows, duplicate_sample_ids, passed)
    print_summary(report_rows, duplicate_sample_ids, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

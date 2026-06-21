"""Verify manually recorded Sprint 2.8 remaining-label raw videos and metadata."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from full_collection_config import (
    EXPECTED_FULL_COLLECTION_VIDEOS,
    FULL_DATASET_PARTICIPANT,
    FULL_DATASET_NOTES,
    FULL_DATASET_REWORK_NOTES,
    FULL_DATASET_REPETITIONS,
    REMAINING_LABELS,
)


RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
CSV_REPORT_PATH = EVIDENCE_DIR / "sprint_2_8_full_collection_check.csv"
MARKDOWN_REPORT_PATH = EVIDENCE_DIR / "sprint_2_8_full_collection_check.md"

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
    """Parse the participant whose full remaining-label collection is checked."""
    parser = argparse.ArgumentParser(
        description="Verify the Sprint 2.8 450-video remaining-label collection."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    return parser.parse_args()


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the same sample ID format used by collect_video.py."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_video_path(participant_id: str, label: str, repetition: int) -> Path:
    """Return the expected raw video path for one Sprint 2.8 sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return RAW_VIDEO_DIR / label / f"{sample_id}.mp4"


def read_metadata_rows() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Read metadata rows, grouped by sample ID, without modifying metadata.csv."""
    errors: list[str] = []
    rows_by_sample_id: dict[str, list[dict[str, str]]] = {}
    if not METADATA_PATH.exists():
        return rows_by_sample_id, ["metadata.csv is missing."]

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            errors.append(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
            return rows_by_sample_id, errors

        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if sample_id:
                rows_by_sample_id.setdefault(sample_id, []).append(row)
    return rows_by_sample_id, errors


def validate_metadata_row(
    row: dict[str, str], participant_id: str, label: str, repetition: int, video_path: Path
) -> list[str]:
    """Check fields required for a newly recorded raw Sprint 2.8 sample."""
    issues: list[str] = []
    if row.get("participant_id") != participant_id:
        issues.append("metadata participant_id is incorrect")
    if row.get("label") != label:
        issues.append("metadata label is incorrect")
    if row.get("repetition") != str(repetition):
        issues.append("metadata repetition is incorrect")
    if row.get("video_path") != video_path.as_posix():
        issues.append("metadata video_path is incorrect")
    if row.get("landmark_path", ""):
        issues.append("metadata landmark_path must be empty before extraction")
    if row.get("status") != "raw_recorded":
        issues.append("metadata status is not raw_recorded")
    valid_notes = (FULL_DATASET_NOTES, FULL_DATASET_REWORK_NOTES)
    if not any(note in row.get("notes", "") for note in valid_notes):
        issues.append("metadata notes do not identify Sprint 2.8 collection or rework")
    return issues


def build_report_rows(
    participant_id: str,
    rows_by_sample_id: dict[str, list[dict[str, str]]],
    metadata_errors: list[str],
) -> list[dict[str, str]]:
    """Build one verification row for every required remaining-label sample."""
    report_rows: list[dict[str, str]] = []
    for label in REMAINING_LABELS:
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1):
            sample_id = build_sample_id(participant_id, label, repetition)
            video_path = expected_video_path(participant_id, label, repetition)
            metadata_rows = rows_by_sample_id.get(sample_id, [])
            issues: list[str] = []

            video_exists = video_path.exists()
            file_size = video_path.stat().st_size if video_exists else 0
            if not video_exists:
                issues.append("missing video")
            elif file_size <= 0:
                issues.append("empty video file")

            if metadata_errors:
                issues.extend(metadata_errors)
            elif not metadata_rows:
                issues.append("missing metadata row")
            elif len(metadata_rows) > 1:
                issues.append("duplicate metadata rows")
            else:
                issues.extend(
                    validate_metadata_row(
                        metadata_rows[0], participant_id, label, repetition, video_path
                    )
                )

            report_rows.append(
                {
                    "sample_id": sample_id,
                    "label": label,
                    "repetition": str(repetition),
                    "video_path": video_path.as_posix(),
                    "video_exists": "yes" if video_exists else "no",
                    "file_size_bytes": str(file_size),
                    "metadata_rows": str(len(metadata_rows)),
                    "status": metadata_rows[0].get("status", "") if metadata_rows else "",
                    "passed": "yes" if not issues else "no",
                    "issues": "; ".join(issues),
                }
            )
    return report_rows


def find_duplicate_expected_sample_ids(
    rows_by_sample_id: dict[str, list[dict[str, str]]], participant_id: str
) -> list[str]:
    """Return duplicates only inside the Sprint 2.8 expected collection scope."""
    expected_ids = {
        build_sample_id(participant_id, label, repetition)
        for label in REMAINING_LABELS
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1)
    }
    counts = Counter({sample_id: len(rows) for sample_id, rows in rows_by_sample_id.items()})
    return sorted(
        sample_id
        for sample_id, count in counts.items()
        if sample_id in expected_ids and count > 1
    )


def write_csv_report(report_rows: list[dict[str, str]]) -> None:
    """Write the detailed 450-row verification evidence report."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "video_path",
        "video_exists",
        "file_size_bytes",
        "metadata_rows",
        "status",
        "passed",
        "issues",
    ]
    with CSV_REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)


def write_markdown_report(
    report_rows: list[dict[str, str]], duplicate_sample_ids: list[str], passed: bool, participant_id: str
) -> None:
    """Write a compact FYP-ready result report with any missing collection items."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    failed_text = (
        "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows)
        if failed_rows
        else "- None"
    )
    duplicate_text = (
        "\n".join(f"- {sample_id}" for sample_id in duplicate_sample_ids)
        if duplicate_sample_ids
        else "- None"
    )
    missing_summary = format_missing_recording_summary(report_rows)
    content = f"""# Sprint 2.8 Full Dataset Collection Check

## Participant
{participant_id}

## Expected Scope
- Remaining labels: {len(REMAINING_LABELS)}
- Repetitions per label: {FULL_DATASET_REPETITIONS}
- Expected videos: {EXPECTED_FULL_COLLECTION_VIDEOS}

## Result
{'PASS' if passed else 'FAIL'}

## Failed Or Missing Items
{failed_text}

## Missing Recording Summary
{missing_summary}

## Duplicate Metadata Sample IDs In Sprint 2.8 Scope
{duplicate_text}

## Report Files
- CSV report: {CSV_REPORT_PATH.as_posix()}
- Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}
"""
    MARKDOWN_REPORT_PATH.write_text(content, encoding="utf-8")


def format_missing_recording_summary(report_rows: list[dict[str, str]]) -> str:
    """Group missing raw videos or metadata rows so rework labels are easy to find."""
    missing_counts: Counter[str] = Counter()
    for row in report_rows:
        if row["video_exists"] == "no" or row["metadata_rows"] == "0":
            missing_counts[row["label"]] += 1

    if not missing_counts:
        return "- None"
    return "\n".join(
        f"- {label}: {count} recording(s) missing a video or metadata row"
        for label, count in sorted(missing_counts.items())
    )


def print_summary(
    report_rows: list[dict[str, str]], duplicate_sample_ids: list[str], passed: bool, participant_id: str
) -> None:
    """Print a clear pass/fail summary after manual collection is complete."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.8 Full Collection Verification Summary")
    print("-----------------------------------------------")
    print(f"participant: {participant_id}")
    print(f"remaining labels considered: {len(REMAINING_LABELS)}")
    print(f"repetitions per label: {FULL_DATASET_REPETITIONS}")
    print(f"expected videos: {EXPECTED_FULL_COLLECTION_VIDEOS}")
    print(f"failed or missing items: {len(failed_rows)}")
    print(f"duplicate sample_id rows: {len(duplicate_sample_ids)}")
    print(f"CSV report: {CSV_REPORT_PATH.as_posix()}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}")
    missing_summary = format_missing_recording_summary(report_rows)
    if missing_summary != "- None":
        print("Missing recording summary:")
        print(missing_summary)
    if passed:
        print("PASS: Sprint 2.8 full collection verification passed.")
    else:
        print("FAIL: Sprint 2.8 full collection verification failed.")
        for row in failed_rows[:20]:
            print(f"- {row['sample_id']}: {row['issues']}")


def main() -> int:
    """Verify full collection files and metadata without modifying them."""
    args = parse_args()
    rows_by_sample_id, metadata_errors = read_metadata_rows()
    report_rows = build_report_rows(args.participant, rows_by_sample_id, metadata_errors)
    duplicate_sample_ids = find_duplicate_expected_sample_ids(rows_by_sample_id, args.participant)
    passed = all(row["passed"] == "yes" for row in report_rows) and not duplicate_sample_ids
    write_csv_report(report_rows)
    write_markdown_report(report_rows, duplicate_sample_ids, passed, args.participant)
    print_summary(report_rows, duplicate_sample_ids, passed, args.participant)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

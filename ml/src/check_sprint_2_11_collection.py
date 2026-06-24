"""Verify Sprint 2.11 raw-video collection without modifying videos or metadata."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from labels import BANKING_INTENTS_V1
from sprint_2_11_intent_expansion_config import (
    EXPECTED_NEW_LABELS,
    EXPECTED_NEW_VIDEOS,
    EXPANSION_LABELS,
    METADATA_PATH,
    SPRINT_2_11_NOTES,
    SPRINT_2_11_PARTICIPANT,
    SPRINT_2_11_REPETITIONS,
    expected_video_path,
)


EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
CSV_REPORT_PATH = EVIDENCE_DIR / "sprint_2_11_collection_check.csv"
MARKDOWN_REPORT_PATH = EVIDENCE_DIR / "sprint_2_11_collection_check.md"
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
VALID_RAW_STATUSES = {"raw_recorded", "landmarks_extracted"}


def parse_args() -> argparse.Namespace:
    """Parse the participant whose Sprint 2.11 recording scope is checked."""
    parser = argparse.ArgumentParser(
        description="Verify the 300 Sprint 2.11 banking intent raw recordings."
    )
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    return parser.parse_args()


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the same stable ID used by the collection tool."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def read_metadata_rows() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Read metadata safely, indexed by sample ID, without changing it."""
    rows_by_sample_id: dict[str, list[dict[str, str]]] = {}
    errors: list[str] = []
    if not METADATA_PATH.exists():
        return rows_by_sample_id, ["metadata.csv is missing"]

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            return rows_by_sample_id, ["metadata.csv headers are incorrect"]
        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if sample_id:
                rows_by_sample_id.setdefault(sample_id, []).append(row)
    return rows_by_sample_id, errors


def validate_metadata_row(
    row: dict[str, str], participant_id: str, label: str, repetition: int, video_path: Path
) -> list[str]:
    """Validate one expected raw-recording metadata row for Sprint 2.11."""
    issues: list[str] = []
    if row.get("participant_id") != participant_id:
        issues.append("metadata participant_id is incorrect")
    if row.get("label") != label:
        issues.append("metadata label is incorrect")
    if row.get("repetition") != str(repetition):
        issues.append("metadata repetition is incorrect")
    if row.get("video_path") != video_path.as_posix():
        issues.append("metadata video_path is incorrect")
    if row.get("status") not in VALID_RAW_STATUSES:
        issues.append("metadata status is not a valid recorded status")
    if SPRINT_2_11_NOTES not in row.get("notes", ""):
        issues.append("metadata notes do not identify Sprint 2.11 collection")
    return issues


def build_report_rows(
    participant_id: str,
    rows_by_sample_id: dict[str, list[dict[str, str]]],
    metadata_errors: list[str],
) -> list[dict[str, str]]:
    """Build 300 detailed verification rows for expansion labels only."""
    report_rows: list[dict[str, str]] = []
    for label in EXPANSION_LABELS:
        for repetition in range(1, SPRINT_2_11_REPETITIONS + 1):
            sample_id = build_sample_id(participant_id, label, repetition)
            video_path = expected_video_path(participant_id, label, repetition)
            metadata_rows = rows_by_sample_id.get(sample_id, [])
            issues = list(metadata_errors)
            video_exists = video_path.exists()
            file_size = video_path.stat().st_size if video_exists else 0
            if not video_exists:
                issues.append("missing raw video")
            elif file_size <= 0:
                issues.append("raw video is empty")

            if not metadata_rows:
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
    """Return duplicate metadata IDs only within the new 300-sample scope."""
    expected_ids = {
        build_sample_id(participant_id, label, repetition)
        for label in EXPANSION_LABELS
        for repetition in range(1, SPRINT_2_11_REPETITIONS + 1)
    }
    counts = Counter({sample_id: len(rows) for sample_id, rows in rows_by_sample_id.items()})
    return sorted(
        sample_id
        for sample_id, count in counts.items()
        if sample_id in expected_ids and count > 1
    )


def write_reports(
    report_rows: list[dict[str, str]], duplicate_sample_ids: list[str], passed: bool, participant_id: str
) -> None:
    """Write the detailed CSV and compact Markdown collection evidence reports."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id", "label", "repetition", "video_path", "video_exists",
        "file_size_bytes", "metadata_rows", "status", "passed", "issues",
    ]
    with CSV_REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    failure_text = (
        "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows)
        if failed_rows
        else "- None"
    )
    duplicate_text = (
        "\n".join(f"- {sample_id}" for sample_id in duplicate_sample_ids)
        if duplicate_sample_ids
        else "- None"
    )
    content = f"""# Sprint 2.11 Banking Intent Collection Check

## Participant
{participant_id}

## Expected Scope
- New banking labels: {EXPECTED_NEW_LABELS}
- Repetitions per label: {SPRINT_2_11_REPETITIONS}
- Expected new raw videos: {EXPECTED_NEW_VIDEOS}
- V1 labels counted in this report: no
- Receipt expected: no

## Result
{'PASS' if passed else 'FAIL'}

## Failed Or Missing Items
{failure_text}

## Duplicate Metadata Sample IDs In Sprint 2.11 Scope
{duplicate_text}

## Report Files
- CSV report: {CSV_REPORT_PATH.as_posix()}
- Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}
"""
    MARKDOWN_REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Verify the future manual collection without correcting or changing any data."""
    args = parse_args()
    rows_by_sample_id, metadata_errors = read_metadata_rows()
    report_rows = build_report_rows(args.participant, rows_by_sample_id, metadata_errors)
    duplicate_sample_ids = find_duplicate_expected_sample_ids(rows_by_sample_id, args.participant)
    valid_scope = "receipt" not in EXPANSION_LABELS and not set(EXPANSION_LABELS).intersection(BANKING_INTENTS_V1)
    passed = (
        valid_scope
        and all(row["passed"] == "yes" for row in report_rows)
        and not duplicate_sample_ids
    )
    write_reports(report_rows, duplicate_sample_ids, passed, args.participant)

    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.11 Collection Verification Summary")
    print("-------------------------------------------")
    print(f"participant: {args.participant}")
    print(f"new labels considered: {EXPECTED_NEW_LABELS}")
    print(f"repetitions per label: {SPRINT_2_11_REPETITIONS}")
    print(f"expected videos: {EXPECTED_NEW_VIDEOS}")
    print(f"failed or missing items: {len(failed_rows)}")
    print(f"duplicate sample_id rows: {len(duplicate_sample_ids)}")
    print(f"CSV report: {CSV_REPORT_PATH.as_posix()}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}")
    if passed:
        print("PASS: Sprint 2.11 collection verification passed.")
        return 0
    print("FAIL: Sprint 2.11 collection verification failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

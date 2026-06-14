"""Verify the Sprint 2.3 trial dataset after manual collection."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from trial_config import DEFAULT_PARTICIPANT_ID, DEFAULT_REPETITIONS, TRIAL_LABELS


RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
CSV_REPORT_PATH = EVIDENCE_DIR / "sprint_2_3_trial_dataset_check.csv"
MARKDOWN_REPORT_PATH = EVIDENCE_DIR / "sprint_2_3_trial_dataset_check.md"

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
    """Parse verification options."""
    parser = argparse.ArgumentParser(
        description="Check the Sprint 2.3 trial dataset videos and metadata."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    return parser.parse_args()


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the expected Sprint 2.3 sample ID."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_video_path(participant_id: str, label: str, repetition: int) -> Path:
    """Build the expected path for one raw trial video."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return RAW_VIDEO_DIR / label / f"{sample_id}.mp4"


def read_metadata_rows() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Read metadata rows and return rows grouped by sample_id."""
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


def build_report_rows(
    participant_id: str,
    repetitions: int,
    rows_by_sample_id: dict[str, list[dict[str, str]]],
    metadata_errors: list[str],
) -> list[dict[str, str]]:
    """Build one verification report row for each expected trial sample."""
    report_rows: list[dict[str, str]] = []

    for label in TRIAL_LABELS:
        for repetition in range(1, repetitions + 1):
            sample_id = build_sample_id(participant_id, label, repetition)
            video_path = expected_video_path(participant_id, label, repetition)
            issues: list[str] = []

            video_exists = video_path.exists()
            file_size = video_path.stat().st_size if video_exists else 0
            if not video_exists:
                issues.append("missing video")
            elif file_size <= 0:
                issues.append("empty video file")

            metadata_rows = rows_by_sample_id.get(sample_id, [])
            if metadata_errors:
                issues.extend(metadata_errors)
            elif not metadata_rows:
                issues.append("missing metadata row")
            else:
                statuses = {row.get("status", "") for row in metadata_rows}
                if "raw_recorded" not in statuses:
                    issues.append("metadata status is not raw_recorded")
                if len(metadata_rows) > 1:
                    issues.append("duplicate metadata rows")

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


def find_duplicate_sample_ids(rows_by_sample_id: dict[str, list[dict[str, str]]]) -> list[str]:
    """Detect duplicate sample IDs anywhere in metadata.csv."""
    counts = Counter({sample_id: len(rows) for sample_id, rows in rows_by_sample_id.items()})
    return sorted(sample_id for sample_id, count in counts.items() if count > 1)


def write_csv_report(report_rows: list[dict[str, str]]) -> None:
    """Save the verification report as CSV evidence."""
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
    report_rows: list[dict[str, str]],
    duplicate_sample_ids: list[str],
    passed: bool,
    participant_id: str,
    repetitions: int,
) -> None:
    """Save a concise Markdown verification report."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    duplicate_text = (
        "\n".join(f"- {sample_id}" for sample_id in duplicate_sample_ids)
        if duplicate_sample_ids
        else "- None"
    )
    failed_text = (
        "\n".join(
            f"- {row['sample_id']}: {row['issues']}" for row in failed_rows
        )
        if failed_rows
        else "- None"
    )

    content = f"""# Sprint 2.3 Trial Dataset Check

## Participant
{participant_id}

## Expected Scope
- Trial labels: {len(TRIAL_LABELS)}
- Repetitions per label: {repetitions}
- Expected videos: {len(TRIAL_LABELS) * repetitions}

## Result
{"PASS" if passed else "FAIL"}

## Failed Or Missing Items
{failed_text}

## Duplicate Metadata Sample IDs
{duplicate_text}

## Report Files
- CSV report: {CSV_REPORT_PATH.as_posix()}
- Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}
"""
    MARKDOWN_REPORT_PATH.write_text(content, encoding="utf-8")


def print_summary(
    report_rows: list[dict[str, str]],
    duplicate_sample_ids: list[str],
    passed: bool,
    participant_id: str,
    repetitions: int,
) -> None:
    """Print the verification result for terminal evidence."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.3 Trial Dataset Verification Summary")
    print("----------------------------------------------")
    print(f"participant: {participant_id}")
    print(f"trial labels: {len(TRIAL_LABELS)}")
    print(f"repetitions per label: {repetitions}")
    print(f"expected videos: {len(TRIAL_LABELS) * repetitions}")
    print(f"failed or missing items: {len(failed_rows)}")
    print(f"duplicate sample_id rows: {len(duplicate_sample_ids)}")
    print(f"CSV report: {CSV_REPORT_PATH.as_posix()}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}")

    if passed:
        print("Sprint 2.3 trial dataset verification passed.")
    else:
        print("Sprint 2.3 trial dataset verification failed.")
        for row in failed_rows[:20]:
            print(f"- {row['sample_id']}: {row['issues']}")
        if duplicate_sample_ids:
            print("Duplicate sample_id rows:")
            for sample_id in duplicate_sample_ids[:20]:
                print(f"- {sample_id}")


def main() -> int:
    """Verify all expected Sprint 2.3 trial videos and metadata rows."""
    args = parse_args()
    rows_by_sample_id, metadata_errors = read_metadata_rows()
    report_rows = build_report_rows(
        args.participant,
        args.repetitions,
        rows_by_sample_id,
        metadata_errors,
    )
    duplicate_sample_ids = find_duplicate_sample_ids(rows_by_sample_id)
    passed = all(row["passed"] == "yes" for row in report_rows) and not duplicate_sample_ids

    write_csv_report(report_rows)
    write_markdown_report(
        report_rows,
        duplicate_sample_ids,
        passed,
        args.participant,
        args.repetitions,
    )
    print_summary(report_rows, duplicate_sample_ids, passed, args.participant, args.repetitions)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Safely prepare the Sprint 2.8 rework for digit 7 and replacement payment."""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from pathlib import Path

from full_collection_config import FULL_DATASET_PARTICIPANT, FULL_DATASET_REPETITIONS


ML_DIR = Path("ml")
RAW_VIDEO_DIR = ML_DIR / "data_raw" / "videos"
METADATA_PATH = ML_DIR / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
BACKUP_DIR = EVIDENCE_DIR / "sprint_2_8_rework_backup"
REPORT_PATH = EVIDENCE_DIR / "sprint_2_8_rework_report.md"

REWORK_DIGIT_LABEL = "7"
REMOVED_LABEL = "receipt"
REPLACEMENT_LABEL = "payment"
REWORK_PARTICIPANT = FULL_DATASET_PARTICIPANT

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


@dataclass(frozen=True)
class ReworkPlan:
    """Describe exactly which existing Sprint 2.8 artifacts are in rework scope."""

    digit_video_paths: list[Path]
    receipt_video_paths: list[Path]
    digit_metadata_rows: list[dict[str, str]]
    receipt_metadata_rows: list[dict[str, str]]
    retained_metadata_rows: list[dict[str, str]]


def parse_args() -> argparse.Namespace:
    """Parse safe inspection mode or explicit apply mode."""
    parser = argparse.ArgumentParser(
        description="Back up and prepare the Sprint 2.8 digit 7/payment rework."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print planned changes only.")
    mode.add_argument("--apply", action="store_true", help="Back up files and clean only rework metadata rows.")
    return parser.parse_args()


def build_sample_id(label: str, repetition: int) -> str:
    """Build a P02 sample ID using the established collection convention."""
    return f"{REWORK_PARTICIPANT}_{label}_R{repetition:02d}"


def digit_video_paths() -> list[Path]:
    """Return only the ten digit-7 video paths permitted for this rework."""
    return [
        RAW_VIDEO_DIR / REWORK_DIGIT_LABEL / f"{build_sample_id(REWORK_DIGIT_LABEL, repetition)}.mp4"
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1)
        if (RAW_VIDEO_DIR / REWORK_DIGIT_LABEL / f"{build_sample_id(REWORK_DIGIT_LABEL, repetition)}.mp4").exists()
    ]


def receipt_video_paths() -> list[Path]:
    """Return only P02 receipt videos; other participants remain untouched."""
    receipt_dir = RAW_VIDEO_DIR / REMOVED_LABEL
    if not receipt_dir.exists():
        return []
    return sorted(receipt_dir.glob(f"{REWORK_PARTICIPANT}_{REMOVED_LABEL}_R*.mp4"))


def read_metadata_rows() -> list[dict[str, str]]:
    """Read metadata without modifying it and validate the project header contract."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {METADATA_PATH.as_posix()}")
    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
        return list(reader)


def is_digit_rework_row(row: dict[str, str]) -> bool:
    """Limit digit cleanup to P02 7 repetitions R01 through R10 only."""
    if row.get("participant_id") != REWORK_PARTICIPANT or row.get("label") != REWORK_DIGIT_LABEL:
        return False
    try:
        repetition = int(row.get("repetition", ""))
    except ValueError:
        return False
    return 1 <= repetition <= FULL_DATASET_REPETITIONS


def is_receipt_rework_row(row: dict[str, str]) -> bool:
    """Limit receipt cleanup to P02 metadata rows only."""
    return (
        row.get("participant_id") == REWORK_PARTICIPANT
        and row.get("label") == REMOVED_LABEL
    )


def build_rework_plan() -> ReworkPlan:
    """Identify all affected artifacts before any backup or mutation occurs."""
    metadata_rows = read_metadata_rows()
    digit_rows = [row for row in metadata_rows if is_digit_rework_row(row)]
    receipt_rows = [row for row in metadata_rows if is_receipt_rework_row(row)]
    retained_rows = [
        row
        for row in metadata_rows
        if not is_digit_rework_row(row) and not is_receipt_rework_row(row)
    ]
    return ReworkPlan(
        digit_video_paths=digit_video_paths(),
        receipt_video_paths=receipt_video_paths(),
        digit_metadata_rows=digit_rows,
        receipt_metadata_rows=receipt_rows,
        retained_metadata_rows=retained_rows,
    )


def unique_backup_path(directory: Path, filename: str) -> Path:
    """Avoid overwriting an earlier backup if --apply is run more than once."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    index = 1
    while True:
        candidate = directory / f"{stem}_{index:02d}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def move_to_backup(source: Path, backup_directory: Path) -> Path:
    """Move one raw video to its evidence backup without overwriting prior backups."""
    backup_directory.mkdir(parents=True, exist_ok=True)
    destination = unique_backup_path(backup_directory, source.name)
    shutil.move(str(source), str(destination))
    return destination


def write_metadata_rows(rows: list[dict[str, str]]) -> None:
    """Rewrite metadata only after its original state has been backed up."""
    with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
        writer = csv.DictWriter(metadata_file, fieldnames=METADATA_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_path_list(paths: list[Path]) -> str:
    """Format a path list clearly for the rework report."""
    return "\n".join(f"- {path.as_posix()}" for path in paths) if paths else "- None"


def markdown_metadata_list(rows: list[dict[str, str]]) -> str:
    """Format metadata sample IDs clearly for the rework report."""
    return "\n".join(f"- {row['sample_id']}" for row in rows) if rows else "- None"


def write_report(
    plan: ReworkPlan,
    mode: str,
    metadata_backup_path: Path | None,
    moved_digit_paths: list[Path],
    moved_receipt_paths: list[Path],
) -> None:
    """Write an evidence report for dry-run planning or applied cleanup."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    action_text = (
        "No files or metadata rows were changed."
        if mode == "dry-run"
        else "Backups were created before the scoped videos were moved and metadata rows were removed."
    )
    content = f"""# Sprint 2.8 Rework Report

## Mode
{mode}

## Scope
- Redo label: {REWORK_DIGIT_LABEL}, repetitions R01-R10.
- Remove label: {REMOVED_LABEL}.
- Replacement label: {REPLACEMENT_LABEL}, repetitions R01-R10.
- Participant: {REWORK_PARTICIPANT}.

## Planned Or Applied Actions
{action_text}

## Existing Digit 7 Videos In Scope
{markdown_path_list(plan.digit_video_paths)}

## Existing Receipt Videos In Scope
{markdown_path_list(plan.receipt_video_paths)}

## Digit 7 Metadata Rows In Scope
{markdown_metadata_list(plan.digit_metadata_rows)}

## Receipt Metadata Rows In Scope
{markdown_metadata_list(plan.receipt_metadata_rows)}

## Backup Result
- Metadata backup: {metadata_backup_path.as_posix() if metadata_backup_path else 'not created in dry-run'}
- Digit 7 videos moved: {len(moved_digit_paths)}
- Receipt videos moved: {len(moved_receipt_paths)}
- Metadata rows removed: {len(plan.digit_metadata_rows) + len(plan.receipt_metadata_rows) if mode == 'apply' else 0}
- Backup root: {BACKUP_DIR.as_posix()}

## Safety Boundary
Only P02 digit-7 rows R01-R10 and P02 receipt rows are eligible for cleanup. All other labels, participants, videos, and metadata rows remain untouched.
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def print_summary(plan: ReworkPlan, mode: str) -> None:
    """Print the cleanup plan without implying any recording has occurred."""
    print("Sprint 2.8 Rework Label Summary")
    print("--------------------------------")
    print(f"mode: {mode}")
    print(f"digit 7 videos in scope: {len(plan.digit_video_paths)}")
    print(f"receipt videos in scope: {len(plan.receipt_video_paths)}")
    print(f"digit 7 metadata rows in scope: {len(plan.digit_metadata_rows)}")
    print(f"receipt metadata rows in scope: {len(plan.receipt_metadata_rows)}")
    print(f"rework report: {REPORT_PATH.as_posix()}")
    if mode == "dry-run":
        print("Dry run completed. No videos were moved and metadata.csv was not changed.")
    else:
        print("Apply completed. Backups were created before scoped cleanup actions.")


def main() -> int:
    """Run a dry-run by default; apply changes only after an explicit --apply."""
    args = parse_args()
    mode = "apply" if args.apply else "dry-run"
    try:
        plan = build_rework_plan()
        metadata_backup_path: Path | None = None
        moved_digit_paths: list[Path] = []
        moved_receipt_paths: list[Path] = []

        if args.apply:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            metadata_backup_path = unique_backup_path(BACKUP_DIR, "metadata_before_rework.csv")
            shutil.copy2(METADATA_PATH, metadata_backup_path)

            for video_path in plan.digit_video_paths:
                moved_digit_paths.append(move_to_backup(video_path, BACKUP_DIR / "videos_7"))
            for video_path in plan.receipt_video_paths:
                moved_receipt_paths.append(
                    move_to_backup(video_path, BACKUP_DIR / "videos_receipt")
                )
            write_metadata_rows(plan.retained_metadata_rows)

        write_report(
            plan,
            mode,
            metadata_backup_path,
            moved_digit_paths,
            moved_receipt_paths,
        )
        print_summary(plan, mode)
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

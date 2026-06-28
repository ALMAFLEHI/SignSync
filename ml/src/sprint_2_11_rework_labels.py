"""Safely prepare Sprint 2.11 label rework without deleting local recordings."""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path

from sprint_2_11_intent_expansion_config import (
    EVIDENCE_DIR,
    METADATA_PATH,
    RAW_VIDEO_ROOT,
    REPLACED_EXPANSION_LABELS,
    REWORK_REDO_SAMPLES,
    SPRINT_2_11_PARTICIPANT,
)


BACKUP_ROOT = EVIDENCE_DIR / "sprint_2_11_rework_backup"
REPORT_PATH = EVIDENCE_DIR / "sprint_2_11_rework_report.md"
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
    """Choose a no-write dry-run or an explicit backup-and-clean apply run."""
    parser = argparse.ArgumentParser(
        description="Back up and clean only the Sprint 2.11 rework samples."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true")
    mode_group.add_argument("--apply", action="store_true")
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    return parser.parse_args()


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the existing SignSync sample ID format."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def timestamp() -> str:
    """Return a filesystem-friendly timestamp for backup files."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_metadata_rows() -> list[dict[str, str]]:
    """Load metadata rows and validate the expected header contract."""
    if not METADATA_PATH.exists():
        return []

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError("metadata.csv headers do not match the expected Sprint format.")
        return list(reader)


def row_is_rework_target(row: dict[str, str], participant_id: str) -> bool:
    """Return True only for rows that must leave the active Sprint 2.11 scope."""
    sample_id = row.get("sample_id", "")
    label = row.get("label", "")
    participant = row.get("participant_id", "")
    if participant != participant_id:
        return False

    redo_sample_ids = {
        build_sample_id(participant_id, label_name, repetition)
        for label_name, repetition in REWORK_REDO_SAMPLES
    }
    if sample_id in redo_sample_ids:
        return True
    return label in REPLACED_EXPANSION_LABELS


def planned_video_paths(participant_id: str) -> list[tuple[str, Path]]:
    """Build the old or incorrect video paths that may need to be moved aside."""
    paths: list[tuple[str, Path]] = []
    for label, repetition in REWORK_REDO_SAMPLES:
        sample_id = build_sample_id(participant_id, label, repetition)
        paths.append((label, RAW_VIDEO_ROOT / label / f"{sample_id}.mp4"))

    for label in REPLACED_EXPANSION_LABELS:
        label_dir = RAW_VIDEO_ROOT / label
        if label_dir.exists():
            paths.extend(
                (label, path)
                for path in sorted(label_dir.glob(f"{participant_id}_{label}_*.mp4"))
            )
    return paths


def unique_destination(path: Path) -> Path:
    """Avoid overwriting previous evidence backups if the script is rerun."""
    if not path.exists():
        return path
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not build a unique backup path for {path.as_posix()}.")


def copy_metadata_backup(run_id: str) -> Path | None:
    """Copy metadata.csv to evidence backup storage before any cleanup."""
    if not METADATA_PATH.exists():
        return None
    destination_dir = BACKUP_ROOT / "metadata"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"metadata_before_sprint_2_11_rework_{run_id}.csv"
    shutil.copy2(METADATA_PATH, destination)
    return destination


def move_video_to_backup(label: str, video_path: Path) -> Path:
    """Move one existing raw video into the evidence backup area."""
    destination_dir = BACKUP_ROOT / f"videos_{label}"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_destination(destination_dir / video_path.name)
    shutil.move(str(video_path), str(destination))
    return destination


def write_metadata_rows(rows: list[dict[str, str]]) -> None:
    """Rewrite metadata.csv with only targeted rows removed."""
    with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
        writer = csv.DictWriter(metadata_file, fieldnames=METADATA_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    participant_id: str,
    metadata_backup_path: Path | None,
    removed_rows: list[dict[str, str]],
    moved_videos: list[tuple[Path, Path]],
    missing_videos: list[Path],
) -> None:
    """Save a concise evidence report for the applied cleanup."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    removed_text = (
        "\n".join(f"- {row['sample_id']}" for row in removed_rows)
        if removed_rows
        else "- None"
    )
    moved_text = (
        "\n".join(
            f"- {source.as_posix()} -> {destination.as_posix()}"
            for source, destination in moved_videos
        )
        if moved_videos
        else "- None"
    )
    missing_text = (
        "\n".join(f"- {path.as_posix()}" for path in missing_videos)
        if missing_videos
        else "- None"
    )
    metadata_backup_text = (
        metadata_backup_path.as_posix()
        if metadata_backup_path
        else "metadata.csv was missing"
    )
    content = f"""# Sprint 2.11 Rework Cleanup Report

## Participant
{participant_id}

## Cleanup Scope
- Replaced labels removed from active scope: {', '.join(REPLACED_EXPANSION_LABELS)}
- Incorrect or partial samples prepared for redo: account_number R01, atm R01
- Permanent deletion performed: no

## Metadata Backup
{metadata_backup_text}

## Metadata Rows Removed
{removed_text}

## Videos Moved To Backup
{moved_text}

## Expected But Not Found
{missing_text}
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def print_plan(
    participant_id: str,
    removed_rows: list[dict[str, str]],
    video_paths: list[tuple[str, Path]],
    mode_name: str,
) -> None:
    """Print the cleanup plan in dry-run and the applied scope in apply mode."""
    print("Sprint 2.11 Rework Cleanup")
    print("--------------------------")
    print(f"mode: {mode_name}")
    print(f"participant: {participant_id}")
    print(f"backup root: {BACKUP_ROOT.as_posix()}")
    print(f"metadata backup: {METADATA_PATH.as_posix()}")
    print(f"metadata rows targeted: {len(removed_rows)}")
    for row in removed_rows:
        print(f"- metadata row: {row['sample_id']}")
    print(f"video files checked: {len(video_paths)}")
    for _, path in video_paths:
        status = "exists" if path.exists() else "not found"
        print(f"- {path.as_posix()} ({status})")


def main() -> int:
    """Run the requested safe Sprint 2.11 rework cleanup mode."""
    args = parse_args()
    rows = read_metadata_rows()
    removed_rows = [row for row in rows if row_is_rework_target(row, args.participant)]
    kept_rows = [row for row in rows if not row_is_rework_target(row, args.participant)]
    video_paths = planned_video_paths(args.participant)

    if args.dry_run:
        print_plan(args.participant, removed_rows, video_paths, "dry-run")
        print("No files were changed.")
        return 0

    print_plan(args.participant, removed_rows, video_paths, "apply")
    run_id = timestamp()
    metadata_backup_path = copy_metadata_backup(run_id)
    moved_videos: list[tuple[Path, Path]] = []
    missing_videos: list[Path] = []
    for label, video_path in video_paths:
        if video_path.exists():
            destination = move_video_to_backup(label, video_path)
            moved_videos.append((video_path, destination))
        else:
            missing_videos.append(video_path)

    if rows:
        write_metadata_rows(kept_rows)
    write_report(args.participant, metadata_backup_path, removed_rows, moved_videos, missing_videos)
    print(f"metadata rows removed: {len(removed_rows)}")
    print(f"videos moved to backup: {len(moved_videos)}")
    print(f"report path: {REPORT_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

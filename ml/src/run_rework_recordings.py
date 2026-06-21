"""Interactively record only Sprint 2.8 rework labels 7 and payment."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from full_collection_config import (
    FULL_DATASET_CAMERA_INDEX,
    FULL_DATASET_PARTICIPANT,
    FULL_DATASET_REPETITIONS,
    FULL_DATASET_REWORK_NOTES,
)


COLLECT_VIDEO_PATH = Path("ml") / "src" / "collect_video.py"
REWORK_LABELS = ("7", "payment")
REWORK_NOTES = FULL_DATASET_REWORK_NOTES


def parse_args() -> argparse.Namespace:
    """Parse manual rework-runner options."""
    parser = argparse.ArgumentParser(
        description="Run or dry-run Sprint 2.8 recording rework for 7 and payment."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=FULL_DATASET_CAMERA_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def build_collect_command(
    participant_id: str,
    label: str,
    repetition: int,
    camera_index: int,
    overwrite: bool,
    display_python: bool,
) -> list[str]:
    """Build a display or subprocess command for one explicit rework sample."""
    command = [
        "python" if display_python else sys.executable,
        COLLECT_VIDEO_PATH.as_posix(),
        "--participant",
        participant_id,
        "--label",
        label,
        "--repetition",
        str(repetition),
        "--camera-index",
        str(camera_index),
        "--notes",
        REWORK_NOTES,
    ]
    if overwrite:
        command.append("--overwrite")
    return command


def print_summary(attempted: int, skipped: int, completed: int, failed: int, participant_id: str) -> None:
    """Print the final status and the next safe verification command."""
    print()
    print("Sprint 2.8 Rework Recording Summary")
    print("------------------------------------")
    print(f"attempted recordings: {attempted}")
    print(f"skipped recordings: {skipped}")
    print(f"completed recordings: {completed}")
    print(f"failed recordings: {failed}")
    print(
        "next command: "
        f"python ml/src/check_full_collection_dataset.py --participant {participant_id}"
    )


def main() -> int:
    """Guide only the approved 20 recordings, never recording automatically in dry-run."""
    args = parse_args()
    attempted = 0
    skipped = 0
    completed = 0
    failed = 0

    for label in REWORK_LABELS:
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1):
            display_command = build_collect_command(
                args.participant,
                label,
                repetition,
                args.camera_index,
                args.overwrite,
                display_python=True,
            )
            if args.dry_run:
                attempted += 1
                print(subprocess.list2cmdline(display_command))
                continue

            choice = input(
                f"Prepare sign {label}, repetition R{repetition:02d}. "
                "Press Enter to record or type skip. "
            ).strip().lower()
            if choice == "skip":
                skipped += 1
                print(f"Skipped by user: {args.participant}_{label}_R{repetition:02d}")
                continue

            actual_command = build_collect_command(
                args.participant,
                label,
                repetition,
                args.camera_index,
                args.overwrite,
                display_python=False,
            )
            attempted += 1
            result = subprocess.run(actual_command, check=False)
            if result.returncode == 0:
                completed += 1
            else:
                failed += 1
                print(
                    "Recording failed and was not skipped: "
                    f"{args.participant}_{label}_R{repetition:02d}"
                )

    print_summary(attempted, skipped, completed, failed, args.participant)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

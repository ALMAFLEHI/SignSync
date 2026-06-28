"""Interactively record only the approved Sprint 2.11 rework samples."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sprint_2_11_intent_expansion_config import (
    EXPECTED_REWORK_RECORDINGS,
    REWORK_RECORDING_PLAN,
    SPRINT_2_11_CAMERA_INDEX,
    SPRINT_2_11_NOTES,
    SPRINT_2_11_PARTICIPANT,
)


COLLECT_VIDEO_PATH = Path("ml") / "src" / "collect_video.py"


def parse_args() -> argparse.Namespace:
    """Parse manual recording controls for the 22-sample rework scope."""
    parser = argparse.ArgumentParser(
        description="Run or dry-run the 22 Sprint 2.11 rework recordings."
    )
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=SPRINT_2_11_CAMERA_INDEX)
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
    """Build a displayed command or current-interpreter subprocess command."""
    python_command = "python" if display_python else sys.executable
    command = [
        python_command,
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
        SPRINT_2_11_NOTES,
    ]
    if overwrite:
        command.append("--overwrite")
    return command


def print_summary(attempted: int, skipped: int, completed: int, failed: int, participant_id: str) -> None:
    """Print the rework outcome and the next verification command."""
    print()
    print("Sprint 2.11 Rework Collection Summary")
    print("-------------------------------------")
    print(f"planned recordings: {EXPECTED_REWORK_RECORDINGS}")
    print(f"attempted recordings: {attempted}")
    print(f"skipped recordings: {skipped}")
    print(f"completed recordings: {completed}")
    print(f"failed recordings: {failed}")
    print(
        "next command: "
        f"python ml/src/check_sprint_2_11_collection.py --participant {participant_id}"
    )


def main() -> int:
    """Print or run the prompted 22-recording rework workflow."""
    args = parse_args()
    attempted = 0
    skipped = 0
    completed = 0
    failed = 0

    for label, repetition in REWORK_RECORDING_PLAN:
        displayed_command = build_collect_command(
            args.participant,
            label,
            repetition,
            args.camera_index,
            args.overwrite,
            display_python=True,
        )
        if args.dry_run:
            attempted += 1
            print(subprocess.list2cmdline(displayed_command))
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
            print(f"Recording failed: {args.participant}_{label}_R{repetition:02d}")

    print_summary(attempted, skipped, completed, failed, args.participant)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

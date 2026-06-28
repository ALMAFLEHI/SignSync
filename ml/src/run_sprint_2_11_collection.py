"""Interactively guide manual Sprint 2.11 collection for current expansion labels."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sprint_2_11_intent_expansion_config import (
    EXPANSION_LABELS,
    SPRINT_2_11_CAMERA_INDEX,
    SPRINT_2_11_NOTES,
    SPRINT_2_11_PARTICIPANT,
    SPRINT_2_11_REPETITIONS,
)


COLLECT_VIDEO_PATH = Path("ml") / "src" / "collect_video.py"


def parse_args() -> argparse.Namespace:
    """Parse manual recording controls for the fixed Sprint 2.11 expansion scope."""
    parser = argparse.ArgumentParser(
        description="Run or dry-run the current Sprint 2.11 30-label collection."
    )
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=SPRINT_2_11_CAMERA_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--start-label", default=None)
    parser.add_argument("--start-repetition", type=int, default=1)
    return parser.parse_args()


def selected_labels(start_label: str | None) -> list[str]:
    """Return expansion labels from an optional valid resume label onward."""
    if start_label is None:
        return EXPANSION_LABELS
    if start_label not in EXPANSION_LABELS:
        raise ValueError(
            "--start-label must be a Sprint 2.11 expansion label: "
            f"{', '.join(EXPANSION_LABELS)}"
        )
    return EXPANSION_LABELS[EXPANSION_LABELS.index(start_label) :]


def selected_repetitions(label_index: int, start_repetition: int) -> range:
    """Apply the resume repetition only to the first selected label."""
    first_repetition = start_repetition if label_index == 0 else 1
    return range(first_repetition, SPRINT_2_11_REPETITIONS + 1)


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
    """Print the collection outcome and the required next verification command."""
    print()
    print("Sprint 2.11 Collection Summary")
    print("-----------------------------")
    print(f"attempted recordings: {attempted}")
    print(f"skipped recordings: {skipped}")
    print(f"completed recordings: {completed}")
    print(f"failed recordings: {failed}")
    print(
        "next command: "
        f"python ml/src/check_sprint_2_11_collection.py --participant {participant_id}"
    )


def main() -> int:
    """Print or run the prompted 300-recording workflow without hidden label changes."""
    args = parse_args()
    if not 1 <= args.start_repetition <= SPRINT_2_11_REPETITIONS:
        print(
            "Error: --start-repetition must be between 1 and "
            f"{SPRINT_2_11_REPETITIONS}."
        )
        return 1
    try:
        labels = selected_labels(args.start_label)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    attempted = 0
    skipped = 0
    completed = 0
    failed = 0
    for label_index, label in enumerate(labels):
        for repetition in selected_repetitions(label_index, args.start_repetition):
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

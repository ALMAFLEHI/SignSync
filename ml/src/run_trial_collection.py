"""Interactive Sprint 2.3 trial dataset collection runner."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from trial_config import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_FPS,
    DEFAULT_FRAMES,
    DEFAULT_HEIGHT,
    DEFAULT_NOTES,
    DEFAULT_PARTICIPANT_ID,
    DEFAULT_REPETITIONS,
    DEFAULT_WIDTH,
    TRIAL_LABELS,
)


COLLECT_VIDEO_PATH = Path("ml") / "src" / "collect_video.py"
RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"


def parse_args() -> argparse.Namespace:
    """Parse options for the interactive trial collection workflow."""
    parser = argparse.ArgumentParser(
        description="Run or dry-run Sprint 2.3 trial dataset collection."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--camera-index", type=int, default=DEFAULT_CAMERA_INDEX)
    parser.add_argument("--start-label", default=None)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--skip-existing", dest="skip_existing", action="store_true", default=True)
    parser.add_argument("--no-skip-existing", dest="skip_existing", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def selected_labels(start_label: str | None) -> list[str]:
    """Return trial labels from the optional start label onward."""
    if start_label is None:
        return TRIAL_LABELS

    if start_label not in TRIAL_LABELS:
        raise ValueError(
            f"start-label must be one of the trial labels: {', '.join(TRIAL_LABELS)}"
        )

    start_index = TRIAL_LABELS.index(start_label)
    return TRIAL_LABELS[start_index:]


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the same sample ID format used by collect_video.py."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_video_path(participant_id: str, label: str, repetition: int) -> Path:
    """Return the expected raw video path for one trial sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return RAW_VIDEO_DIR / label / f"{sample_id}.mp4"


def build_collect_command(
    participant_id: str,
    label: str,
    repetition: int,
    camera_index: int,
    overwrite: bool,
    display_python: bool,
) -> list[str]:
    """Build the collect_video.py subprocess command."""
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
        "--frames",
        str(DEFAULT_FRAMES),
        "--fps",
        str(DEFAULT_FPS),
        "--width",
        str(DEFAULT_WIDTH),
        "--height",
        str(DEFAULT_HEIGHT),
        "--notes",
        DEFAULT_NOTES,
    ]

    if overwrite:
        command.append("--overwrite")

    return command


def print_summary(attempted: int, skipped: int, completed: int, failed: int, participant_id: str) -> None:
    """Print the final collection run summary."""
    print()
    print("Sprint 2.3 Trial Collection Summary")
    print("------------------------------------")
    print(f"number of attempted recordings: {attempted}")
    print(f"number skipped: {skipped}")
    print(f"number completed: {completed}")
    print(f"number failed: {failed}")
    print(
        "next command: "
        f"python ml/src/check_trial_dataset.py --participant {participant_id}"
    )


def main() -> int:
    """Run the controlled trial collection workflow or dry-run commands only."""
    args = parse_args()

    try:
        labels = selected_labels(args.start_label)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    attempted = 0
    skipped = 0
    completed = 0
    failed = 0

    for label in labels:
        for repetition in range(1, args.repetitions + 1):
            repetition_label = f"R{repetition:02d}"
            video_path = expected_video_path(args.participant, label, repetition)
            display_command = build_collect_command(
                args.participant,
                label,
                repetition,
                args.camera_index,
                args.overwrite,
                display_python=True,
            )
            display_command_text = subprocess.list2cmdline(display_command)

            if video_path.exists() and args.skip_existing and not args.overwrite:
                skipped += 1
                print(f"Skipped existing sample: {video_path.as_posix()}")
                continue

            if args.dry_run:
                attempted += 1
                print(display_command_text)
                continue

            prompt = (
                f"Prepare sign {label}, repetition {repetition_label}. "
                "Press Enter to record or type skip. "
            )
            user_choice = input(prompt).strip().lower()
            if user_choice == "skip":
                skipped += 1
                print(f"Skipped by user: {args.participant}_{label}_{repetition_label}")
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

    print_summary(attempted, skipped, completed, failed, args.participant)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Interactively guide Sprint 2.8 remaining-label collection without hidden skips."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from full_collection_config import (
    EXPECTED_FULL_COLLECTION_VIDEOS,
    FULL_DATASET_CAMERA_INDEX,
    FULL_DATASET_NOTES,
    FULL_DATASET_PARTICIPANT,
    FULL_DATASET_REPETITIONS,
    REMAINING_LABELS,
)


COLLECT_VIDEO_PATH = Path("ml") / "src" / "collect_video.py"
RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"


def parse_args() -> argparse.Namespace:
    """Parse interactive-runner options while preserving the 10-repeat scope."""
    parser = argparse.ArgumentParser(
        description="Run or dry-run the Sprint 2.8 remaining-label collection workflow."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=FULL_DATASET_CAMERA_INDEX)
    parser.add_argument("--start-label", default=None)
    parser.add_argument("--start-repetition", type=int, default=1)
    parser.add_argument("--skip-existing", dest="skip_existing", action="store_true", default=True)
    parser.add_argument("--no-skip-existing", dest="skip_existing", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def selected_labels(start_label: str | None) -> list[str]:
    """Return remaining labels from an optional resume label onward."""
    if start_label is None:
        return REMAINING_LABELS
    if start_label not in REMAINING_LABELS:
        raise ValueError(
            "--start-label must be a remaining Sprint 2.8 label: "
            f"{', '.join(REMAINING_LABELS)}"
        )
    return REMAINING_LABELS[REMAINING_LABELS.index(start_label) :]


def selected_repetitions(label_index: int, start_repetition: int) -> range:
    """Resume at the requested repetition for the first selected label only."""
    first_repetition = start_repetition if label_index == 0 else 1
    return range(first_repetition, FULL_DATASET_REPETITIONS + 1)


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Use the same stable sample ID convention as collect_video.py."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_video_path(participant_id: str, label: str, repetition: int) -> Path:
    """Return the raw-video target path for one expected sample."""
    return RAW_VIDEO_DIR / label / f"{build_sample_id(participant_id, label, repetition)}.mp4"


def build_collect_command(
    participant_id: str,
    label: str,
    repetition: int,
    camera_index: int,
    overwrite: bool,
    display_python: bool,
) -> list[str]:
    """Build either a displayed command or the current-interpreter subprocess command."""
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
        FULL_DATASET_NOTES,
    ]
    if overwrite:
        command.append("--overwrite")
    return command


def print_summary(
    attempted: int, skipped: int, completed: int, failed: int, participant_id: str
) -> None:
    """Print the final recording-flow summary requested for this sprint."""
    print()
    print("Sprint 2.8 Full Collection Summary")
    print("-----------------------------------")
    print(f"attempted recordings: {attempted}")
    print(f"skipped recordings: {skipped}")
    print(f"completed recordings: {completed}")
    print(f"failed recordings: {failed}")
    print(
        "next command: "
        f"python ml/src/check_full_collection_dataset.py --participant {participant_id}"
    )


def main() -> int:
    """Run the manual workflow, or print its commands in dry-run mode only."""
    args = parse_args()
    if not 1 <= args.start_repetition <= FULL_DATASET_REPETITIONS:
        print(
            "Error: --start-repetition must be between 1 and "
            f"{FULL_DATASET_REPETITIONS}."
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

            video_path = expected_video_path(args.participant, label, repetition)
            if video_path.exists() and args.skip_existing and not args.overwrite:
                skipped += 1
                print(f"Skipped existing sample: {video_path.as_posix()}")
                continue

            repetition_label = f"R{repetition:02d}"
            user_choice = input(
                f"Prepare sign {label}, repetition {repetition_label}. "
                "Press Enter to record or type skip. "
            ).strip().lower()
            if user_choice == "skip":
                skipped += 1
                print(f"Skipped by user: {build_sample_id(args.participant, label, repetition)}")
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
                    f"{build_sample_id(args.participant, label, repetition)}"
                )

    print_summary(attempted, skipped, completed, failed, args.participant)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

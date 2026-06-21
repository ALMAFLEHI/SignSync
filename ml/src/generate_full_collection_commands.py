"""Generate manual Sprint 2.8 collection commands for the remaining labels."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from full_collection_config import (
    EXPECTED_FULL_COLLECTION_VIDEOS,
    FULL_DATASET_CAMERA_INDEX,
    FULL_DATASET_NOTES,
    FULL_DATASET_PARTICIPANT,
    FULL_DATASET_REPETITIONS,
    REMAINING_LABELS,
)


EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
POWERSHELL_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_8_full_collection_commands.ps1"
MARKDOWN_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_8_full_collection_commands.md"


def parse_args() -> argparse.Namespace:
    """Parse allowed command-generation overrides without changing collection scope."""
    parser = argparse.ArgumentParser(
        description="Generate Sprint 2.8 manual recording commands for 45 remaining labels."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=FULL_DATASET_CAMERA_INDEX)
    return parser.parse_args()


def build_command(
    participant_id: str, label: str, repetition: int, camera_index: int
) -> list[str]:
    """Build one collect_video.py command without launching the webcam."""
    return [
        "python",
        "ml/src/collect_video.py",
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


def build_commands(participant_id: str, camera_index: int) -> list[str]:
    """Return all 450 stable-order commands for manual recording."""
    commands: list[str] = []
    for label in REMAINING_LABELS:
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1):
            command = build_command(participant_id, label, repetition, camera_index)
            commands.append(subprocess.list2cmdline(command))
    return commands


def write_powershell_commands(commands: list[str]) -> None:
    """Write a PowerShell command list without executing any recording command."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    content = [
        "# SignSync Phase 2 Sprint 2.8 remaining-label recording commands",
        "# Run one command at a time from the project root when ready to record.",
        "# Do not run this file until the collection session is prepared.",
        "",
        *commands,
        "",
    ]
    POWERSHELL_COMMANDS_PATH.write_text("\n".join(content), encoding="utf-8")


def write_markdown_commands(commands: list[str]) -> None:
    """Write a Markdown evidence list of the same manual recording commands."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    command_lines = "\n".join(commands)
    content = f"""# Sprint 2.8 Full Dataset Collection Commands

These are manual collection commands for the 45 labels not present in the Sprint 2.3 trial set. Confirm the camera is ready on index 1 before running an individual command.

```powershell
{command_lines}
```
"""
    MARKDOWN_COMMANDS_PATH.write_text(content, encoding="utf-8")


def print_summary(commands: list[str]) -> None:
    """Print the requested generation summary for FYP evidence."""
    print("Sprint 2.8 Full Collection Command Generation Summary")
    print("----------------------------------------------------")
    print(f"total remaining labels: {len(REMAINING_LABELS)}")
    print(f"repetitions per label: {FULL_DATASET_REPETITIONS}")
    print(f"total commands: {len(commands)}")
    print(f"expected commands: {EXPECTED_FULL_COLLECTION_VIDEOS}")
    print(f"PowerShell commands path: {POWERSHELL_COMMANDS_PATH.as_posix()}")
    print(f"Markdown commands path: {MARKDOWN_COMMANDS_PATH.as_posix()}")


def main() -> int:
    """Generate the requested command files only; no recording is started here."""
    args = parse_args()
    commands = build_commands(args.participant, args.camera_index)
    if len(commands) != EXPECTED_FULL_COLLECTION_VIDEOS:
        raise ValueError(
            f"Expected {EXPECTED_FULL_COLLECTION_VIDEOS} commands, found {len(commands)}."
        )
    write_powershell_commands(commands)
    write_markdown_commands(commands)
    print_summary(commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

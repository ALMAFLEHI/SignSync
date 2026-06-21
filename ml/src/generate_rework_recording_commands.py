"""Generate the 20 manual Sprint 2.8 rework commands for 7 and payment."""

from __future__ import annotations

import subprocess
from pathlib import Path

from full_collection_config import (
    FULL_DATASET_CAMERA_INDEX,
    FULL_DATASET_PARTICIPANT,
    FULL_DATASET_REPETITIONS,
    FULL_DATASET_REWORK_NOTES,
)


EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
POWERSHELL_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_8_rework_recording_commands.ps1"
MARKDOWN_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_8_rework_recording_commands.md"
REWORK_LABELS = ("7", "payment")
REWORK_NOTES = FULL_DATASET_REWORK_NOTES


def build_command(label: str, repetition: int) -> list[str]:
    """Build one rework recording command without launching the camera."""
    return [
        "python",
        "ml/src/collect_video.py",
        "--participant",
        FULL_DATASET_PARTICIPANT,
        "--label",
        label,
        "--repetition",
        str(repetition),
        "--camera-index",
        str(FULL_DATASET_CAMERA_INDEX),
        "--notes",
        REWORK_NOTES,
    ]


def build_commands() -> list[str]:
    """Build ten commands for digit 7 and ten commands for payment."""
    return [
        subprocess.list2cmdline(build_command(label, repetition))
        for label in REWORK_LABELS
        for repetition in range(1, FULL_DATASET_REPETITIONS + 1)
    ]


def write_command_files(commands: list[str]) -> None:
    """Write PowerShell and Markdown command files without executing them."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    POWERSHELL_COMMANDS_PATH.write_text(
        "\n".join(
            [
                "# SignSync Phase 2 Sprint 2.8 rework commands",
                "# Record only digit 7 and payment after cleanup is applied.",
                "",
                *commands,
                "",
            ]
        ),
        encoding="utf-8",
    )
    MARKDOWN_COMMANDS_PATH.write_text(
        "# Sprint 2.8 Rework Recording Commands\n\n"
        "These 20 commands re-record digit `7` and collect replacement label `payment`.\n\n"
        "```powershell\n"
        + "\n".join(commands)
        + "\n```\n",
        encoding="utf-8",
    )


def main() -> int:
    """Generate the 20 rework commands and print a concise evidence summary."""
    commands = build_commands()
    expected_commands = len(REWORK_LABELS) * FULL_DATASET_REPETITIONS
    if len(commands) != expected_commands:
        raise ValueError(f"Expected {expected_commands} rework commands, found {len(commands)}.")
    write_command_files(commands)
    print("Sprint 2.8 Rework Command Generation Summary")
    print("--------------------------------------------")
    print(f"labels: {', '.join(REWORK_LABELS)}")
    print(f"repetitions per label: {FULL_DATASET_REPETITIONS}")
    print(f"total commands: {len(commands)}")
    print(f"PowerShell commands path: {POWERSHELL_COMMANDS_PATH.as_posix()}")
    print(f"Markdown commands path: {MARKDOWN_COMMANDS_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

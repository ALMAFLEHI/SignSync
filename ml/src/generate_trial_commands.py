"""Generate Sprint 2.3 trial dataset recording commands."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from trial_config import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_NOTES,
    DEFAULT_PARTICIPANT_ID,
    DEFAULT_REPETITIONS,
    TRIAL_LABELS,
)


EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
POWERSHELL_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_3_trial_commands.ps1"
MARKDOWN_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_3_trial_commands.md"


def parse_args() -> argparse.Namespace:
    """Parse optional overrides for the generated trial commands."""
    parser = argparse.ArgumentParser(
        description="Generate Sprint 2.3 trial recording commands."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--camera-index", type=int, default=DEFAULT_CAMERA_INDEX)
    return parser.parse_args()


def build_command(participant_id: str, label: str, repetition: int, camera_index: int) -> list[str]:
    """Build one collect_video.py command as a list for safe formatting."""
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
        DEFAULT_NOTES,
    ]


def build_commands(participant_id: str, camera_index: int) -> list[str]:
    """Generate one command for every trial label and repetition."""
    commands: list[str] = []
    for label in TRIAL_LABELS:
        for repetition in range(1, DEFAULT_REPETITIONS + 1):
            command = build_command(participant_id, label, repetition, camera_index)
            commands.append(subprocess.list2cmdline(command))
    return commands


def write_powershell_commands(commands: list[str]) -> None:
    """Save the generated commands to a PowerShell script file."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    content = [
        "# SignSync Phase 2 Sprint 2.3 trial dataset commands",
        "# Run from the project root. Each command records one sample.",
        "",
        *commands,
        "",
    ]
    POWERSHELL_COMMANDS_PATH.write_text("\n".join(content), encoding="utf-8")


def write_markdown_commands(commands: list[str]) -> None:
    """Save the generated commands to a Markdown evidence file."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    command_lines = "\n".join(commands)
    content = f"""# Sprint 2.3 Trial Recording Commands

Run these commands from the project root after confirming the camera works with `--camera-index 1`.

```powershell
{command_lines}
```
"""
    MARKDOWN_COMMANDS_PATH.write_text(content, encoding="utf-8")


def print_summary(commands: list[str]) -> None:
    """Print a concise generation summary for terminal evidence."""
    print("Sprint 2.3 Trial Command Generation Summary")
    print("--------------------------------------------")
    print(f"total labels: {len(TRIAL_LABELS)}")
    print(f"repetitions per label: {DEFAULT_REPETITIONS}")
    print(f"total commands: {len(commands)}")
    print(f"PowerShell commands path: {POWERSHELL_COMMANDS_PATH.as_posix()}")
    print(f"Markdown commands path: {MARKDOWN_COMMANDS_PATH.as_posix()}")


def main() -> int:
    """Generate and save all Sprint 2.3 trial recording commands."""
    args = parse_args()
    commands = build_commands(args.participant, args.camera_index)
    write_powershell_commands(commands)
    write_markdown_commands(commands)
    print_summary(commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

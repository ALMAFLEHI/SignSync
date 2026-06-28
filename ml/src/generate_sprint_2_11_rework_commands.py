"""Generate the 22 manual recording commands for the Sprint 2.11 rework."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from sprint_2_11_intent_expansion_config import (
    EVIDENCE_DIR,
    EXPECTED_REWORK_RECORDINGS,
    REWORK_RECORDING_PLAN,
    SPRINT_2_11_CAMERA_INDEX,
    SPRINT_2_11_NOTES,
    SPRINT_2_11_PARTICIPANT,
)


POWERSHELL_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_11_rework_recording_commands.ps1"
MARKDOWN_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_11_rework_recording_commands.md"


def parse_args() -> argparse.Namespace:
    """Allow participant and camera overrides while keeping the 22-sample scope fixed."""
    parser = argparse.ArgumentParser(
        description="Generate commands for the 22 Sprint 2.11 rework recordings."
    )
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=SPRINT_2_11_CAMERA_INDEX)
    return parser.parse_args()


def build_command(participant_id: str, label: str, repetition: int, camera_index: int) -> list[str]:
    """Build one collect_video.py command without opening the webcam."""
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
        SPRINT_2_11_NOTES,
    ]


def build_commands(participant_id: str, camera_index: int) -> list[str]:
    """Return exactly the 22 rework recording commands in a stable order."""
    return [
        subprocess.list2cmdline(build_command(participant_id, label, repetition, camera_index))
        for label, repetition in REWORK_RECORDING_PLAN
    ]


def write_command_files(commands: list[str]) -> None:
    """Save PowerShell and Markdown evidence files for the rework recording plan."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    powershell_content = [
        "# SignSync Phase 2 Sprint 2.11 rework recording commands",
        "# Run after applying the safe rework cleanup.",
        "# These commands cover document, signature, account_number R01, and atm R01 only.",
        "",
        *commands,
        "",
    ]
    POWERSHELL_COMMANDS_PATH.write_text("\n".join(powershell_content), encoding="utf-8")

    command_lines = "\n".join(commands)
    markdown_content = f"""# Sprint 2.11 Rework Recording Commands

These {len(commands)} commands cover only the approved Sprint 2.11 rework recordings:

- document R01-R10
- signature R01-R10
- account_number R01
- atm R01

Run them manually from the project root after applying the safe cleanup.

```powershell
{command_lines}
```
"""
    MARKDOWN_COMMANDS_PATH.write_text(markdown_content, encoding="utf-8")


def main() -> int:
    """Generate the rework command files and print a compact summary."""
    args = parse_args()
    commands = build_commands(args.participant, args.camera_index)
    if len(commands) != EXPECTED_REWORK_RECORDINGS:
        raise ValueError(
            f"Expected {EXPECTED_REWORK_RECORDINGS} commands, found {len(commands)}."
        )
    write_command_files(commands)
    print("Sprint 2.11 Rework Command Generation Summary")
    print("---------------------------------------------")
    print(f"commands generated: {len(commands)}")
    print(f"participant: {args.participant}")
    print(f"camera index: {args.camera_index}")
    print(f"PowerShell commands path: {POWERSHELL_COMMANDS_PATH.as_posix()}")
    print(f"Markdown commands path: {MARKDOWN_COMMANDS_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

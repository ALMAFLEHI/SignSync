"""Generate, but never run, current Sprint 2.11 recording commands."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from sprint_2_11_intent_expansion_config import (
    EXPECTED_NEW_LABELS,
    EXPECTED_NEW_VIDEOS,
    EXPANSION_LABELS,
    SPRINT_2_11_CAMERA_INDEX,
    SPRINT_2_11_NOTES,
    SPRINT_2_11_PARTICIPANT,
    SPRINT_2_11_REPETITIONS,
)


EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
POWERSHELL_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_11_recording_commands.ps1"
MARKDOWN_COMMANDS_PATH = EVIDENCE_DIR / "sprint_2_11_recording_commands.md"


def parse_args() -> argparse.Namespace:
    """Allow participant and camera overrides without changing the 300-video scope."""
    parser = argparse.ArgumentParser(
        description="Generate commands for the current 30-label Sprint 2.11 scope."
    )
    parser.add_argument("--participant", default=SPRINT_2_11_PARTICIPANT)
    parser.add_argument("--camera-index", type=int, default=SPRINT_2_11_CAMERA_INDEX)
    return parser.parse_args()


def build_command(
    participant_id: str, label: str, repetition: int, camera_index: int
) -> list[str]:
    """Build one manual collect_video.py command without launching the camera."""
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
    """Return exactly 300 stable-order recording commands for the expansion labels."""
    return [
        subprocess.list2cmdline(build_command(participant_id, label, repetition, camera_index))
        for label in EXPANSION_LABELS
        for repetition in range(1, SPRINT_2_11_REPETITIONS + 1)
    ]


def write_command_files(commands: list[str]) -> None:
    """Save PowerShell and Markdown command lists without executing any command."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    powershell_content = [
        "# SignSync Phase 2 Sprint 2.11 banking intent expansion commands",
        "# Run one command at a time from the project root after confirming each gesture.",
        "# This file records raw video only when a listed command is manually run.",
        "",
        *commands,
        "",
    ]
    POWERSHELL_COMMANDS_PATH.write_text("\n".join(powershell_content), encoding="utf-8")

    command_lines = "\n".join(commands)
    markdown_content = f"""# Sprint 2.11 Banking Intent Expansion Recording Commands

These {len(commands)} commands cover only the 30 new Sprint 2.11 banking labels. They do not include any completed V1 labels. Run commands manually from the project root only when ready to record with camera index 1.

```powershell
{command_lines}
```
"""
    MARKDOWN_COMMANDS_PATH.write_text(markdown_content, encoding="utf-8")


def main() -> int:
    """Generate the requested evidence files and print their small summary."""
    args = parse_args()
    commands = build_commands(args.participant, args.camera_index)
    if len(commands) != EXPECTED_NEW_VIDEOS:
        raise ValueError(
            f"Expected {EXPECTED_NEW_VIDEOS} commands, found {len(commands)}."
        )
    write_command_files(commands)
    print("Sprint 2.11 Recording Command Generation Summary")
    print("-------------------------------------------------")
    print(f"labels: {EXPECTED_NEW_LABELS}")
    print(f"repetitions per label: {SPRINT_2_11_REPETITIONS}")
    print(f"commands generated: {len(commands)}")
    print(f"PowerShell commands path: {POWERSHELL_COMMANDS_PATH.as_posix()}")
    print(f"Markdown commands path: {MARKDOWN_COMMANDS_PATH.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

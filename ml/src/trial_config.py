"""Trial dataset configuration for Phase 2, Sprint 2.3."""

from __future__ import annotations

from labels import ALL_LABELS_V1


TRIAL_LABELS: list[str] = [
    "A",
    "B",
    "C",
    "0",
    "1",
    "2",
    "deposit",
    "withdraw",
    "balance",
    "help",
    "confirm",
]

DEFAULT_PARTICIPANT_ID = "P02"
DEFAULT_CAMERA_INDEX = 1
DEFAULT_REPETITIONS = 5
DEFAULT_FRAMES = 60
DEFAULT_FPS = 20
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_NOTES = "Sprint 2.3 trial dataset"

EXPECTED_TRIAL_LABEL_COUNT = 11
EXPECTED_TOTAL_VIDEOS = len(TRIAL_LABELS) * DEFAULT_REPETITIONS


def validate_trial_config() -> None:
    """Validate the trial scope before helper scripts use it."""
    missing_labels = [label for label in TRIAL_LABELS if label not in ALL_LABELS_V1]
    if missing_labels:
        raise ValueError(
            "Trial labels must exist in ALL_LABELS_V1. Missing labels: "
            f"{', '.join(missing_labels)}"
        )

    if len(TRIAL_LABELS) != EXPECTED_TRIAL_LABEL_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TRIAL_LABEL_COUNT} trial labels, "
            f"but found {len(TRIAL_LABELS)}."
        )

    if EXPECTED_TOTAL_VIDEOS != 55:
        raise ValueError(
            f"Expected 55 total trial videos, but found {EXPECTED_TOTAL_VIDEOS}."
        )


validate_trial_config()

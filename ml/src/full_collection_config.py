"""Configuration for Phase 2, Sprint 2.8 remaining-label collection."""

from __future__ import annotations

from labels import ALL_LABELS_V1


# These labels were already collected during the Sprint 2.3 trial dataset.
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

# Keep the frozen V1 order so completed Sprint 2.8 commands remain predictable.
REMAINING_LABELS: list[str] = [label for label in ALL_LABELS_V1 if label not in TRIAL_LABELS]

FULL_DATASET_PARTICIPANT = "P02"
FULL_DATASET_CAMERA_INDEX = 1
FULL_DATASET_REPETITIONS = 10
FULL_DATASET_NOTES = "Sprint 2.8 full dataset collection"
FULL_DATASET_REWORK_NOTES = "Sprint 2.8 rework recording"

EXPECTED_VOCABULARY_SIZE = 56
EXPECTED_TRIAL_LABEL_COUNT = 11
EXPECTED_REMAINING_LABEL_COUNT = 45
EXPECTED_FULL_COLLECTION_VIDEOS = (
    EXPECTED_REMAINING_LABEL_COUNT * FULL_DATASET_REPETITIONS
)


def validate_full_collection_config() -> None:
    """Protect the fixed Sprint 2.8 scope before collection scripts use it."""
    if len(ALL_LABELS_V1) != EXPECTED_VOCABULARY_SIZE:
        raise ValueError(
            f"Expected {EXPECTED_VOCABULARY_SIZE} source labels, found {len(ALL_LABELS_V1)}."
        )
    if len(TRIAL_LABELS) != EXPECTED_TRIAL_LABEL_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TRIAL_LABEL_COUNT} trial labels, found {len(TRIAL_LABELS)}."
        )
    if len(set(TRIAL_LABELS)) != len(TRIAL_LABELS):
        raise ValueError("Sprint 2.8 trial labels must be unique.")

    missing_trial_labels = [label for label in TRIAL_LABELS if label not in ALL_LABELS_V1]
    if missing_trial_labels:
        raise ValueError(
            "Trial labels must exist in ALL_LABELS_V1. Missing labels: "
            f"{', '.join(missing_trial_labels)}"
        )
    if len(REMAINING_LABELS) != EXPECTED_REMAINING_LABEL_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REMAINING_LABEL_COUNT} remaining labels, "
            f"found {len(REMAINING_LABELS)}."
        )
    if len(set(REMAINING_LABELS)) != len(REMAINING_LABELS):
        raise ValueError("Remaining labels must be unique.")
    if "receipt" in REMAINING_LABELS or "payment" not in REMAINING_LABELS:
        raise ValueError(
            "Sprint 2.8 must replace receipt with payment in the remaining-label scope."
        )
    if EXPECTED_FULL_COLLECTION_VIDEOS != 450:
        raise ValueError(
            "Sprint 2.8 must plan exactly 450 recordings, but the current "
            f"configuration plans {EXPECTED_FULL_COLLECTION_VIDEOS}."
        )


validate_full_collection_config()

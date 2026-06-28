"""Configuration for Phase 2, Sprint 2.11 banking-intent expansion collection."""

from __future__ import annotations

from pathlib import Path

from labels import (
    ALL_LABELS_V2,
    BANKING_INTENTS_EXPANSION_V2,
    BANKING_INTENTS_V2,
    NORMAL_MODE_LABELS_V2,
    NUMBER_MODE_LABELS,
)


SPRINT_2_11_PARTICIPANT = "P02"
SPRINT_2_11_CAMERA_INDEX = 1
SPRINT_2_11_REPETITIONS = 10
SPRINT_2_11_NOTES = "Sprint 2.11 banking intent expansion"

EXPANSION_LABELS: list[str] = BANKING_INTENTS_EXPANSION_V2
REPLACED_EXPANSION_LABELS: list[str] = ["transaction_history", "dispute_transaction"]
REWORK_ADDED_LABELS: list[str] = ["document", "signature"]
REWORK_REDO_SAMPLES: list[tuple[str, int]] = [("account_number", 1), ("atm", 1)]
REWORK_RECORDING_PLAN: list[tuple[str, int]] = [
    *[
        (label, repetition)
        for label in REWORK_ADDED_LABELS
        for repetition in range(1, SPRINT_2_11_REPETITIONS + 1)
    ],
    *REWORK_REDO_SAMPLES,
]
EXPECTED_REWORK_RECORDINGS = 22
EXPECTED_NEW_LABELS = 30
EXPECTED_NEW_VIDEOS = EXPECTED_NEW_LABELS * SPRINT_2_11_REPETITIONS
EXPECTED_V2_BANKING_INTENTS = 50
EXPECTED_V2_TOTAL_LABELS = 86
EXPECTED_V2_NORMAL_MODE_LABELS = 76
EXPECTED_NUMBER_MODE_LABELS = 10

RAW_VIDEO_ROOT = Path("ml") / "data_raw" / "videos"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the sample ID shared by raw videos and metadata rows."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_video_path(participant_id: str, label: str, repetition: int) -> Path:
    """Return the intended raw-video path without creating or changing it."""
    return RAW_VIDEO_ROOT / label / f"{build_sample_id(participant_id, label, repetition)}.mp4"


def iter_expected_samples(
    participant_id: str = SPRINT_2_11_PARTICIPANT,
) -> list[dict[str, object]]:
    """Build the 300 expected Sprint 2.11 samples in stable label order."""
    samples: list[dict[str, object]] = []
    for label in EXPANSION_LABELS:
        for repetition in range(1, SPRINT_2_11_REPETITIONS + 1):
            sample_id = build_sample_id(participant_id, label, repetition)
            samples.append(
                {
                    "sample_id": sample_id,
                    "participant_id": participant_id,
                    "label": label,
                    "repetition": repetition,
                    "video_path": expected_video_path(participant_id, label, repetition),
                }
            )
    return samples


def validate_sprint_2_11_config() -> None:
    """Keep the expansion scope fixed before generating recording work."""
    if len(EXPANSION_LABELS) != EXPECTED_NEW_LABELS:
        raise ValueError(
            f"Sprint 2.11 must include {EXPECTED_NEW_LABELS} new labels, "
            f"found {len(EXPANSION_LABELS)}."
        )
    if len(set(EXPANSION_LABELS)) != len(EXPANSION_LABELS):
        raise ValueError("Sprint 2.11 expansion labels must be unique.")
    if set(EXPANSION_LABELS).intersection(BANKING_INTENTS_V2[:20]):
        raise ValueError("Sprint 2.11 expansion labels must not overlap with V1 banking intents.")
    if "receipt" in EXPANSION_LABELS or "receipt" in ALL_LABELS_V2:
        raise ValueError("receipt must not be included in the Sprint 2.11 scope.")
    if "payment" not in ALL_LABELS_V2:
        raise ValueError("payment must remain in the active V2 vocabulary.")
    if any(label in EXPANSION_LABELS for label in REPLACED_EXPANSION_LABELS):
        raise ValueError("Replaced Sprint 2.11 labels must not remain expected.")
    if any(label not in EXPANSION_LABELS for label in REWORK_ADDED_LABELS):
        raise ValueError("Rework replacement labels must be included in Sprint 2.11.")
    if len(BANKING_INTENTS_V2) != EXPECTED_V2_BANKING_INTENTS:
        raise ValueError("Sprint 2.11 must have 50 V2 banking intents.")
    if len(ALL_LABELS_V2) != EXPECTED_V2_TOTAL_LABELS:
        raise ValueError("Sprint 2.11 must have 86 total V2 labels.")
    if len(NORMAL_MODE_LABELS_V2) != EXPECTED_V2_NORMAL_MODE_LABELS:
        raise ValueError("Sprint 2.11 Normal Mode must have 76 labels.")
    if len(NUMBER_MODE_LABELS) != EXPECTED_NUMBER_MODE_LABELS:
        raise ValueError("Sprint 2.11 Number Mode must have 10 labels.")
    if len(iter_expected_samples()) != EXPECTED_NEW_VIDEOS:
        raise ValueError("Sprint 2.11 must plan exactly 300 new recordings.")
    if len(REWORK_RECORDING_PLAN) != EXPECTED_REWORK_RECORDINGS:
        raise ValueError("Sprint 2.11 rework must plan exactly 22 recordings.")


validate_sprint_2_11_config()

"""Configuration for Sprint 2.16A phone-camera weak-label pilot samples."""

from __future__ import annotations

from pathlib import Path

from labels import (
    ALL_LABELS_V3_76,
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)


PARTICIPANT_ID = "P02_PHONE"
SOURCE_NAME = "phone_live_landmark"
DEVICE_NAME = "Samsung Android phone"

WEAK_LABELS: list[str] = [
    "transfer",
    "document",
    "signature",
    "atm",
]

EXPECTED_SAMPLES_PER_LABEL = 20
TARGET_FRAMES = 60
LANDMARK_DIMENSION = 126
OUTPUT_CLASSES = 76
HISTORICAL_OUTPUT_CLASSES = 86

DATA_PHONE_DIR = Path("ml") / "data_phone"
PHONE_SAMPLE_DIR = DATA_PHONE_DIR / "landmark_samples"
IMPORTED_PHONE_DIR = DATA_PHONE_DIR / "imported_landmarks"

DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
OLD_EXPANDED_DATASET_PATH = DATASET_ROOT / "signsync_expanded_v2_2hand_60f.npz"
OLD_LABEL_MAPPING_PATH = DATASET_ROOT / "signsync_expanded_v2_label_mapping.json"
OLD_LABEL_GROUPS_PATH = DATASET_ROOT / "signsync_expanded_v2_label_groups.json"
OLD_SPLIT_CSV_PATH = DATASET_ROOT / "signsync_expanded_v2_splits.csv"

PHONE_PILOT_DATASET_VERSION = "signsync_scope_v3_40_phone_pilot_v1"
PHONE_PILOT_DATASET_PATH = DATASET_ROOT / f"{PHONE_PILOT_DATASET_VERSION}_2hand_60f.npz"
PHONE_PILOT_SPLIT_CSV_PATH = DATASET_ROOT / "signsync_scope_v3_40_splits.csv"
PHONE_PILOT_LABEL_MAPPING_PATH = DATASET_ROOT / "signsync_scope_v3_40_label_mapping.json"
PHONE_PILOT_LABEL_GROUPS_PATH = DATASET_ROOT / "signsync_scope_v3_40_label_groups.json"

FUTURE_MODEL_DIR = Path("ml") / "models" / "sprint_2_16A_v3_40"
FUTURE_MODEL_INPUT_SHAPE = (1, 756)
FUTURE_MODEL_OUTPUT_SHAPE = (1, 76)

EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
PHONE_SAMPLE_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_16A_phone_sample_check_report.csv"
PHONE_SAMPLE_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_16A_phone_sample_check_report.md"
DATASET_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_16A_dataset_report.csv"
DATASET_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_16A_dataset_report.md"


def validate_phone_dataset_config() -> None:
    """Protect the Sprint 2.16A pilot scope."""
    missing = [label for label in WEAK_LABELS if label not in BANKING_INTENTS_V3_40]
    if missing:
        raise ValueError(f"Sprint 2.16A weak labels are outside active V3 scope: {missing}")
    if len(WEAK_LABELS) != 4:
        raise ValueError(f"Expected four retained weak labels, found {len(WEAK_LABELS)}.")
    if set(WEAK_LABELS).intersection(REMOVED_BANKING_INTENTS_V3_10):
        raise ValueError("Removed banking intents cannot appear in the phone pilot.")
    if len(ALL_LABELS_V3_76) != OUTPUT_CLASSES:
        raise ValueError(f"Expected {OUTPUT_CLASSES} labels, found {len(ALL_LABELS_V3_76)}.")
    if len(ALPHABET_LABELS) != 26 or len(DIGIT_LABELS) != 10:
        raise ValueError("V3 requires 26 alphabet labels and 10 digit labels.")
    if FUTURE_MODEL_INPUT_SHAPE != (1, 756) or FUTURE_MODEL_OUTPUT_SHAPE != (1, 76):
        raise ValueError("Future model contract must be [1, 756] input and [1, 76] output.")
    if TARGET_FRAMES != 60 or LANDMARK_DIMENSION != 126:
        raise ValueError("Sprint 2.16A requires 60 frames x 126 landmark values.")


def split_for_phone_repetition(repetition: int) -> str:
    """Split phone repetitions while keeping validation/test phone samples."""
    if 1 <= repetition <= 14:
        return "train"
    if 15 <= repetition <= 17:
        return "val"
    if 18 <= repetition:
        return "test"
    raise ValueError(f"Invalid phone repetition: {repetition}")


def expected_total_phone_samples() -> int:
    """Return the minimum Sprint 2.16A phone pilot target."""
    return len(WEAK_LABELS) * EXPECTED_SAMPLES_PER_LABEL


validate_phone_dataset_config()

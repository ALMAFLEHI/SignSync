"""Configuration for Sprint 2.16A phone-camera weak-label pilot samples."""

from __future__ import annotations

from pathlib import Path

from labels import ALL_LABELS_V2


PARTICIPANT_ID = "P02_PHONE"
SOURCE_NAME = "phone_live_landmark"
DEVICE_NAME = "Samsung Android phone"

WEAK_LABELS: list[str] = [
    "transfer",
    "address_change",
    "document",
    "signature",
    "atm",
]

EXPECTED_SAMPLES_PER_LABEL = 20
TARGET_FRAMES = 60
LANDMARK_DIMENSION = 126
OUTPUT_CLASSES = 86

DATA_PHONE_DIR = Path("ml") / "data_phone"
PHONE_SAMPLE_DIR = DATA_PHONE_DIR / "landmark_samples"
IMPORTED_PHONE_DIR = DATA_PHONE_DIR / "imported_landmarks"

DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
OLD_EXPANDED_DATASET_PATH = DATASET_ROOT / "signsync_expanded_v2_2hand_60f.npz"
OLD_LABEL_MAPPING_PATH = DATASET_ROOT / "signsync_expanded_v2_label_mapping.json"
OLD_LABEL_GROUPS_PATH = DATASET_ROOT / "signsync_expanded_v2_label_groups.json"

PHONE_PILOT_DATASET_VERSION = "signsync_phone_pilot_v1"
PHONE_PILOT_DATASET_PATH = DATASET_ROOT / f"{PHONE_PILOT_DATASET_VERSION}_2hand_60f.npz"
PHONE_PILOT_SPLIT_CSV_PATH = DATASET_ROOT / f"{PHONE_PILOT_DATASET_VERSION}_splits.csv"
PHONE_PILOT_LABEL_MAPPING_PATH = DATASET_ROOT / f"{PHONE_PILOT_DATASET_VERSION}_label_mapping.json"
PHONE_PILOT_LABEL_GROUPS_PATH = DATASET_ROOT / f"{PHONE_PILOT_DATASET_VERSION}_label_groups.json"

EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
PHONE_SAMPLE_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_16A_phone_sample_check_report.csv"
PHONE_SAMPLE_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_16A_phone_sample_check_report.md"
DATASET_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_16A_dataset_report.csv"
DATASET_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_16A_dataset_report.md"


def validate_phone_dataset_config() -> None:
    """Protect the Sprint 2.16A pilot scope."""
    missing = [label for label in WEAK_LABELS if label not in ALL_LABELS_V2]
    if missing:
        raise ValueError(f"Sprint 2.16A weak labels are missing from V2 labels: {missing}")
    if len(ALL_LABELS_V2) != OUTPUT_CLASSES:
        raise ValueError(f"Expected {OUTPUT_CLASSES} labels, found {len(ALL_LABELS_V2)}.")
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

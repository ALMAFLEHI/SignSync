"""Shared configuration for Phase 2, Sprint 2.12 expanded V2 dataset workflow."""

from __future__ import annotations

from pathlib import Path

from labels import (
    ALL_LABELS_V2,
    BANKING_INTENTS_V2,
    NORMAL_MODE_LABELS_V2,
    NUMBER_MODE_LABELS,
)


EXPANDED_DATASET_PARTICIPANT = "P02"
TRIAL_LABELS: list[str] = [
    "A", "B", "C", "0", "1", "2", "deposit", "withdraw", "balance", "help", "confirm",
]
TEN_REPETITION_LABELS: list[str] = [
    label for label in ALL_LABELS_V2 if label not in TRIAL_LABELS
]

EXPECTED_LABELS = 86
EXPECTED_BANKING_INTENTS = 50
EXPECTED_SAMPLES = 805
EXPECTED_TRAIN_SAMPLES = 558
EXPECTED_VAL_SAMPLES = 86
EXPECTED_TEST_SAMPLES = 161
TRIAL_REPETITIONS = 5
FULL_REPETITIONS = 10
TARGET_FRAMES = 60
MAX_HANDS = 2
LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3
LANDMARK_DIMENSION = MAX_HANDS * LANDMARKS_PER_HAND * COORDINATES_PER_LANDMARK
MASK_DIMENSION = MAX_HANDS

RAW_VIDEO_ROOT = Path("ml") / "data_raw" / "videos"
LANDMARK_ROOT = Path("ml") / "data_processed" / "landmarks"
DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
METADATA_PATH = Path("ml") / "metadata.csv"
HAND_MODEL_PATH = Path("ml") / "models" / "hand_landmarker.task"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
DATASET_VERSION = "signsync_expanded_v2"

DATASET_PATH = DATASET_ROOT / f"{DATASET_VERSION}_2hand_60f.npz"
LABEL_MAPPING_PATH = DATASET_ROOT / f"{DATASET_VERSION}_label_mapping.json"
LABEL_GROUPS_PATH = DATASET_ROOT / f"{DATASET_VERSION}_label_groups.json"
SPLIT_CSV_PATH = DATASET_ROOT / f"{DATASET_VERSION}_splits.csv"

EXTRACTION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_extraction_report.csv"
EXTRACTION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_extraction_report.md"
LANDMARK_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_check.csv"
LANDMARK_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_check.md"
QUALITY_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_quality_report.csv"
QUALITY_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_landmark_quality_report.md"
PREPARATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_dataset_preparation_report.csv"
PREPARATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_dataset_preparation_report.md"
DATASET_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_training_dataset_check.csv"
DATASET_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_12_expanded_training_dataset_check.md"

MODEL_OUTPUT_DIR = Path("ml") / "models" / "sprint_2_12"
MODEL_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_baseline_model.joblib"
MODEL_LABEL_NAMES_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_label_names.json"
MODEL_LABEL_GROUPS_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_label_groups.json"
TRAINING_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_training_report.csv"
TRAINING_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_12_training_report.md"
METRICS_SUMMARY_PATH = EVIDENCE_DIR / "sprint_2_12_metrics_summary.json"
EVALUATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_evaluation_report.csv"
EVALUATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_12_evaluation_report.md"
CONFUSION_MATRIX_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_confusion_matrix.csv"
CONFUSION_MATRIX_PNG_PATH = EVIDENCE_DIR / "sprint_2_12_confusion_matrix.png"
WEAK_LABEL_ANALYSIS_CSV_PATH = EVIDENCE_DIR / "sprint_2_12_weak_label_analysis.csv"
WEAK_LABEL_ANALYSIS_MD_PATH = EVIDENCE_DIR / "sprint_2_12_weak_label_analysis.md"

LABEL_GROUPS = {
    "all_labels": ALL_LABELS_V2,
    "normal_mode": NORMAL_MODE_LABELS_V2,
    "number_mode": NUMBER_MODE_LABELS,
}


def repetitions_for_label(label: str) -> int:
    """Return the fixed repetition count for one expanded V2 label."""
    if label in TRIAL_LABELS:
        return TRIAL_REPETITIONS
    if label in TEN_REPETITION_LABELS:
        return FULL_REPETITIONS
    raise ValueError(f"Label is outside the expanded V2 scope: {label}")


def split_for_repetition(label: str, repetition: int) -> str:
    """Assign deterministic train, validation, and test splits from repetition."""
    if label in TRIAL_LABELS:
        if repetition in {1, 2, 3}:
            return "train"
        if repetition == 4:
            return "val"
        if repetition == 5:
            return "test"
    elif label in TEN_REPETITION_LABELS:
        if 1 <= repetition <= 7:
            return "train"
        if repetition == 8:
            return "val"
        if repetition in {9, 10}:
            return "test"
    raise ValueError(f"Unsupported repetition R{repetition:02d} for label {label}.")


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the stable raw, landmark, and dataset sample identifier."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_paths(participant_id: str, label: str, repetition: int) -> dict[str, Path]:
    """Return the raw video, landmark, and mask paths for one expected sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return {
        "video": RAW_VIDEO_ROOT / label / f"{sample_id}.mp4",
        "landmark_path": LANDMARK_ROOT / label / f"{sample_id}_landmarks.npy",
        "mask_path": LANDMARK_ROOT / label / f"{sample_id}_mask.npy",
    }


def iter_expected_samples(
    participant_id: str = EXPANDED_DATASET_PARTICIPANT,
) -> list[dict[str, object]]:
    """Build all 805 expected V2 samples in stable label and repetition order."""
    samples: list[dict[str, object]] = []
    for label_index, label in enumerate(ALL_LABELS_V2):
        for repetition in range(1, repetitions_for_label(label) + 1):
            paths = expected_paths(participant_id, label, repetition)
            samples.append(
                {
                    "sample_id": build_sample_id(participant_id, label, repetition),
                    "participant_id": participant_id,
                    "label": label,
                    "label_index": label_index,
                    "repetition": repetition,
                    "split": split_for_repetition(label, repetition),
                    **paths,
                }
            )
    return samples


def validate_expanded_dataset_config() -> None:
    """Protect the Sprint 2.12 expanded V2 scope before any script uses it."""
    if len(ALL_LABELS_V2) != EXPECTED_LABELS:
        raise ValueError(f"Expected {EXPECTED_LABELS} V2 labels, found {len(ALL_LABELS_V2)}.")
    if len(BANKING_INTENTS_V2) != EXPECTED_BANKING_INTENTS:
        raise ValueError("Expanded V2 scope must contain 50 banking intents.")
    if len(NORMAL_MODE_LABELS_V2) != 76 or len(NUMBER_MODE_LABELS) != 10:
        raise ValueError("Normal Mode V2 must be 76 labels and Number Mode must be 10 labels.")
    required = {"payment", "document", "signature"}
    excluded = {"receipt", "transaction_history", "dispute_transaction"}
    if not required.issubset(ALL_LABELS_V2):
        raise ValueError(f"Expanded V2 labels are missing required labels: {sorted(required)}")
    if excluded.intersection(ALL_LABELS_V2):
        raise ValueError(f"Expanded V2 labels contain excluded labels: {sorted(excluded)}")
    if len(TRIAL_LABELS) != 11 or len(TEN_REPETITION_LABELS) != 75:
        raise ValueError("Expected 11 trial labels and 75 ten-repetition labels.")
    if LANDMARK_DIMENSION != 126 or MASK_DIMENSION != 2:
        raise ValueError("Expanded V2 must use 126 landmark values and a 2-value mask.")
    samples = iter_expected_samples()
    split_counts = {
        split: sum(sample["split"] == split for sample in samples)
        for split in ("train", "val", "test")
    }
    if len(samples) != EXPECTED_SAMPLES:
        raise ValueError(f"Expected {EXPECTED_SAMPLES} samples, found {len(samples)}.")
    if split_counts != {
        "train": EXPECTED_TRAIN_SAMPLES,
        "val": EXPECTED_VAL_SAMPLES,
        "test": EXPECTED_TEST_SAMPLES,
    }:
        raise ValueError(f"Unexpected expanded V2 split counts: {split_counts}")


validate_expanded_dataset_config()

"""Dataset preparation configuration for Phase 2, Sprint 2.5."""

from __future__ import annotations

from pathlib import Path

from trial_config import TRIAL_LABELS


PARTICIPANT_ID = "P02"
TARGET_FRAMES = 60
LANDMARK_DIM = 126
MASK_DIM = 2
EXPECTED_REPETITIONS = 5
EXPECTED_SAMPLES = 55

DATASET_OUTPUT_DIR = Path("ml") / "data_processed" / "datasets"
REPORT_OUTPUT_DIR = Path("docs") / "phase_2_evidence"

DATASET_FILENAME = "signsync_trial_v1_2hand_60f.npz"
LABEL_MAPPING_FILENAME = "signsync_trial_v1_label_mapping.json"
SPLIT_CSV_FILENAME = "signsync_trial_v1_splits.csv"

QUALITY_REPORT_CSV_FILENAME = "sprint_2_5_landmark_quality_report.csv"
QUALITY_REPORT_MD_FILENAME = "sprint_2_5_landmark_quality_report.md"
TRAINING_CHECK_CSV_FILENAME = "sprint_2_5_training_dataset_check.csv"
TRAINING_CHECK_MD_FILENAME = "sprint_2_5_training_dataset_check.md"
PREPARATION_REPORT_CSV_FILENAME = "sprint_2_5_training_dataset_preparation_report.csv"
PREPARATION_REPORT_MD_FILENAME = "sprint_2_5_training_dataset_preparation_report.md"

DATASET_PATH = DATASET_OUTPUT_DIR / DATASET_FILENAME
LABEL_MAPPING_PATH = DATASET_OUTPUT_DIR / LABEL_MAPPING_FILENAME
SPLIT_CSV_PATH = DATASET_OUTPUT_DIR / SPLIT_CSV_FILENAME

QUALITY_REPORT_CSV_PATH = REPORT_OUTPUT_DIR / QUALITY_REPORT_CSV_FILENAME
QUALITY_REPORT_MD_PATH = REPORT_OUTPUT_DIR / QUALITY_REPORT_MD_FILENAME
TRAINING_CHECK_CSV_PATH = REPORT_OUTPUT_DIR / TRAINING_CHECK_CSV_FILENAME
TRAINING_CHECK_MD_PATH = REPORT_OUTPUT_DIR / TRAINING_CHECK_MD_FILENAME
PREPARATION_REPORT_CSV_PATH = REPORT_OUTPUT_DIR / PREPARATION_REPORT_CSV_FILENAME
PREPARATION_REPORT_MD_PATH = REPORT_OUTPUT_DIR / PREPARATION_REPORT_MD_FILENAME

TRAIN_REPETITIONS = {1, 2, 3}
VAL_REPETITIONS = {4}
TEST_REPETITIONS = {5}

EXPECTED_TRAIN_SAMPLES = 33
EXPECTED_VAL_SAMPLES = 11
EXPECTED_TEST_SAMPLES = 11


def validate_dataset_config() -> None:
    """Validate the Sprint 2.5 dataset preparation constants."""
    if len(TRIAL_LABELS) * EXPECTED_REPETITIONS != EXPECTED_SAMPLES:
        raise ValueError(
            "Sprint 2.5 expected sample count is inconsistent with "
            "trial labels and repetitions."
        )

    if len(TRAIN_REPETITIONS) * len(TRIAL_LABELS) != EXPECTED_TRAIN_SAMPLES:
        raise ValueError("Training split expected count is incorrect.")

    if len(VAL_REPETITIONS) * len(TRIAL_LABELS) != EXPECTED_VAL_SAMPLES:
        raise ValueError("Validation split expected count is incorrect.")

    if len(TEST_REPETITIONS) * len(TRIAL_LABELS) != EXPECTED_TEST_SAMPLES:
        raise ValueError("Test split expected count is incorrect.")


validate_dataset_config()

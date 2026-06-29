"""Configuration for Phase 2, Sprint 2.13 TensorFlow Lite export workflow."""

from __future__ import annotations

from pathlib import Path

from expanded_dataset_config import (
    DATASET_PATH as EXPANDED_SEQUENCE_DATASET_PATH,
    EXPECTED_LABELS,
    EXPECTED_SAMPLES,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    LABEL_GROUPS_PATH,
    LABEL_MAPPING_PATH,
    LANDMARK_DIMENSION,
    MASK_DIMENSION,
    SPLIT_CSV_PATH,
    TARGET_FRAMES,
)


DATASET_VERSION = "signsync_expanded_v2"
SPRINT_OUTPUT_DIR = Path("ml") / "models" / "sprint_2_13"
DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
FEATURE_DATASET_PATH = DATASET_ROOT / f"{DATASET_VERSION}_stats_756f.npz"
SOURCE_DATASET_PATH = EXPANDED_SEQUENCE_DATASET_PATH
SOURCE_SPLIT_CSV_PATH = SPLIT_CSV_PATH
SOURCE_LABEL_MAPPING_PATH = LABEL_MAPPING_PATH
SOURCE_LABEL_GROUPS_PATH = LABEL_GROUPS_PATH
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"

FEATURE_ORDER: list[str] = ["mean", "std", "min", "max", "first_frame", "last_frame"]
INPUT_FEATURE_WIDTH = 756
OUTPUT_CLASSES = EXPECTED_LABELS
EXPECTED_TOTAL_SAMPLES = EXPECTED_SAMPLES
EXPECTED_TRAIN = EXPECTED_TRAIN_SAMPLES
EXPECTED_VAL = EXPECTED_VAL_SAMPLES
EXPECTED_TEST = EXPECTED_TEST_SAMPLES

KERAS_MODEL_PATH = SPRINT_OUTPUT_DIR / f"{DATASET_VERSION}_keras_best.keras"
SAVED_MODEL_DIR = SPRINT_OUTPUT_DIR / "saved_model" / f"{DATASET_VERSION}_keras_best"
TFLITE_FLOAT32_PATH = SPRINT_OUTPUT_DIR / f"{DATASET_VERSION}_float32.tflite"
TFLITE_DYNAMIC_RANGE_PATH = SPRINT_OUTPUT_DIR / f"{DATASET_VERSION}_dynamic_range.tflite"
MODEL_LABEL_NAMES_PATH = SPRINT_OUTPUT_DIR / f"{DATASET_VERSION}_label_names.json"
MODEL_LABEL_GROUPS_PATH = SPRINT_OUTPUT_DIR / f"{DATASET_VERSION}_label_groups.json"
FLUTTER_ASSETS_DIR = SPRINT_OUTPUT_DIR / "flutter_assets"

FEATURE_PREPARATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_feature_preparation_report.csv"
FEATURE_PREPARATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_feature_preparation_report.md"
FEATURE_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_feature_check.csv"
FEATURE_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_feature_check.md"
ENVIRONMENT_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_13_environment_check.md"
KERAS_TRAINING_HISTORY_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_keras_training_history.csv"
KERAS_TRAINING_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_keras_training_report.md"
KERAS_METRICS_SUMMARY_PATH = EVIDENCE_DIR / "sprint_2_13_keras_metrics_summary.json"
KERAS_EVALUATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_keras_evaluation_report.csv"
KERAS_EVALUATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_keras_evaluation_report.md"
KERAS_CONFUSION_MATRIX_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_keras_confusion_matrix.csv"
KERAS_CONFUSION_MATRIX_PNG_PATH = EVIDENCE_DIR / "sprint_2_13_keras_confusion_matrix.png"
TFLITE_CONVERSION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_conversion_report.md"
TFLITE_TEST_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_test_report.csv"
TFLITE_TEST_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_tflite_test_report.md"
FLUTTER_ASSETS_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_13_flutter_assets_report.md"

SPRINT_2_12_BASELINE_ACCURACY = 0.9441
SPRINT_2_12_BASELINE_MACRO_F1 = 0.9256


def expected_split_counts() -> dict[str, int]:
    """Return the fixed expanded V2 split counts used by Sprint 2.13."""
    return {"train": EXPECTED_TRAIN, "val": EXPECTED_VAL, "test": EXPECTED_TEST}


def validate_tflite_config() -> None:
    """Protect the TensorFlow/TFLite workflow shape and label assumptions."""
    if TARGET_FRAMES != 60:
        raise ValueError(f"TFLite workflow expects 60 source frames, found {TARGET_FRAMES}.")
    if LANDMARK_DIMENSION != 126:
        raise ValueError(f"TFLite workflow expects 126 landmark values, found {LANDMARK_DIMENSION}.")
    if MASK_DIMENSION != 2:
        raise ValueError(f"TFLite workflow expects a two-hand mask, found {MASK_DIMENSION}.")
    if INPUT_FEATURE_WIDTH != LANDMARK_DIMENSION * len(FEATURE_ORDER):
        raise ValueError("Input feature width must be 126 x 6 = 756.")
    if OUTPUT_CLASSES != 86:
        raise ValueError(f"TFLite output must contain 86 classes, found {OUTPUT_CLASSES}.")
    if expected_split_counts() != {"train": 558, "val": 86, "test": 161}:
        raise ValueError("Unexpected Sprint 2.13 split counts.")


validate_tflite_config()

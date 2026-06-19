"""Configuration shared by the Phase 2, Sprint 2.7 validation scripts."""

from __future__ import annotations

from pathlib import Path


# Existing Sprint 2.5 and Sprint 2.6 inputs. These paths are relative to the
# project root so the scripts remain portable across Windows machines.
DATASET_PATH = "ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz"
LABEL_MAPPING_PATH = "ml/data_processed/datasets/signsync_trial_v1_label_mapping.json"
SPLIT_CSV_PATH = "ml/data_processed/datasets/signsync_trial_v1_splits.csv"
MODEL_PATH = "ml/models/sprint_2_6/signsync_trial_baseline_model.joblib"
SCALER_PATH = "ml/models/sprint_2_6/signsync_trial_baseline_scaler.joblib"
LABEL_NAMES_PATH = "ml/models/sprint_2_6/signsync_trial_label_names.json"
REPORT_OUTPUT_DIR = "docs/phase_2_evidence"
ALL_LABELS_SOURCE = "ml/src/labels.py"

# Sprint 2.7 report filenames.
INPUT_CHECK_REPORT_MD = "sprint_2_7_input_check_report.md"
PIPELINE_VALIDATION_REPORT_CSV = "sprint_2_7_pipeline_validation_report.csv"
PIPELINE_VALIDATION_REPORT_MD = "sprint_2_7_pipeline_validation_report.md"
PREDICTION_CHECK_REPORT_CSV = "sprint_2_7_prediction_check_report.csv"
PREDICTION_CHECK_REPORT_MD = "sprint_2_7_prediction_check_report.md"
DATASET_LIMITATION_REPORT_MD = "sprint_2_7_dataset_limitation_report.md"
DATASET_LIMITATION_REPORT_JSON = "sprint_2_7_dataset_limitation_report.json"
FULL_DATASET_RECORDING_PLAN_MD = "sprint_2_7_full_dataset_recording_plan.md"
FULL_DATASET_RECORDING_PLAN_CSV = "sprint_2_7_full_dataset_recording_plan.csv"
REMAINING_LABELS_CSV = "sprint_2_7_remaining_labels.csv"
READINESS_DECISION_MD = "sprint_2_7_readiness_decision.md"

DEFAULT_FEATURE_MODE = "stats"

EXPECTED_X_SHAPE = (55, 60, 126)
EXPECTED_Y_SHAPE = (55,)
EXPECTED_LABEL_COUNT = 11
EXPECTED_SPLIT_COUNTS = {"train": 33, "val": 11, "test": 11}
STATS_FEATURE_SIZE = 756

REPORT_OUTPUT_PATH = Path(REPORT_OUTPUT_DIR)
TRAINING_REPORT_PATH = REPORT_OUTPUT_PATH / "sprint_2_6_training_report.md"
EVALUATION_REPORT_PATH = REPORT_OUTPUT_PATH / "sprint_2_6_evaluation_report.md"
CONFUSION_MATRIX_PATH = REPORT_OUTPUT_PATH / "sprint_2_6_confusion_matrix.png"
METRICS_SUMMARY_PATH = REPORT_OUTPUT_PATH / "sprint_2_6_metrics_summary.json"


def report_path(filename: str) -> Path:
    """Return an evidence-report path and keep all output path handling central."""
    return REPORT_OUTPUT_PATH / filename

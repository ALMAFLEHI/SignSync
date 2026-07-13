"""Configuration for the Sprint 2.16A controlled phone augmentation experiment."""

from __future__ import annotations

from pathlib import Path

from labels import ALL_LABELS_V3_76, BANKING_INTENTS_V3_40


SEED = 42
PARTICIPANT_ID = "P02_PHONE"
PHONE_SOURCE = "phone_live_landmark"
PHONE_DEVICE_METADATA = "Samsung Android phone"
PHYSICAL_DEVICE = "Samsung Galaxy A55"
PILOT_LABELS: list[str] = ["transfer", "document", "signature", "atm"]
EXPECTED_PHONE_REPETITIONS = set(range(1, 26))

TARGET_FRAMES = 60
FRAME_WIDTH = 126
FEATURE_ORDER: list[str] = [
    "mean",
    "std",
    "min",
    "max",
    "first_frame",
    "last_frame",
]
FEATURE_WIDTH = 756
OUTPUT_CLASSES = 76

PHONE_SAMPLE_DIR = Path("ml") / "data_phone" / "landmark_samples"
PHONE_SPLIT_DIR = Path("ml") / "data_phone" / "splits"
PHONE_SPLIT_MANIFEST_PATH = (
    PHONE_SPLIT_DIR / "sprint_2_16A_phone_split_manifest.csv"
)
COMBINED_MANIFEST_PATH = (
    PHONE_SPLIT_DIR / "sprint_2_16A_combined_dataset_manifest.csv"
)
PARITY_FIXTURE_PATH = (
    Path("ml")
    / "data_phone"
    / "fixtures"
    / "P02_PHONE_transfer_R21_feature_parity.json"
)

DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
HISTORICAL_SEQUENCE_DATASET_PATH = (
    DATASET_ROOT / "signsync_expanded_v2_2hand_60f.npz"
)
EXPERIMENT_DATASET_DIR = DATASET_ROOT / "sprint_2_16A_v3_40"
REAL_SEQUENCE_DATASET_PATH = (
    EXPERIMENT_DATASET_DIR / "signsync_scope_v3_40_phone_real_sequences.npz"
)

MODEL_ROOT = Path("ml") / "models" / "sprint_2_16A_v3_40"
NO_AUGMENTATION_DIR = MODEL_ROOT / "no_augmentation"
WITH_AUGMENTATION_DIR = MODEL_ROOT / "with_augmentation"
BASELINE_KERAS_PATH = (
    Path("ml")
    / "models"
    / "sprint_2_13"
    / "signsync_expanded_v2_keras_best.keras"
)
BASELINE_TFLITE_PATH = (
    Path("ml")
    / "models"
    / "sprint_2_13"
    / "signsync_expanded_v2_dynamic_range.tflite"
)
BASELINE_LABELS_PATH = (
    Path("ml")
    / "models"
    / "sprint_2_13"
    / "signsync_expanded_v2_label_names.json"
)

ACTIVE_SCOPE_PATH = Path("ml") / "config" / "signsync_active_scope_v3_40.json"
AUGMENTATION_CONFIG_PATH = (
    Path("ml") / "config" / "sprint_2_16A_augmentation_config.json"
)

EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
DETAILED_VALIDATION_MD_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_dataset_detailed_validation.md"
)
DETAILED_VALIDATION_CSV_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_dataset_detailed_validation.csv"
)
DETAILED_VALIDATION_JSON_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_dataset_detailed_validation.json"
)
DATASET_COUNTS_CSV_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_controlled_dataset_counts.csv"
)
CONTROLLED_REPORT_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_controlled_experiment_report.md"
)
COMPARISON_CSV_PATH = EVIDENCE_DIR / "sprint_2_16A_experiment_comparison.csv"
PHONE_PREDICTIONS_CSV_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_test_predictions.csv"
)
PER_CLASS_METRICS_CSV_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_per_class_metrics.csv"
)

HIDDEN_UNITS: list[int] = [512, 256, 128]
DROPOUT = 0.25
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
MAX_EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20
CONFIDENCE_THRESHOLD = 0.70
TOP2_GAP_THRESHOLD = 0.15
CONTROL_LABELS: list[str] = ["A", "7", "deposit", "payment", "balance"]


def phone_split_for_repetition(repetition: int) -> str:
    """Return the fixed leakage-safe phone split."""
    if 1 <= repetition <= 15:
        return "train"
    if 16 <= repetition <= 20:
        return "val"
    if 21 <= repetition <= 25:
        return "test"
    raise ValueError(f"Phone repetition R{repetition:02d} is outside R01-R25.")


def validate_experiment_config() -> None:
    """Protect the controlled experiment contract."""
    if len(ALL_LABELS_V3_76) != OUTPUT_CLASSES:
        raise ValueError("The controlled experiment requires exactly 76 active labels.")
    if len(BANKING_INTENTS_V3_40) != 40:
        raise ValueError("The controlled experiment requires 40 active banking intents.")
    if not set(PILOT_LABELS).issubset(BANKING_INTENTS_V3_40):
        raise ValueError("Every pilot label must be an active banking intent.")
    if FRAME_WIDTH * len(FEATURE_ORDER) != FEATURE_WIDTH:
        raise ValueError("Feature contract must be 126 x 6 = 756 values.")
    split_counts = {
        split: sum(phone_split_for_repetition(rep) == split for rep in range(1, 26))
        for split in ("train", "val", "test")
    }
    if split_counts != {"train": 15, "val": 5, "test": 5}:
        raise ValueError(f"Unexpected phone split contract: {split_counts}")


validate_experiment_config()

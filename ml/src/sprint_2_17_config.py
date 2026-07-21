"""Frozen configuration for Sprint 2.17 final 40-class training."""

from __future__ import annotations

from pathlib import Path

from labels import (
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
    SPRINT_2_16A_PILOT_INTENTS_4,
)


ROOT = Path(__file__).resolve().parents[2]
SEED = 21617
AUGMENTATION_SEED = 42

FINAL_LABELS: list[str] = list(BANKING_INTENTS_V3_40)
LABEL_TO_INDEX = {label: index for index, label in enumerate(FINAL_LABELS)}
PILOT_LABELS: list[str] = list(SPRINT_2_16A_PILOT_INTENTS_4)
REMOVED_LABELS: list[str] = list(REMOVED_BANKING_INTENTS_V3_10)

PARTICIPANT_ID = "P02_PHONE"
PHONE_SOURCE = "phone_live_landmark"
PHONE_DEVICE = "Samsung Android phone"
PHONE_SAMPLE_DIR = ROOT / "ml" / "data_phone" / "landmark_samples"
PHONE_BACKUP_PATH = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
)
PILOT_MANIFEST_PATH = (
    ROOT
    / "ml"
    / "data_phone"
    / "splits"
    / "sprint_2_16A_phone_split_manifest.csv"
)
HISTORICAL_DATASET_PATH = (
    ROOT
    / "ml"
    / "data_processed"
    / "datasets"
    / "signsync_expanded_v2_2hand_60f.npz"
)

DERIVED_ROOT = ROOT / "ml" / "data_phone" / "sprint_2_17_40class"
DERIVED_MANIFEST_DIR = DERIVED_ROOT / "manifests"
DERIVED_FEATURE_DIR = DERIVED_ROOT / "features"
DERIVED_AUGMENTATION_DIR = DERIVED_ROOT / "augmentation"
DERIVED_REPORT_DIR = DERIVED_ROOT / "reports"
DERIVED_CHECKSUM_DIR = DERIVED_ROOT / "checksums"

CANDIDATE_ROOT = ROOT / "ml" / "models" / "sprint_2_17_final_40class"
MODEL_DIR = CANDIDATE_ROOT / "models"
METADATA_DIR = CANDIDATE_ROOT / "metadata"
MANIFEST_DIR = CANDIDATE_ROOT / "manifests"
METRICS_DIR = CANDIDATE_ROOT / "metrics"
FIGURES_DIR = CANDIDATE_ROOT / "figures"
REPORTS_DIR = CANDIDATE_ROOT / "reports"
EXPERIMENTS_DIR = CANDIDATE_ROOT / "experiments"

PHONE_TRAIN_MANIFEST = MANIFEST_DIR / "phone_train_manifest.csv"
PHONE_VALIDATION_MANIFEST = MANIFEST_DIR / "phone_validation_manifest.csv"
PHONE_TEST_MANIFEST = MANIFEST_DIR / "phone_test_manifest.csv"
COMBINED_MANIFEST = MANIFEST_DIR / "combined_split_manifest.json"

PHONE_TRAIN_FEATURES = DERIVED_FEATURE_DIR / "phone_train_features.npz"
PHONE_VALIDATION_FEATURES = DERIVED_FEATURE_DIR / "phone_validation_features.npz"
PHONE_TEST_FEATURES = DERIVED_FEATURE_DIR / "phone_test_features_locked.npz"
PHONE_AUGMENTED_FEATURES = (
    DERIVED_FEATURE_DIR / "phone_train_augmented_features.npz"
)
HISTORICAL_TRAIN_FEATURES = (
    DERIVED_FEATURE_DIR / "historical_banking_train_features.npz"
)

TARGET_FRAMES = 60
FRAME_WIDTH = 126
FEATURE_ORDER: list[str] = [
    "mean",
    "population_std",
    "minimum",
    "maximum",
    "first_frame",
    "last_frame",
]
FEATURE_WIDTH = 756
OUTPUT_CLASSES = 40

HIDDEN_UNITS: list[int] = [512, 256, 128]
DROPOUT = 0.25
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
MAX_EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20

MINIMUM_CONFIDENCE_GRID: list[float] = [0.50, 0.60, 0.70, 0.80, 0.90]
TOP2_MARGIN_GRID: list[float] = [0.00, 0.10, 0.15, 0.20]
MINIMUM_CALIBRATION_COVERAGE = 0.70

FLUTTER_DYNAMIC_MODEL = (
    ROOT / "flutter_app" / "assets" / "models" / "model_dynamic_range.tflite"
)
FLUTTER_FLOAT32_MODEL = (
    ROOT / "flutter_app" / "assets" / "models" / "model_float32.tflite"
)
QUERY_CONFIG_PATH = (
    ROOT / "flutter_app" / "assets" / "content" / "banking_queries.json"
)
EXPECTED_FLUTTER_DYNAMIC_SHA256 = (
    "88CDC0367F40E50081E5BDE7644EDE242937061843CB68EA1235214E62308DDD"
)
EXPECTED_FLUTTER_FLOAT32_SHA256 = (
    "36EC44E5EBEFD1C7DE56161A305324488BFD6CFC58337CA9B2679198F424FAC8"
)
EXPECTED_PHONE_BACKUP_SHA256 = (
    "F3F76C6BBE06305C7AE82E2772C5DACA7F76619444F7ECA892D7AA253986B70B"
)
EXPECTED_QUERY_CONFIG_SHA256 = (
    "6F52D50F8FBBF64CD43479A1A6135F3886164D7857B1430090589D2CCCEC6B51"
)


def split_for_repetition(repetition: int) -> str:
    """Return the frozen deterministic phone split for R01-R25."""
    if 1 <= repetition <= 15:
        return "train"
    if 16 <= repetition <= 20:
        return "validation"
    if 21 <= repetition <= 25:
        return "test"
    raise ValueError(f"Repetition R{repetition:02d} is outside R01-R25.")


def ensure_output_directories() -> None:
    """Create only Sprint 2.17 derived and candidate directories."""
    for path in (
        DERIVED_MANIFEST_DIR,
        DERIVED_FEATURE_DIR,
        DERIVED_AUGMENTATION_DIR,
        DERIVED_REPORT_DIR,
        DERIVED_CHECKSUM_DIR,
        MODEL_DIR,
        METADATA_DIR,
        MANIFEST_DIR,
        METRICS_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        EXPERIMENTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def validate_config() -> None:
    """Protect the final scope, order, and feature contract."""
    if len(FINAL_LABELS) != OUTPUT_CLASSES or len(set(FINAL_LABELS)) != 40:
        raise ValueError("Sprint 2.17 requires exactly 40 unique banking labels.")
    if set(FINAL_LABELS).intersection(ALPHABET_LABELS + DIGIT_LABELS):
        raise ValueError("Alphabet and digit labels are forbidden in the final scope.")
    if set(FINAL_LABELS).intersection(REMOVED_LABELS):
        raise ValueError("Removed banking labels are forbidden in the final scope.")
    if not set(PILOT_LABELS).issubset(FINAL_LABELS):
        raise ValueError("Every protected pilot label must remain in the final scope.")
    if TARGET_FRAMES != 60 or FRAME_WIDTH != 126 or FEATURE_WIDTH != 756:
        raise ValueError("The protected 60 x 126 to 756 feature contract changed.")
    if FRAME_WIDTH * len(FEATURE_ORDER) != FEATURE_WIDTH:
        raise ValueError("The six 126-value feature groups must total 756 values.")


validate_config()

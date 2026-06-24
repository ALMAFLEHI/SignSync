"""Shared configuration for Phase 2, Sprint 2.10 full dataset preparation."""

from __future__ import annotations

from pathlib import Path

from labels import ALPHABET_LABELS, ALL_LABELS_V1, BANKING_INTENTS_V1, DIGIT_LABELS


FULL_DATASET_PARTICIPANT = "P02"
TRIAL_LABELS: list[str] = [
    "A", "B", "C", "0", "1", "2", "deposit", "withdraw", "balance", "help", "confirm",
]
FULL_COLLECTION_LABELS: list[str] = [label for label in ALL_LABELS_V1 if label not in TRIAL_LABELS]

EXPECTED_LABELS = 56
EXPECTED_SAMPLES = 505
TARGET_FRAMES = 60
LANDMARK_DIMENSION = 126
MASK_DIMENSION = 2
TRIAL_REPETITIONS = 5
FULL_COLLECTION_REPETITIONS = 10
EXPECTED_TRAIN_SAMPLES = 348
EXPECTED_VAL_SAMPLES = 56
EXPECTED_TEST_SAMPLES = 101

LANDMARK_ROOT = Path("ml") / "data_processed" / "landmarks"
DATASET_ROOT = Path("ml") / "data_processed" / "datasets"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
DATASET_VERSION = "signsync_full_v1"

DATASET_PATH = DATASET_ROOT / f"{DATASET_VERSION}_2hand_60f.npz"
LABEL_MAPPING_PATH = DATASET_ROOT / f"{DATASET_VERSION}_label_mapping.json"
LABEL_GROUPS_PATH = DATASET_ROOT / f"{DATASET_VERSION}_label_groups.json"
SPLIT_CSV_PATH = DATASET_ROOT / f"{DATASET_VERSION}_splits.csv"

QUALITY_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_full_landmark_quality_report.csv"
QUALITY_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_10_full_landmark_quality_report.md"
PREPARATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_full_dataset_preparation_report.csv"
PREPARATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_10_full_dataset_preparation_report.md"
DATASET_CHECK_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_full_training_dataset_check.csv"
DATASET_CHECK_MD_PATH = EVIDENCE_DIR / "sprint_2_10_full_training_dataset_check.md"

MODEL_OUTPUT_DIR = Path("ml") / "models" / "sprint_2_10"
MODEL_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_baseline_model.joblib"
MODEL_LABEL_NAMES_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_label_names.json"
MODEL_LABEL_GROUPS_PATH = MODEL_OUTPUT_DIR / f"{DATASET_VERSION}_label_groups.json"
TRAINING_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_training_report.csv"
TRAINING_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_10_training_report.md"
METRICS_SUMMARY_PATH = EVIDENCE_DIR / "sprint_2_10_metrics_summary.json"
EVALUATION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_evaluation_report.csv"
EVALUATION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_10_evaluation_report.md"
CONFUSION_MATRIX_CSV_PATH = EVIDENCE_DIR / "sprint_2_10_confusion_matrix.csv"
CONFUSION_MATRIX_PNG_PATH = EVIDENCE_DIR / "sprint_2_10_confusion_matrix.png"

LABEL_GROUPS = {
    "normal_mode": ALPHABET_LABELS + BANKING_INTENTS_V1,
    "number_mode": DIGIT_LABELS,
    "all_labels": ALL_LABELS_V1,
}


def repetitions_for_label(label: str) -> int:
    """Return the fixed repetition count for one current scoped label."""
    if label in TRIAL_LABELS:
        return TRIAL_REPETITIONS
    if label in FULL_COLLECTION_LABELS:
        return FULL_COLLECTION_REPETITIONS
    raise ValueError(f"Label is outside the full dataset scope: {label}")


def split_for_repetition(label: str, repetition: int) -> str:
    """Assign a non-random split from repetition number to avoid sample leakage."""
    if label in TRIAL_LABELS:
        if repetition in {1, 2, 3}:
            return "train"
        if repetition == 4:
            return "val"
        if repetition == 5:
            return "test"
    elif label in FULL_COLLECTION_LABELS:
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
    """Return the two Sprint 2.9 output paths consumed by dataset preparation."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return {
        "landmark_path": LANDMARK_ROOT / label / f"{sample_id}_landmarks.npy",
        "mask_path": LANDMARK_ROOT / label / f"{sample_id}_mask.npy",
    }


def iter_expected_samples(participant_id: str = FULL_DATASET_PARTICIPANT) -> list[dict[str, object]]:
    """Build all 505 expected samples in stable label and repetition order."""
    samples: list[dict[str, object]] = []
    for label_index, label in enumerate(ALL_LABELS_V1):
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


def validate_full_dataset_config() -> None:
    """Ensure the full dataset scope and future app mode metadata remain stable."""
    if len(ALL_LABELS_V1) != EXPECTED_LABELS:
        raise ValueError(f"Expected {EXPECTED_LABELS} labels, found {len(ALL_LABELS_V1)}.")
    if len(TRIAL_LABELS) != 11 or len(FULL_COLLECTION_LABELS) != 45:
        raise ValueError("Expected 11 trial labels and 45 full collection labels.")
    if "payment" not in ALL_LABELS_V1 or "receipt" in ALL_LABELS_V1:
        raise ValueError("The full dataset must include payment and exclude receipt.")
    if len(LABEL_GROUPS["normal_mode"]) != 46:
        raise ValueError("Normal Mode must include 26 alphabet and 20 banking labels.")
    if len(LABEL_GROUPS["number_mode"]) != 10:
        raise ValueError("Number Mode must include exactly 10 digit labels.")
    if LABEL_GROUPS["all_labels"] != ALL_LABELS_V1:
        raise ValueError("All-label mode metadata must preserve ALL_LABELS_V1 order.")
    samples = iter_expected_samples()
    split_counts = {split: sum(sample["split"] == split for sample in samples) for split in ("train", "val", "test")}
    if len(samples) != EXPECTED_SAMPLES:
        raise ValueError(f"Expected {EXPECTED_SAMPLES} samples, found {len(samples)}.")
    if split_counts != {"train": EXPECTED_TRAIN_SAMPLES, "val": EXPECTED_VAL_SAMPLES, "test": EXPECTED_TEST_SAMPLES}:
        raise ValueError(f"Unexpected repetition split counts: {split_counts}")


validate_full_dataset_config()

"""Configuration for Phase 2, Sprint 2.9 full-dataset landmark extraction."""

from __future__ import annotations

from pathlib import Path

from labels import ALL_LABELS_V1


FULL_DATASET_PARTICIPANT = "P02"
TRIAL_LABELS: list[str] = [
    "A",
    "B",
    "C",
    "0",
    "1",
    "2",
    "deposit",
    "withdraw",
    "balance",
    "help",
    "confirm",
]
FULL_COLLECTION_LABELS: list[str] = [label for label in ALL_LABELS_V1 if label not in TRIAL_LABELS]

TRIAL_REPETITIONS = 5
FULL_COLLECTION_REPETITIONS = 10
EXPECTED_SCOPED_LABELS = 56
EXPECTED_TRIAL_LABELS = 11
EXPECTED_FULL_COLLECTION_LABELS = 45
EXPECTED_TRIAL_VIDEOS = EXPECTED_TRIAL_LABELS * TRIAL_REPETITIONS
EXPECTED_FULL_COLLECTION_VIDEOS = (
    EXPECTED_FULL_COLLECTION_LABELS * FULL_COLLECTION_REPETITIONS
)
EXPECTED_TOTAL_RAW_VIDEOS = EXPECTED_TRIAL_VIDEOS + EXPECTED_FULL_COLLECTION_VIDEOS

MAX_HANDS = 2
LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3
LANDMARK_VALUES_PER_HAND = LANDMARKS_PER_HAND * COORDINATES_PER_LANDMARK
LANDMARK_OUTPUT_DIMENSION = MAX_HANDS * LANDMARK_VALUES_PER_HAND
HAND_MASK_DIMENSION = MAX_HANDS
DEFAULT_TARGET_FRAMES = 60

RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"
LANDMARK_DIR = Path("ml") / "data_processed" / "landmarks"
METADATA_PATH = Path("ml") / "metadata.csv"
HAND_MODEL_PATH = Path("ml") / "models" / "hand_landmarker.task"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
EXTRACTION_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_9_full_landmark_extraction_report.csv"
EXTRACTION_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_9_full_landmark_extraction_report.md"
CHECK_REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_9_full_landmark_check.csv"
CHECK_REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_9_full_landmark_check.md"


def repetitions_for_label(label: str) -> int:
    """Return the fixed trial or full-collection repetition count for a label."""
    if label in TRIAL_LABELS:
        return TRIAL_REPETITIONS
    if label in FULL_COLLECTION_LABELS:
        return FULL_COLLECTION_REPETITIONS
    raise ValueError(f"Label is outside the Sprint 2.9 collection scope: {label}")


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the stable ID shared by raw videos, outputs, and metadata."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_paths(participant_id: str, label: str, repetition: int) -> dict[str, Path]:
    """Return the raw video, landmark, and mask paths for one expected sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return {
        "video": RAW_VIDEO_DIR / label / f"{sample_id}.mp4",
        "landmarks": LANDMARK_DIR / label / f"{sample_id}_landmarks.npy",
        "mask": LANDMARK_DIR / label / f"{sample_id}_mask.npy",
    }


def iter_expected_samples(participant_id: str = FULL_DATASET_PARTICIPANT) -> list[dict[str, object]]:
    """Build every expected trial and full-collection sample in stable label order."""
    samples: list[dict[str, object]] = []
    for label in ALL_LABELS_V1:
        for repetition in range(1, repetitions_for_label(label) + 1):
            paths = expected_paths(participant_id, label, repetition)
            samples.append(
                {
                    "sample_id": build_sample_id(participant_id, label, repetition),
                    "participant_id": participant_id,
                    "label": label,
                    "repetition": repetition,
                    **paths,
                }
            )
    return samples


def validate_full_landmark_config() -> None:
    """Validate Sprint 2.9 scope before extraction or verification uses it."""
    if len(ALL_LABELS_V1) != EXPECTED_SCOPED_LABELS:
        raise ValueError(f"Expected {EXPECTED_SCOPED_LABELS} labels, found {len(ALL_LABELS_V1)}.")
    if len(TRIAL_LABELS) != EXPECTED_TRIAL_LABELS:
        raise ValueError(f"Expected {EXPECTED_TRIAL_LABELS} trial labels, found {len(TRIAL_LABELS)}.")
    if len(FULL_COLLECTION_LABELS) != EXPECTED_FULL_COLLECTION_LABELS:
        raise ValueError(
            f"Expected {EXPECTED_FULL_COLLECTION_LABELS} full collection labels, "
            f"found {len(FULL_COLLECTION_LABELS)}."
        )
    if "payment" not in ALL_LABELS_V1 or "payment" not in FULL_COLLECTION_LABELS:
        raise ValueError("Sprint 2.9 expects payment in the full collection label scope.")
    if "receipt" in ALL_LABELS_V1 or "receipt" in FULL_COLLECTION_LABELS:
        raise ValueError("Sprint 2.9 must not include receipt in the label scope.")
    if LANDMARK_OUTPUT_DIMENSION != 126 or HAND_MASK_DIMENSION != 2:
        raise ValueError("Sprint 2.9 must use a 126-value landmark row and a 2-value hand mask.")
    if EXPECTED_TOTAL_RAW_VIDEOS != 505:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_RAW_VIDEOS} raw videos, found a different scope."
        )
    if len(iter_expected_samples()) != EXPECTED_TOTAL_RAW_VIDEOS:
        raise ValueError("Expected sample generation does not match the Sprint 2.9 total.")


validate_full_landmark_config()

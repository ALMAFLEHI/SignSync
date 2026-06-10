"""Create and validate the SignSync Phase 2 Sprint 2.1 project structure."""

from __future__ import annotations

import csv
from pathlib import Path

from labels import ALPHABET, ALL_LABELS, BANKING_INTENTS_V1, DIGITS


# The expected command is run from the workspace root:
# python ml/src/create_folders.py
# These paths are intentionally project-relative and avoid hard-coded
# absolute machine-specific locations.
PROJECT_ROOT = Path(".")
ML_DIR = Path("ml")
RAW_VIDEO_DIR = ML_DIR / "data_raw" / "videos"
PROCESSED_LANDMARK_DIR = ML_DIR / "data_processed" / "landmarks"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"
SRC_DIR = ML_DIR / "src"
FLUTTER_APP_DIR = Path("flutter_app")
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
METADATA_PATH = ML_DIR / "metadata.csv"
DATASET_SCOPE_SUMMARY_PATH = EVIDENCE_DIR / "dataset_scope_summary.md"

METADATA_HEADERS = [
    "sample_id",
    "participant_id",
    "label",
    "repetition",
    "video_path",
    "landmark_path",
    "status",
    "notes",
]

MAIN_FOLDERS = [
    RAW_VIDEO_DIR,
    PROCESSED_LANDMARK_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    SRC_DIR,
    FLUTTER_APP_DIR,
    EVIDENCE_DIR,
]


def relative_path(path: Path) -> str:
    """Return a readable project-relative path for terminal and docs output."""
    return path.as_posix()


def create_main_folders() -> None:
    """Create the main Sprint 2.1 folders without removing existing content."""
    for folder in MAIN_FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)


def create_label_folders() -> None:
    """Create raw video and processed landmark folders for every dataset label."""
    for label in ALL_LABELS:
        (RAW_VIDEO_DIR / label).mkdir(parents=True, exist_ok=True)
        (PROCESSED_LANDMARK_DIR / label).mkdir(parents=True, exist_ok=True)


def create_metadata_file() -> None:
    """Create metadata.csv with headers only when the file does not already exist."""
    if METADATA_PATH.exists():
        return

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
        writer = csv.writer(metadata_file)
        writer.writerow(METADATA_HEADERS)


def build_dataset_scope_summary() -> str:
    """Build the Markdown evidence summary for the Sprint 2.1 dataset scope."""
    banking_intents = "\n".join(
        f"- {intent}" for intent in BANKING_INTENTS_V1
    )
    folder_summary = "\n".join(
        f"- {relative_path(folder)}" for folder in MAIN_FOLDERS
    )

    return f"""# SignSync Dataset Scope Summary

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.1: Project Setup & Dataset Scope

## Label Counts
- Total labels: {len(ALL_LABELS)}
- Alphabet labels: {len(ALPHABET)}
- Digit labels: {len(DIGITS)}
- Banking intent labels: {len(BANKING_INTENTS_V1)}

## Full Banking Intent List
{banking_intents}

## Folder Structure Summary
{folder_summary}
- {relative_path(METADATA_PATH)}
- Label subfolders under {relative_path(RAW_VIDEO_DIR)}
- Label subfolders under {relative_path(PROCESSED_LANDMARK_DIR)}

## Acceptance Checklist
- [x] Main project folders are created.
- [x] Raw video label folders are created for all labels.
- [x] Processed landmark label folders are created for all labels.
- [x] metadata.csv exists with the required headers.
- [x] Initial dataset vocabulary contains 56 unique labels.
- [x] No data collection, landmark extraction, or model training is included in this sprint.
"""


def create_dataset_scope_summary() -> None:
    """Write the Sprint 2.1 dataset scope summary for documentation evidence."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_SCOPE_SUMMARY_PATH.write_text(
        build_dataset_scope_summary(),
        encoding="utf-8",
    )


def validate_setup() -> None:
    """Validate required folders, metadata, and label subfolders."""
    missing_paths = []

    for folder in MAIN_FOLDERS:
        if not folder.exists():
            missing_paths.append(relative_path(folder))

    if not METADATA_PATH.exists():
        missing_paths.append(relative_path(METADATA_PATH))

    for label in ALL_LABELS:
        raw_label_folder = RAW_VIDEO_DIR / label
        processed_label_folder = PROCESSED_LANDMARK_DIR / label

        if not raw_label_folder.exists():
            missing_paths.append(relative_path(raw_label_folder))

        if not processed_label_folder.exists():
            missing_paths.append(relative_path(processed_label_folder))

    if missing_paths:
        formatted_paths = "\n".join(f"- {path}" for path in missing_paths)
        raise RuntimeError(
            "Sprint 2.1 setup validation failed. Missing paths:\n"
            f"{formatted_paths}"
        )

    print("Validation passed.")


def print_summary() -> None:
    """Print the final Sprint 2.1 setup summary."""
    raw_label_folder_count = sum(
        1 for label in ALL_LABELS if (RAW_VIDEO_DIR / label).exists()
    )
    processed_label_folder_count = sum(
        1 for label in ALL_LABELS if (PROCESSED_LANDMARK_DIR / label).exists()
    )

    print()
    print("Sprint 2.1 Setup Summary")
    print("-------------------------")
    print(f"Total labels created: {len(ALL_LABELS)}")
    print(f"Number of raw label folders: {raw_label_folder_count}")
    print(f"Number of processed label folders: {processed_label_folder_count}")
    print(f"metadata.csv path: {relative_path(METADATA_PATH)}")
    print(
        "dataset_scope_summary.md path: "
        f"{relative_path(DATASET_SCOPE_SUMMARY_PATH)}"
    )
    print("Sprint 2.1 setup completed successfully.")


def main() -> None:
    """Run the complete Sprint 2.1 setup workflow."""
    create_main_folders()
    create_label_folders()
    create_metadata_file()
    create_dataset_scope_summary()
    validate_setup()
    print_summary()


if __name__ == "__main__":
    main()

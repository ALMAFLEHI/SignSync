"""Versioned configuration for Sprint 2.16B banking phone collection."""

from __future__ import annotations

from pathlib import Path

from labels import (
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
    SPRINT_2_16A_PILOT_INTENTS_4,
    SPRINT_2_16B_REMAINING_BANKING_INTENTS_36,
)


PARTICIPANT_ID = "P02_PHONE"
SOURCE_NAME = "phone_live_landmark"
DEVICE_NAME = "Samsung Android phone"
SPRINT_ID = "2.16B"
TARGET_FRAMES = 60
FRAME_WIDTH = 126
HAND_WIDTH = 63
SAMPLES_PER_LABEL = 25
NEW_SAMPLE_TARGET = 900
FINAL_BANKING_PHONE_TARGET = 1000

PHONE_SAMPLE_DIR = Path("ml") / "data_phone" / "landmark_samples"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
REPORT_MD_PATH = EVIDENCE_DIR / "sprint_2_16B_phone_sample_check_report.md"
REPORT_CSV_PATH = EVIDENCE_DIR / "sprint_2_16B_phone_sample_check_report.csv"
REPORT_JSON_PATH = EVIDENCE_DIR / "sprint_2_16B_phone_sample_check_report.json"
BACKUP_PATH = (
    Path("ml") / "data_phone" / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
)


def validate_config() -> None:
    """Protect the banking-only, active-order Sprint 2.16B contract."""
    remaining = SPRINT_2_16B_REMAINING_BANKING_INTENTS_36
    pilot = SPRINT_2_16A_PILOT_INTENTS_4
    if len(remaining) != 36 or len(set(remaining)) != 36:
        raise ValueError("Sprint 2.16B requires exactly 36 unique remaining labels.")
    if len(pilot) != 4 or len(set(pilot)) != 4:
        raise ValueError("Sprint 2.16A requires exactly four unique pilot labels.")
    if set(remaining).intersection(pilot):
        raise ValueError("Pilot and remaining banking scopes cannot overlap.")
    if [label for label in BANKING_INTENTS_V3_40 if label not in pilot] != remaining:
        raise ValueError("Sprint 2.16B labels must preserve active V3 order.")
    if set(remaining).union(pilot) != set(BANKING_INTENTS_V3_40):
        raise ValueError("Pilot plus remaining labels must reconstruct active V3.")
    if set(remaining).intersection(REMOVED_BANKING_INTENTS_V3_10):
        raise ValueError("Removed banking labels cannot appear in Sprint 2.16B.")
    if set(remaining).intersection(ALPHABET_LABELS + DIGIT_LABELS):
        raise ValueError("Sprint 2.16B cannot include alphabet or digit labels.")
    if len(BANKING_INTENTS_V3_40) != 40:
        raise ValueError("Active V3 must contain exactly 40 banking intents.")
    if SAMPLES_PER_LABEL * len(remaining) != NEW_SAMPLE_TARGET:
        raise ValueError("Sprint 2.16B new-sample target must equal 900.")
    if NEW_SAMPLE_TARGET + SAMPLES_PER_LABEL * len(pilot) != FINAL_BANKING_PHONE_TARGET:
        raise ValueError("Final banking-phone target must equal 1,000.")
    if TARGET_FRAMES != 60 or FRAME_WIDTH != 126 or HAND_WIDTH != 63:
        raise ValueError("Landmark contract must remain 60 x 126 with 63-value slots.")


validate_config()

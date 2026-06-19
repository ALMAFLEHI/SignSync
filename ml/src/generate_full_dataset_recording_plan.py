"""Create the Sprint 2.7 plan for completing the remaining SignSync labels."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from labels import ALPHABET, ALL_LABELS, BANKING_INTENTS_V1, DIGITS
from pipeline_validation_config import (
    FULL_DATASET_RECORDING_PLAN_CSV,
    FULL_DATASET_RECORDING_PLAN_MD,
    LABEL_MAPPING_PATH,
    READINESS_DECISION_MD,
    REMAINING_LABELS_CSV,
    report_path,
)


TRIAL_LABELS = [
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


def label_category(label: str) -> str:
    """Classify labels for a readable full-dataset recording plan."""
    if label in ALPHABET:
        return "alphabet"
    if label in DIGITS:
        return "digit"
    if label in BANKING_INTENTS_V1:
        return "banking_intent"
    raise ValueError(f"Label is outside the approved Sprint 2.1 vocabulary: {label}")


def load_recorded_trial_labels() -> list[str]:
    """Load trial labels from the Sprint 2.5 mapping and validate their expected set."""
    mapping = json.loads(Path(LABEL_MAPPING_PATH).read_text(encoding="utf-8"))
    recorded_labels = list(mapping.keys())
    if set(recorded_labels) != set(TRIAL_LABELS) or len(recorded_labels) != len(TRIAL_LABELS):
        raise ValueError(
            "Sprint 2.5 label mapping does not contain the expected 11 trial labels."
        )
    return recorded_labels


def write_remaining_labels(remaining_labels: list[str]) -> Path:
    """Write a concise CSV of labels that still need full dataset recordings."""
    output_path = report_path(REMAINING_LABELS_CSV)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["label", "category", "recommended_participant", "minimum_repetitions"],
        )
        writer.writeheader()
        for label in remaining_labels:
            writer.writerow(
                {
                    "label": label,
                    "category": label_category(label),
                    "recommended_participant": "P02",
                    "minimum_repetitions": 5,
                }
            )
    return output_path


def write_recording_plan_csv(remaining_labels: list[str]) -> Path:
    """Write one actionable Stage 1 plan row for every remaining label."""
    output_path = report_path(FULL_DATASET_RECORDING_PLAN_CSV)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "stage",
                "recording_order",
                "participant",
                "label",
                "category",
                "minimum_repetitions",
                "camera_index",
                "quality_check",
            ],
        )
        writer.writeheader()
        for order, label in enumerate(remaining_labels, start=1):
            writer.writerow(
                {
                    "stage": "Stage 1",
                    "recording_order": order,
                    "participant": "P02",
                    "label": label,
                    "category": label_category(label),
                    "minimum_repetitions": 5,
                    "camera_index": 1,
                    "quality_check": "hand fully visible; stable lighting; plain background",
                }
            )
    return output_path


def write_plan_markdown(recorded_labels: list[str], remaining_labels: list[str]) -> Path:
    """Write the FYP evidence plan and its recording-quality rules."""
    output_path = report_path(FULL_DATASET_RECORDING_PLAN_MD)
    remaining_list = ", ".join(remaining_labels)
    recorded_list = ", ".join(recorded_labels)
    content = f"""# Sprint 2.7 Full Dataset Recording Plan

## Coverage Summary
- Total scoped labels: {len(ALL_LABELS)}
- Already recorded trial labels: {len(recorded_labels)}
- Remaining labels: {len(remaining_labels)}
- Already recorded: {recorded_list}
- Remaining: {remaining_list}

## Recommended Recording Stages
### Stage 1: Complete the First Full-Label Dataset
- Record all {len(remaining_labels)} remaining labels for participant P02.
- Record 5 repetitions per label first ({len(remaining_labels) * 5} new recordings).
- Use camera index 1.
- This completes one full-label dataset version with 56 labels.

### Stage 2: Increase Repetitions
- Add more repetitions when time allows.
- Recommended target: 10 to 20 repetitions per label.

### Stage 3: Add Participants
- Add more participants when possible.
- More participants improve generalization and enable cross-participant testing.

## Recording Quality Rules
- Use the same camera index 1.
- Keep the hand visible.
- Keep stable lighting.
- Keep a plain background.
- Keep the same distance from the camera.
- For static signs, hold the gesture clearly.
- For movement signs, perform the movement once clearly and hold the final position.
- Re-record if the hand is cut off or landmark detection will likely fail.

## Checks After Recording
- Confirm metadata rows are created correctly.
- Confirm every new video is clean and has no preview overlay.
- Extract and verify two-hand landmarks.
- Rebuild and verify the training dataset only after the recordings are complete.
- Keep raw videos and generated dataset files out of Git.

## Output Files
- Remaining labels CSV: {report_path(REMAINING_LABELS_CSV).as_posix()}
- Recording plan CSV: {report_path(FULL_DATASET_RECORDING_PLAN_CSV).as_posix()}
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_readiness_decision() -> Path:
    """Write a clear decision that authorizes planning, not automatic recording."""
    output_path = report_path(READINESS_DECISION_MD)
    content = """# Sprint 2.7 Readiness Decision

## Decision
- Sprint 2.6 pipeline works.
- Sprint 2.7 validates the saved pipeline and identifies trial dataset limitations.
- The project is ready to move to full dataset recording after Sprint 2.7 is confirmed.

## Boundary
This report does not record videos, change metadata, retrain the model, create TensorFlow Lite files, or create Flutter integration.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> int:
    """Generate planning evidence only; do not collect videos or alter metadata."""
    if len(ALL_LABELS) != 56:
        raise ValueError(f"Expected 56 scoped labels, found {len(ALL_LABELS)}.")

    recorded_labels = load_recorded_trial_labels()
    remaining_labels = [label for label in ALL_LABELS if label not in recorded_labels]
    if len(recorded_labels) != 11 or len(remaining_labels) != 45:
        raise ValueError(
            f"Expected 11 recorded and 45 remaining labels, found "
            f"{len(recorded_labels)} recorded and {len(remaining_labels)} remaining."
        )

    remaining_path = write_remaining_labels(remaining_labels)
    plan_csv_path = write_recording_plan_csv(remaining_labels)
    plan_md_path = write_plan_markdown(recorded_labels, remaining_labels)
    readiness_path = write_readiness_decision()

    print("Sprint 2.7 Full Dataset Recording Plan")
    print("---------------------------------------")
    print(f"total labels: {len(ALL_LABELS)}")
    print(f"recorded trial labels: {len(recorded_labels)}")
    print(f"remaining labels: {len(remaining_labels)}")
    print(f"Stage 1 P02 recordings recommended: {len(remaining_labels) * 5}")
    print(f"remaining labels CSV: {remaining_path.as_posix()}")
    print(f"recording plan CSV: {plan_csv_path.as_posix()}")
    print(f"recording plan Markdown: {plan_md_path.as_posix()}")
    print(f"readiness decision: {readiness_path.as_posix()}")
    print("PASS: Full dataset recording plan generated. No videos were recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

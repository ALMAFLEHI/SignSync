"""Analyze Sprint 2.4 landmark quality before Sprint 2.5 dataset preparation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from dataset_config import (
    EXPECTED_SAMPLES,
    LANDMARK_DIM,
    MASK_DIM,
    PARTICIPANT_ID,
    QUALITY_REPORT_CSV_PATH,
    QUALITY_REPORT_MD_PATH,
)
from trial_config import TRIAL_LABELS


METADATA_PATH = Path("ml") / "metadata.csv"
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


def parse_args() -> argparse.Namespace:
    """Parse quality-check options."""
    parser = argparse.ArgumentParser(
        description="Analyze Sprint 2.4 landmark quality for Sprint 2.5."
    )
    parser.add_argument("--participant", default=PARTICIPANT_ID)
    parser.add_argument("--min-detection-rate", type=float, default=0.80)
    return parser.parse_args()


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the expected trial sample ID."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def mask_path_from_landmark_path(landmark_path: Path) -> Path:
    """Infer the matching mask file path from the landmark file path."""
    if landmark_path.name.endswith("_landmarks.npy"):
        return landmark_path.with_name(
            landmark_path.name.replace("_landmarks.npy", "_mask.npy")
        )
    return landmark_path.with_name(f"{landmark_path.stem}_mask.npy")


def read_metadata_rows() -> list[dict[str, str]]:
    """Read metadata.csv with a clear header validation."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError("ml/metadata.csv is missing.")

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
        return list(reader)


def metadata_index(rows: list[dict[str, str]], participant_id: str) -> dict[str, dict[str, str]]:
    """Index successful landmark metadata rows by sample ID."""
    indexed_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("participant_id") != participant_id:
            continue
        if row.get("status") != "landmarks_extracted":
            continue
        if row.get("label") not in TRIAL_LABELS:
            continue
        sample_id = row.get("sample_id", "")
        if sample_id:
            indexed_rows[sample_id] = row
    return indexed_rows


def expected_sample_ids(participant_id: str) -> list[tuple[str, str, int]]:
    """Return the expected 55 Sprint 2.3 trial sample IDs."""
    samples: list[tuple[str, str, int]] = []
    for label in TRIAL_LABELS:
        for repetition in range(1, 6):
            samples.append((build_sample_id(participant_id, label, repetition), label, repetition))
    return samples


def analyze_one_sample(
    sample_id: str,
    label: str,
    repetition: int,
    row: dict[str, str] | None,
    min_detection_rate: float,
) -> dict[str, str]:
    """Check one landmark and mask pair and return a CSV-ready report row."""
    issues: list[str] = []
    landmark_path_text = row.get("landmark_path", "") if row else ""
    landmark_path = Path(landmark_path_text) if landmark_path_text else Path()
    mask_path = mask_path_from_landmark_path(landmark_path) if landmark_path_text else Path()

    total_frames = 0
    left_frames = 0
    right_frames = 0
    any_hand_frames = 0
    two_hand_frames = 0
    any_hand_rate = 0.0
    two_hand_rate = 0.0
    landmark_shape = ""
    mask_shape = ""
    landmark_shape_valid = False
    mask_shape_valid = False
    no_nan = False
    no_inf = False

    landmarks = None
    mask = None

    if row is None:
        issues.append("missing landmarks_extracted metadata row")
    elif not landmark_path_text:
        issues.append("missing landmark_path in metadata")

    if landmark_path_text and not landmark_path.exists():
        issues.append("missing landmark file")

    if landmark_path_text and not mask_path.exists():
        issues.append("missing mask file")

    if landmark_path_text and landmark_path.exists():
        try:
            landmarks = np.load(landmark_path)
            landmark_shape = str(tuple(landmarks.shape))
            landmark_shape_valid = landmarks.ndim == 2 and landmarks.shape[1] == LANDMARK_DIM
            if not landmark_shape_valid:
                issues.append(f"landmark shape must be 2D with second dimension {LANDMARK_DIM}")
            no_nan = not np.isnan(landmarks).any()
            no_inf = not np.isinf(landmarks).any()
            if not no_nan:
                issues.append("landmarks contain NaN values")
            if not no_inf:
                issues.append("landmarks contain infinite values")
        except Exception as exc:
            issues.append(f"could not load landmark file: {exc}")

    if landmark_path_text and mask_path.exists():
        try:
            mask = np.load(mask_path)
            mask_shape = str(tuple(mask.shape))
            mask_shape_valid = mask.ndim == 2 and mask.shape[1] == MASK_DIM
            if not mask_shape_valid:
                issues.append(f"mask shape must be 2D with second dimension {MASK_DIM}")
        except Exception as exc:
            issues.append(f"could not load mask file: {exc}")

    if landmarks is not None and mask is not None:
        if mask.shape[0] != landmarks.shape[0]:
            issues.append("landmark and mask frame counts do not match")
        total_frames = int(landmarks.shape[0])

    if mask is not None and mask.ndim == 2 and mask.shape[1] == MASK_DIM:
        left_frames = int(np.count_nonzero(mask[:, 0]))
        right_frames = int(np.count_nonzero(mask[:, 1]))
        any_hand_frames = int(np.count_nonzero(np.any(mask > 0, axis=1)))
        two_hand_frames = int(np.count_nonzero(np.all(mask > 0, axis=1)))
        if mask.shape[0] > 0:
            any_hand_rate = any_hand_frames / mask.shape[0]
            two_hand_rate = two_hand_frames / mask.shape[0]
        if any_hand_rate < min_detection_rate:
            issues.append(
                f"any-hand detection rate below {min_detection_rate:.2f}"
            )

    passed = (
        row is not None
        and landmark_shape_valid
        and mask_shape_valid
        and no_nan
        and no_inf
        and any_hand_rate >= min_detection_rate
        and not issues
    )

    return {
        "sample_id": sample_id,
        "label": label,
        "repetition": str(repetition),
        "landmark_path": landmark_path.as_posix() if landmark_path_text else "",
        "mask_path": mask_path.as_posix() if landmark_path_text else "",
        "landmark_exists": "yes" if landmark_path_text and landmark_path.exists() else "no",
        "mask_exists": "yes" if landmark_path_text and mask_path.exists() else "no",
        "landmark_shape": landmark_shape,
        "mask_shape": mask_shape,
        "total_frames": str(total_frames),
        "left_hand_detected_frames": str(left_frames),
        "right_hand_detected_frames": str(right_frames),
        "any_hand_detected_frames": str(any_hand_frames),
        "two_hand_detected_frames": str(two_hand_frames),
        "any_hand_detection_rate": f"{any_hand_rate:.4f}",
        "two_hand_detection_rate": f"{two_hand_rate:.4f}",
        "passed": "yes" if passed else "no",
        "issues": "; ".join(issues),
    }


def write_csv_report(report_rows: list[dict[str, str]]) -> None:
    """Save the detailed landmark quality report."""
    QUALITY_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "landmark_path",
        "mask_path",
        "landmark_exists",
        "mask_exists",
        "landmark_shape",
        "mask_shape",
        "total_frames",
        "left_hand_detected_frames",
        "right_hand_detected_frames",
        "any_hand_detected_frames",
        "two_hand_detected_frames",
        "any_hand_detection_rate",
        "two_hand_detection_rate",
        "passed",
        "issues",
    ]
    with QUALITY_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)


def write_markdown_report(
    report_rows: list[dict[str, str]],
    min_detection_rate: float,
    participant_id: str,
) -> None:
    """Save a concise Markdown summary for FYP evidence."""
    passed_rows = [row for row in report_rows if row["passed"] == "yes"]
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    failed_text = (
        "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows)
        if failed_rows
        else "- None"
    )
    content = f"""# Sprint 2.5 Landmark Quality Report

## Participant
{participant_id}

## Quality Rule
A sample passes if landmark and mask shapes are valid, there are no NaN or infinite values, and any-hand detection rate is at least {min_detection_rate:.2f}.

## Summary
- Expected samples: {EXPECTED_SAMPLES}
- Checked samples: {len(report_rows)}
- Passed samples: {len(passed_rows)}
- Failed samples: {len(failed_rows)}

## Failed Samples
{failed_text}

## Report Files
- CSV report: {QUALITY_REPORT_CSV_PATH.as_posix()}
- Markdown report: {QUALITY_REPORT_MD_PATH.as_posix()}
"""
    QUALITY_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_summary(report_rows: list[dict[str, str]]) -> None:
    """Print the quality-check summary."""
    passed_rows = [row for row in report_rows if row["passed"] == "yes"]
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.5 Landmark Quality Summary")
    print("------------------------------------")
    print(f"expected samples: {EXPECTED_SAMPLES}")
    print(f"checked samples: {len(report_rows)}")
    print(f"passed samples: {len(passed_rows)}")
    print(f"failed samples: {len(failed_rows)}")
    print(f"CSV report path: {QUALITY_REPORT_CSV_PATH.as_posix()}")
    print(f"Markdown report path: {QUALITY_REPORT_MD_PATH.as_posix()}")
    if not failed_rows and len(report_rows) == EXPECTED_SAMPLES:
        print("Sprint 2.5 landmark quality check passed.")
    else:
        print("Sprint 2.5 landmark quality check failed.")


def main() -> int:
    """Run the Sprint 2.5 landmark quality analysis."""
    args = parse_args()
    rows = read_metadata_rows()
    indexed_rows = metadata_index(rows, args.participant)
    report_rows = [
        analyze_one_sample(sample_id, label, repetition, indexed_rows.get(sample_id), args.min_detection_rate)
        for sample_id, label, repetition in expected_sample_ids(args.participant)
    ]
    write_csv_report(report_rows)
    write_markdown_report(report_rows, args.min_detection_rate, args.participant)
    print_summary(report_rows)

    all_passed = all(row["passed"] == "yes" for row in report_rows)
    return 0 if all_passed and len(report_rows) == EXPECTED_SAMPLES else 1


if __name__ == "__main__":
    raise SystemExit(main())

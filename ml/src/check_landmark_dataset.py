"""Verify Sprint 2.4 landmark arrays and metadata updates."""

from __future__ import annotations

import argparse
import csv
import importlib
from pathlib import Path
from typing import Any

from trial_config import DEFAULT_PARTICIPANT_ID, DEFAULT_REPETITIONS, TRIAL_LABELS


LANDMARK_DIR = Path("ml") / "data_processed" / "landmarks"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
CSV_REPORT_PATH = EVIDENCE_DIR / "sprint_2_4_landmark_dataset_check.csv"
MARKDOWN_REPORT_PATH = EVIDENCE_DIR / "sprint_2_4_landmark_dataset_check.md"

VALID_METADATA_STATUSES = {"landmarks_extracted", "landmark_detection_failed"}
EXPECTED_LANDMARK_DIMENSION = 126
EXPECTED_MASK_DIMENSION = 2


def parse_args() -> argparse.Namespace:
    """Parse landmark dataset verification options."""
    parser = argparse.ArgumentParser(
        description="Verify Sprint 2.4 landmark output files and metadata."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    return parser.parse_args()


def import_numpy() -> Any:
    """Import NumPy with a clear install hint."""
    try:
        return importlib.import_module("numpy")
    except ImportError as exc:
        raise ImportError(
            "numpy is required. Install with: "
            "python -m pip install -r requirements_sprint_2_4.txt"
        ) from exc


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the expected sample ID."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def landmark_paths(participant_id: str, label: str, repetition: int) -> tuple[Path, Path]:
    """Return expected landmark and mask paths for one sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return (
        LANDMARK_DIR / label / f"{sample_id}_landmarks.npy",
        LANDMARK_DIR / label / f"{sample_id}_mask.npy",
    )


def read_metadata() -> dict[str, list[dict[str, str]]]:
    """Read metadata rows grouped by sample_id."""
    grouped_rows: dict[str, list[dict[str, str]]] = {}
    if not METADATA_PATH.exists():
        return grouped_rows

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        for row in reader:
            sample_id = row.get("sample_id", "")
            grouped_rows.setdefault(sample_id, []).append(row)

    return grouped_rows


def check_one_sample(
    numpy: Any,
    participant_id: str,
    label: str,
    repetition: int,
    metadata_rows: dict[str, list[dict[str, str]]],
) -> dict[str, str]:
    """Check files, shapes, mask length, and metadata for one sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    landmark_path, mask_path = landmark_paths(participant_id, label, repetition)
    issues: list[str] = []
    frame_count = ""
    landmark_shape = ""
    mask_shape = ""

    if not landmark_path.exists():
        issues.append("missing landmark file")
    if not mask_path.exists():
        issues.append("missing mask file")

    if landmark_path.exists():
        try:
            landmarks = numpy.load(landmark_path)
            landmark_shape = str(tuple(landmarks.shape))
            if landmarks.ndim != 2:
                issues.append("landmark array is not 2D")
            elif landmarks.shape[1] != EXPECTED_LANDMARK_DIMENSION:
                issues.append(
                    f"landmark second dimension is not {EXPECTED_LANDMARK_DIMENSION}"
                )
            frame_count = str(landmarks.shape[0]) if landmarks.ndim >= 1 else ""
        except Exception as exc:  # noqa: BLE001 - report array load errors clearly.
            issues.append(f"could not load landmark file: {exc}")
            landmarks = None
    else:
        landmarks = None

    if mask_path.exists():
        try:
            mask = numpy.load(mask_path)
            mask_shape = str(tuple(mask.shape))
            if mask.ndim != 2:
                issues.append("mask array is not 2D")
            elif mask.shape[1] != EXPECTED_MASK_DIMENSION:
                issues.append(f"mask second dimension is not {EXPECTED_MASK_DIMENSION}")
            if landmarks is not None and mask.shape[0] != landmarks.shape[0]:
                issues.append("mask length does not match frame count")
        except Exception as exc:  # noqa: BLE001 - report array load errors clearly.
            issues.append(f"could not load mask file: {exc}")

    rows = metadata_rows.get(sample_id, [])
    status = rows[0].get("status", "") if rows else ""
    landmark_path_in_metadata = rows[0].get("landmark_path", "") if rows else ""

    if not rows:
        issues.append("missing metadata row")
    elif status not in VALID_METADATA_STATUSES:
        issues.append("metadata status is not a Sprint 2.4 status")
    elif status == "landmarks_extracted" and not landmark_path_in_metadata:
        issues.append("successful sample missing landmark_path in metadata")

    return {
        "sample_id": sample_id,
        "label": label,
        "repetition": str(repetition),
        "landmark_path": landmark_path.as_posix(),
        "mask_path": mask_path.as_posix(),
        "landmark_shape": landmark_shape,
        "mask_shape": mask_shape,
        "frame_count": frame_count,
        "metadata_status": status,
        "passed": "yes" if not issues else "no",
        "issues": "; ".join(issues),
    }


def write_reports(report_rows: list[dict[str, str]], passed: bool) -> None:
    """Write CSV and Markdown verification reports."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "landmark_path",
        "mask_path",
        "landmark_shape",
        "mask_shape",
        "frame_count",
        "metadata_status",
        "passed",
        "issues",
    ]
    with CSV_REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    failed_text = (
        "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows)
        if failed_rows
        else "- None"
    )
    content = f"""# Sprint 2.4 Landmark Dataset Check

## Expected Format
- Expected landmark dimension: {EXPECTED_LANDMARK_DIMENSION}
- Expected mask dimension: {EXPECTED_MASK_DIMENSION}
- Landmark shape: `number_of_frames x {EXPECTED_LANDMARK_DIMENSION}`
- Mask shape: `number_of_frames x {EXPECTED_MASK_DIMENSION}`

## Result
{"PASS" if passed else "FAIL"}

## Failed Items
{failed_text}

## Report Files
- CSV report: {CSV_REPORT_PATH.as_posix()}
- Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}
"""
    MARKDOWN_REPORT_PATH.write_text(content, encoding="utf-8")


def print_summary(report_rows: list[dict[str, str]], passed: bool) -> None:
    """Print a concise verification summary."""
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    print("Sprint 2.4 Landmark Dataset Verification Summary")
    print("------------------------------------------------")
    print(f"expected samples: {len(report_rows)}")
    print(f"failed items: {len(failed_rows)}")
    print(f"CSV report: {CSV_REPORT_PATH.as_posix()}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}")

    if passed:
        print("Sprint 2.4 landmark dataset verification passed.")
    else:
        print("Sprint 2.4 landmark dataset verification failed.")
        for row in failed_rows[:20]:
            print(f"- {row['sample_id']}: {row['issues']}")


def main() -> int:
    """Verify all expected Sprint 2.4 landmark outputs."""
    args = parse_args()
    try:
        numpy = import_numpy()
    except ImportError as exc:
        print(f"Error: {exc}")
        return 1

    metadata_rows = read_metadata()
    report_rows = [
        check_one_sample(numpy, args.participant, label, repetition, metadata_rows)
        for label in TRIAL_LABELS
        for repetition in range(1, args.repetitions + 1)
    ]
    passed = all(row["passed"] == "yes" for row in report_rows)
    write_reports(report_rows, passed)
    print_summary(report_rows, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Inspect Sprint 2.9 full landmark and mask output quality before preparation."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import numpy as np

from full_dataset_config import (
    EXPECTED_SAMPLES,
    FULL_DATASET_PARTICIPANT,
    LANDMARK_DIMENSION,
    MASK_DIMENSION,
    QUALITY_REPORT_CSV_PATH,
    QUALITY_REPORT_MD_PATH,
    iter_expected_samples,
)


def parse_args() -> argparse.Namespace:
    """Parse the participant whose full landmark files are inspected."""
    parser = argparse.ArgumentParser(
        description="Analyze Sprint 2.9 full landmark and mask output quality."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    return parser.parse_args()


def analyze_sample(sample: dict[str, object]) -> dict[str, str]:
    """Validate one landmark/mask pair and calculate hand-coverage statistics."""
    landmark_path = Path(sample["landmark_path"])
    mask_path = Path(sample["mask_path"])
    issues: list[str] = []
    landmarks = None
    mask = None
    if not landmark_path.exists():
        issues.append("missing landmark file")
    if not mask_path.exists():
        issues.append("missing mask file")
    if not issues:
        try:
            landmarks = np.load(landmark_path, allow_pickle=False)
            mask = np.load(mask_path, allow_pickle=False)
        except Exception as exc:  # noqa: BLE001 - surface corrupt output cleanly.
            issues.append(f"could not load arrays: {exc}")

    frame_count = 0
    any_hand_rate = 0.0
    two_hand_rate = 0.0
    all_zero = False
    landmark_shape = ""
    mask_shape = ""
    if landmarks is not None and mask is not None:
        landmark_shape = str(tuple(landmarks.shape))
        mask_shape = str(tuple(mask.shape))
        if landmarks.ndim != 2 or landmarks.shape[1] != LANDMARK_DIMENSION:
            issues.append(f"landmark shape must be frames x {LANDMARK_DIMENSION}")
        if mask.ndim != 2 or mask.shape[1] != MASK_DIMENSION:
            issues.append(f"mask shape must be frames x {MASK_DIMENSION}")
        if landmarks.ndim == 2 and landmarks.shape[0] < 1:
            issues.append("landmark array contains no frames")
        if landmarks.ndim == 2 and mask.ndim == 2 and landmarks.shape[0] != mask.shape[0]:
            issues.append("landmark and mask frame counts do not match")
        if not issues:
            frame_count = int(landmarks.shape[0])
            any_hand_rate = float(np.any(mask > 0, axis=1).mean() * 100)
            two_hand_rate = float(np.all(mask > 0, axis=1).mean() * 100)
            all_zero = bool(np.all(landmarks == 0))

    return {
        "sample_id": str(sample["sample_id"]),
        "label": str(sample["label"]),
        "repetition": str(sample["repetition"]),
        "landmark_path": landmark_path.as_posix(),
        "mask_path": mask_path.as_posix(),
        "landmark_shape": landmark_shape,
        "mask_shape": mask_shape,
        "frame_count": str(frame_count),
        "any_hand_frames_percent": f"{any_hand_rate:.2f}",
        "two_hand_frames_percent": f"{two_hand_rate:.2f}",
        "all_zero_sample": "yes" if all_zero else "no",
        "passed": "yes" if not issues else "no",
        "issues": "; ".join(issues),
    }


def write_reports(report_rows: list[dict[str, str]]) -> None:
    """Save quality CSV and Markdown reports suitable for FYP evidence."""
    QUALITY_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(report_rows[0]) if report_rows else []
    with QUALITY_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    all_zero_rows = [row for row in report_rows if row["all_zero_sample"] == "yes"]
    average_any_hand = (
        sum(float(row["any_hand_frames_percent"]) for row in report_rows) / len(report_rows)
        if report_rows else 0.0
    )
    average_two_hands = (
        sum(float(row["two_hand_frames_percent"]) for row in report_rows) / len(report_rows)
        if report_rows else 0.0
    )
    failed_text = "\n".join(f"- {row['sample_id']}: {row['issues']}" for row in failed_rows) if failed_rows else "- None"
    zero_text = "\n".join(f"- {row['sample_id']}" for row in all_zero_rows) if all_zero_rows else "- None"
    content = f"""# Sprint 2.10 Full Landmark Quality Report

## Scope
- Expected samples: {EXPECTED_SAMPLES}
- Checked samples: {len(report_rows)}
- Structurally valid samples: {len(report_rows) - len(failed_rows)}
- Invalid or missing samples: {len(failed_rows)}
- All-zero landmark samples: {len(all_zero_rows)}
- Average frames with any detected hand: {average_any_hand:.2f}%
- Average frames with two detected hands: {average_two_hands:.2f}%

## Invalid Or Missing Samples
{failed_text}

## All-Zero Samples
{zero_text}

## Output Files
- CSV report: {QUALITY_REPORT_CSV_PATH.as_posix()}
- Markdown report: {QUALITY_REPORT_MD_PATH.as_posix()}
"""
    QUALITY_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Analyze every expected full-dataset landmark pair without modifying it."""
    args = parse_args()
    report_rows = [analyze_sample(sample) for sample in iter_expected_samples(args.participant)]
    write_reports(report_rows)
    failed_rows = [row for row in report_rows if row["passed"] == "no"]
    all_zero_rows = [row for row in report_rows if row["all_zero_sample"] == "yes"]
    print("Sprint 2.10 Full Landmark Quality Summary")
    print("------------------------------------------")
    print(f"expected samples: {EXPECTED_SAMPLES}")
    print(f"checked samples: {len(report_rows)}")
    print(f"valid samples: {len(report_rows) - len(failed_rows)}")
    print(f"invalid or missing samples: {len(failed_rows)}")
    print(f"all-zero landmark samples: {len(all_zero_rows)}")
    print(f"CSV report: {QUALITY_REPORT_CSV_PATH.as_posix()}")
    print(f"Markdown report: {QUALITY_REPORT_MD_PATH.as_posix()}")
    print("PASS: full landmark quality analysis passed." if not failed_rows else "FAIL: review the quality report.")
    return 0 if not failed_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())

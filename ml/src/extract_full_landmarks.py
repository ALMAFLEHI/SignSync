"""Extract Tasks API two-hand landmarks for the full Sprint 2.9 raw dataset."""

from __future__ import annotations

import argparse
import csv
import importlib
from collections import Counter
from pathlib import Path
from typing import Any

from extract_landmarks import (
    assign_hands_to_fixed_layout,
    average_landmark_x,
    handedness_from_group,
    safe_fps,
)
from full_landmark_extraction_config import (
    EXPECTED_TOTAL_RAW_VIDEOS,
    EXTRACTION_REPORT_CSV_PATH,
    EXTRACTION_REPORT_MD_PATH,
    FULL_DATASET_PARTICIPANT,
    HAND_MASK_DIMENSION,
    HAND_MODEL_PATH,
    LANDMARK_OUTPUT_DIMENSION,
    METADATA_PATH,
    iter_expected_samples,
)


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
    """Parse safe full-dataset extraction options."""
    parser = argparse.ArgumentParser(
        description="Extract Sprint 2.9 full-dataset MediaPipe Tasks hand landmarks."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--label", default=None)
    selection.add_argument("--start-label", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def import_required_runtime() -> tuple[Any, Any, Any]:
    """Import extraction dependencies only when real processing is requested."""
    modules: dict[str, Any] = {}
    missing: list[str] = []
    for import_name, package_name in [
        ("cv2", "opencv-python"),
        ("mediapipe", "mediapipe"),
        ("numpy", "numpy"),
    ]:
        try:
            modules[import_name] = importlib.import_module(import_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        raise ImportError(
            "Missing packages for Sprint 2.9 extraction: "
            f"{', '.join(missing)}. Install with: "
            "python -m pip install -r requirements_sprint_2_4.txt"
        )
    return modules["cv2"], modules["mediapipe"], modules["numpy"]


def create_tasks_hand_detector(mediapipe: Any) -> Any:
    """Create the local MediaPipe Tasks HandLandmarker used for one input video."""
    if not HAND_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"MediaPipe Tasks model is missing: {HAND_MODEL_PATH.as_posix()}"
        )
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL_PATH.as_posix()),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


def detect_tasks_hands(
    detector: Any, mediapipe: Any, rgb_frame: Any, frame_index: int, fps: float
) -> list[dict[str, object]]:
    """Return up to two Tasks API detections for one RGB frame."""
    timestamp_ms = int((frame_index * 1000) / max(fps, 1.0))
    mp_image = mediapipe.Image(
        image_format=mediapipe.ImageFormat.SRGB,
        data=rgb_frame,
    )
    result = detector.detect_for_video(mp_image, timestamp_ms)
    detections: list[dict[str, object]] = []
    handedness_groups = result.handedness or []
    for index, landmarks in enumerate(result.hand_landmarks[:2]):
        landmark_list = list(landmarks)
        detections.append(
            {
                "landmarks": landmark_list,
                "handedness": handedness_from_group(
                    handedness_groups[index] if index < len(handedness_groups) else []
                ),
                "average_x": average_landmark_x(landmark_list),
            }
        )
    return detections


def read_metadata_index() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Read metadata rows by sample ID without modifying the collection record."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {METADATA_PATH.as_posix()}")
    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)
        if reader.fieldnames != METADATA_HEADERS:
            raise ValueError(
                "metadata.csv headers are incorrect. Expected: "
                f"{', '.join(METADATA_HEADERS)}"
            )
        rows_by_id: dict[str, list[dict[str, str]]] = {}
        for row in reader:
            sample_id = row.get("sample_id", "").strip()
            if sample_id:
                rows_by_id.setdefault(sample_id, []).append(row)
    duplicates = sorted(
        sample_id for sample_id, rows in rows_by_id.items() if len(rows) > 1
    )
    return rows_by_id, duplicates


def select_samples(
    participant_id: str, label: str | None, start_label: str | None
) -> list[dict[str, object]]:
    """Select one label, a resume point, or the whole stable-order full dataset."""
    samples = iter_expected_samples(participant_id)
    labels = []
    for sample in samples:
        sample_label = str(sample["label"])
        if sample_label not in labels:
            labels.append(sample_label)

    if label is not None:
        if label not in labels:
            raise ValueError(f"--label is not in the Sprint 2.9 scope: {label}")
        return [sample for sample in samples if sample["label"] == label]
    if start_label is not None:
        if start_label not in labels:
            raise ValueError(f"--start-label is not in the Sprint 2.9 scope: {start_label}")
        start_index = labels.index(start_label)
        selected_labels = set(labels[start_index:])
        return [sample for sample in samples if sample["label"] in selected_labels]
    return samples


def dry_run_summary(samples: list[dict[str, object]], metadata_index: dict[str, list[dict[str, str]]]) -> None:
    """Print planned inputs and outputs without importing MediaPipe or writing files."""
    by_label = Counter(str(sample["label"]) for sample in samples)
    missing_videos = [sample for sample in samples if not Path(sample["video"]).exists()]
    missing_metadata = [
        sample for sample in samples if not metadata_index.get(str(sample["sample_id"]))
    ]
    existing_outputs = [
        sample
        for sample in samples
        if Path(sample["landmarks"]).exists() and Path(sample["mask"]).exists()
    ]
    print("Sprint 2.9 Full Landmark Extraction Dry Run")
    print("-------------------------------------------")
    print(f"participant: {samples[0]['participant_id'] if samples else 'none'}")
    print(f"selected labels: {len(by_label)}")
    print(f"selected expected videos: {len(samples)}")
    print(f"full expected videos: {EXPECTED_TOTAL_RAW_VIDEOS}")
    print(f"existing complete landmark outputs: {len(existing_outputs)}")
    print(f"missing raw videos: {len(missing_videos)}")
    print(f"missing metadata rows: {len(missing_metadata)}")
    print("planned labels:")
    for label, count in by_label.items():
        print(f"- {label}: {count} sample(s)")
    print("Dry run completed. No videos processed and no .npy files written.")


def extract_one_sample(sample: dict[str, object], cv2: Any, mediapipe: Any, numpy: Any) -> dict[str, object]:
    """Extract 126-value landmark rows and two-value masks for one raw video."""
    video_path = Path(sample["video"])
    landmark_path = Path(sample["landmarks"])
    mask_path = Path(sample["mask"])
    if not video_path.exists():
        return {**sample, "status": "missing_video", "frames": 0, "issues": "input video missing"}

    capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        return {**sample, "status": "video_open_failed", "frames": 0, "issues": "could not open input video"}

    detector = None
    landmark_rows: list[list[float]] = []
    mask_rows: list[list[int]] = []
    frame_index = 0
    try:
        detector = create_tasks_hand_detector(mediapipe)
        fps = safe_fps(capture.get(cv2.CAP_PROP_FPS))
        while True:
            success, frame = capture.read()
            if not success:
                break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detections = detect_tasks_hands(detector, mediapipe, rgb_frame, frame_index, fps)
            landmarks, mask = assign_hands_to_fixed_layout(detections)
            landmark_rows.append(landmarks)
            mask_rows.append(mask)
            frame_index += 1
    except Exception as exc:  # noqa: BLE001 - report sample-level extraction failures.
        return {**sample, "status": "extraction_failed", "frames": frame_index, "issues": str(exc)}
    finally:
        if detector is not None:
            detector.close()
        capture.release()

    if not landmark_rows:
        return {**sample, "status": "empty_video", "frames": 0, "issues": "video contains no readable frames"}

    landmarks_array = numpy.asarray(landmark_rows, dtype=numpy.float32)
    mask_array = numpy.asarray(mask_rows, dtype=numpy.uint8)
    landmark_path.parent.mkdir(parents=True, exist_ok=True)
    numpy.save(landmark_path, landmarks_array)
    numpy.save(mask_path, mask_array)
    any_hand_frames = sum(1 for mask in mask_rows if mask[0] or mask[1])
    return {
        **sample,
        "status": "landmarks_extracted",
        "frames": len(landmark_rows),
        "issues": "",
        "any_hand_frames": any_hand_frames,
    }


def skipped_result(sample: dict[str, object]) -> dict[str, object]:
    """Represent an existing complete output without reprocessing it."""
    return {**sample, "status": "skipped_existing", "frames": "", "issues": "", "any_hand_frames": ""}


def report_value(value: object) -> object:
    """Format path values safely for CSV reports."""
    return value.as_posix() if isinstance(value, Path) else value


def write_reports(results: list[dict[str, object]], duplicate_metadata_ids: list[str]) -> None:
    """Write extraction evidence without modifying raw videos or metadata."""
    EXTRACTION_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id", "label", "repetition", "video", "landmarks", "mask", "status", "frames", "any_hand_frames", "issues"
    ]
    with EXTRACTION_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({field: report_value(result.get(field, "")) for field in fieldnames})

    counts = Counter(str(result["status"]) for result in results)
    failed = [
        result for result in results
        if result["status"] not in {"landmarks_extracted", "skipped_existing"}
    ]
    failed_text = (
        "\n".join(f"- {item['sample_id']}: {item['issues']}" for item in failed)
        if failed else "- None"
    )
    duplicates_text = "\n".join(f"- {item}" for item in duplicate_metadata_ids) if duplicate_metadata_ids else "- None"
    content = f"""# Sprint 2.9 Full Landmark Extraction Report

## Format
- Landmark output: frames x {LANDMARK_OUTPUT_DIMENSION}
- Hand mask output: frames x {HAND_MASK_DIMENSION}
- API: MediaPipe Tasks HandLandmarker using `{HAND_MODEL_PATH.as_posix()}`

## Summary
- Selected samples: {len(results)}
- Extracted: {counts['landmarks_extracted']}
- Skipped existing: {counts['skipped_existing']}
- Failed or missing: {len(failed)}

## Failed Or Missing Items
{failed_text}

## Duplicate Metadata Sample IDs
{duplicates_text}
"""
    EXTRACTION_REPORT_MD_PATH.write_text(content, encoding="utf-8")


def print_summary(results: list[dict[str, object]]) -> None:
    """Print the final extraction status for the manual confirmed run."""
    counts = Counter(str(result["status"]) for result in results)
    failures = sum(
        count for status, count in counts.items() if status not in {"landmarks_extracted", "skipped_existing"}
    )
    print("Sprint 2.9 Full Landmark Extraction Summary")
    print("-------------------------------------------")
    print(f"total selected videos: {len(results)}")
    print(f"landmarks extracted: {counts['landmarks_extracted']}")
    print(f"existing outputs skipped: {counts['skipped_existing']}")
    print(f"failed or missing: {failures}")
    print(f"CSV report: {EXTRACTION_REPORT_CSV_PATH.as_posix()}")
    print(f"Markdown report: {EXTRACTION_REPORT_MD_PATH.as_posix()}")
    print("PASS: extraction completed." if failures == 0 else "FAIL: review the extraction report.")


def main() -> int:
    """Run a dry-run or extract only missing landmark outputs for selected samples."""
    args = parse_args()
    try:
        samples = select_samples(args.participant, args.label, args.start_label)
        metadata_index, duplicate_metadata_ids = read_metadata_index()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if args.dry_run:
        dry_run_summary(samples, metadata_index)
        return 0

    try:
        cv2, mediapipe, numpy = import_required_runtime()
    except ImportError as exc:
        print(f"Error: {exc}")
        return 1

    results: list[dict[str, object]] = []
    for sample in samples:
        metadata_rows = metadata_index.get(str(sample["sample_id"]), [])
        if not metadata_rows:
            results.append({**sample, "status": "missing_metadata", "frames": 0, "any_hand_frames": 0, "issues": "metadata row missing"})
            continue
        if len(metadata_rows) > 1:
            results.append({**sample, "status": "duplicate_metadata", "frames": 0, "any_hand_frames": 0, "issues": "duplicate metadata rows"})
            continue
        if not args.overwrite and Path(sample["landmarks"]).exists() and Path(sample["mask"]).exists():
            results.append(skipped_result(sample))
            continue
        results.append(extract_one_sample(sample, cv2, mediapipe, numpy))

    write_reports(results, duplicate_metadata_ids)
    print_summary(results)
    failures = any(
        result["status"] not in {"landmarks_extracted", "skipped_existing"}
        for result in results
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

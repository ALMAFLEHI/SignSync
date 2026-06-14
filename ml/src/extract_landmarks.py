"""Extract MediaPipe hand landmarks from Sprint 2.3 trial videos."""

from __future__ import annotations

import argparse
import csv
import importlib
import shutil
from pathlib import Path
from typing import Any

from trial_config import DEFAULT_PARTICIPANT_ID, DEFAULT_REPETITIONS, TRIAL_LABELS


RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"
LANDMARK_DIR = Path("ml") / "data_processed" / "landmarks"
DEFAULT_HAND_MODEL_PATH = Path("ml") / "models" / "hand_landmarker.task"
METADATA_PATH = Path("ml") / "metadata.csv"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
METADATA_BACKUP_PATH = EVIDENCE_DIR / "metadata_backup_before_sprint_2_4_landmarks.csv"
CSV_REPORT_PATH = EVIDENCE_DIR / "sprint_2_4_landmark_extraction_report.csv"
MARKDOWN_REPORT_PATH = EVIDENCE_DIR / "sprint_2_4_landmark_extraction_report.md"

LANDMARK_VALUES_PER_HAND = 21 * 3
TWO_HAND_LANDMARK_VALUES = LANDMARK_VALUES_PER_HAND * 2
HAND_MASK_VALUES = 2

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
    """Parse extraction options."""
    parser = argparse.ArgumentParser(
        description="Extract MediaPipe hand landmarks from Sprint 2.3 trial videos."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--min-detection-rate", type=float, default=0.80)
    parser.add_argument("--model-path", default=DEFAULT_HAND_MODEL_PATH.as_posix())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def import_required_runtime() -> tuple[Any, Any, Any]:
    """Import runtime packages only when real extraction is requested."""
    missing_packages: list[str] = []
    modules: dict[str, Any] = {}

    for import_name, package_name in [
        ("cv2", "opencv-python"),
        ("mediapipe", "mediapipe"),
        ("numpy", "numpy"),
    ]:
        try:
            modules[import_name] = importlib.import_module(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        raise ImportError(
            "Missing packages for Sprint 2.4 extraction: "
            f"{', '.join(missing_packages)}. Install with: "
            "python -m pip install -r requirements_sprint_2_4.txt"
        )

    return modules["cv2"], modules["mediapipe"], modules["numpy"]


def create_hand_detector(mediapipe: Any, model_path: Path) -> tuple[str, Any, Any]:
    """Create a MediaPipe hand detector for legacy or Tasks-only installs."""
    if hasattr(mediapipe, "solutions"):
        hands_solution = mediapipe.solutions.hands
        detector = hands_solution.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        return "legacy_solutions", detector, hands_solution

    if not model_path.exists():
        raise FileNotFoundError(
            "MediaPipe Tasks HandLandmarker model is missing. Expected model path: "
            f"{model_path.as_posix()}. Download hand_landmarker.task into ml/models "
            "or pass --model-path."
        )

    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path.as_posix()),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    detector = vision.HandLandmarker.create_from_options(options)
    return "tasks", detector, vision


def detect_hand_landmarks(
    api_name: str,
    detector: Any,
    mediapipe: Any,
    cv2: Any,
    rgb_frame: Any,
    frame_index: int,
    fps: float,
) -> list[dict[str, object]]:
    """Return up to two detected hands with landmarks and handedness data."""
    if api_name == "legacy_solutions":
        results = detector.process(rgb_frame)
        if not results.multi_hand_landmarks:
            return []

        handedness_groups = results.multi_handedness or []
        detections: list[dict[str, object]] = []
        for index, hand_landmarks in enumerate(results.multi_hand_landmarks[:2]):
            handedness = handedness_from_group(
                handedness_groups[index].classification
                if index < len(handedness_groups)
                else []
            )
            landmarks = list(hand_landmarks.landmark)
            detections.append(
                {
                    "landmarks": landmarks,
                    "handedness": handedness,
                    "average_x": average_landmark_x(landmarks),
                }
            )
        return detections

    timestamp_ms = int((frame_index * 1000) / max(fps, 1.0))
    mp_image = mediapipe.Image(
        image_format=mediapipe.ImageFormat.SRGB,
        data=rgb_frame,
    )
    results = detector.detect_for_video(mp_image, timestamp_ms)
    if not results.hand_landmarks:
        return []

    handedness_groups = results.handedness or []
    detections = []
    for index, hand_landmarks in enumerate(results.hand_landmarks[:2]):
        handedness = handedness_from_group(
            handedness_groups[index] if index < len(handedness_groups) else []
        )
        landmarks = list(hand_landmarks)
        detections.append(
            {
                "landmarks": landmarks,
                "handedness": handedness,
                "average_x": average_landmark_x(landmarks),
            }
        )
    return detections


def handedness_from_group(categories: Any) -> str:
    """Return normalized MediaPipe handedness label when available."""
    if not categories:
        return ""

    category = categories[0]
    raw_label = (
        getattr(category, "category_name", "")
        or getattr(category, "label", "")
        or ""
    )
    normalized = str(raw_label).strip().lower()
    if normalized.startswith("left"):
        return "left"
    if normalized.startswith("right"):
        return "right"
    return ""


def average_landmark_x(landmarks: list[Any]) -> float:
    """Calculate average normalized x-position for fallback left/right ordering."""
    if not landmarks:
        return 0.5
    return sum(float(landmark.x) for landmark in landmarks) / len(landmarks)


def landmark_values(landmarks: list[Any]) -> list[float]:
    """Flatten 21 hand landmarks into x, y, z values and pad if needed."""
    values: list[float] = []
    for landmark in landmarks[:21]:
        values.extend([landmark.x, landmark.y, landmark.z])

    if len(values) < LANDMARK_VALUES_PER_HAND:
        values.extend([0.0] * (LANDMARK_VALUES_PER_HAND - len(values)))

    return values[:LANDMARK_VALUES_PER_HAND]


def assign_hands_to_fixed_layout(
    detections: list[dict[str, object]]
) -> tuple[list[float], list[int]]:
    """Return a 126-value row and [left, right] detection mask.

    MediaPipe handedness is used first. If handedness is missing, duplicated, or
    otherwise not enough to place a detected hand, the fallback uses image-space
    x-position: smaller average x goes to the left slot and larger average x
    goes to the right slot.
    """
    hand_slots = [[0.0] * LANDMARK_VALUES_PER_HAND, [0.0] * LANDMARK_VALUES_PER_HAND]
    mask = [0, 0]
    unassigned: list[dict[str, object]] = []

    for detection in detections[:2]:
        handedness = str(detection.get("handedness", ""))
        slot_index = 0 if handedness == "left" else 1 if handedness == "right" else None
        if slot_index is not None and mask[slot_index] == 0:
            hand_slots[slot_index] = landmark_values(detection["landmarks"])
            mask[slot_index] = 1
        else:
            unassigned.append(detection)

    free_slots = [slot_index for slot_index, detected in enumerate(mask) if detected == 0]
    if unassigned and free_slots:
        if len(unassigned) == 1 and len(free_slots) == 2:
            average_x = float(unassigned[0].get("average_x", 0.5))
            slot_index = 0 if average_x <= 0.5 else 1
            hand_slots[slot_index] = landmark_values(unassigned[0]["landmarks"])
            mask[slot_index] = 1
        else:
            ordered_hands = sorted(
                unassigned,
                key=lambda detection: float(detection.get("average_x", 0.5)),
            )
            for detection, slot_index in zip(ordered_hands, free_slots):
                hand_slots[slot_index] = landmark_values(detection["landmarks"])
                mask[slot_index] = 1

    return hand_slots[0] + hand_slots[1], mask


def safe_fps(raw_fps: float) -> float:
    """Use a stable fallback FPS when OpenCV reports an invalid value."""
    return raw_fps if raw_fps and raw_fps > 0 else 20.0


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the sample ID shared by videos, landmarks, masks, and metadata."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def expected_paths(participant_id: str, label: str, repetition: int) -> dict[str, Path]:
    """Return all expected paths for one trial sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return {
        "video": RAW_VIDEO_DIR / label / f"{sample_id}.mp4",
        "landmarks": LANDMARK_DIR / label / f"{sample_id}_landmarks.npy",
        "mask": LANDMARK_DIR / label / f"{sample_id}_mask.npy",
    }


def iter_expected_samples(participant_id: str, repetitions: int) -> list[dict[str, object]]:
    """Build the expected Sprint 2.4 sample list."""
    samples: list[dict[str, object]] = []
    for label in TRIAL_LABELS:
        for repetition in range(1, repetitions + 1):
            paths = expected_paths(participant_id, label, repetition)
            samples.append(
                {
                    "sample_id": build_sample_id(participant_id, label, repetition),
                    "label": label,
                    "repetition": repetition,
                    **paths,
                }
            )
    return samples


def print_dry_run(samples: list[dict[str, object]]) -> None:
    """Print expected inputs and outputs without writing files."""
    print("Sprint 2.4 Landmark Extraction Dry Run")
    print("--------------------------------------")
    for sample in samples:
        print(f"{sample['sample_id']}")
        print(f"  input: {Path(sample['video']).as_posix()}")
        print(f"  landmarks: {Path(sample['landmarks']).as_posix()}")
        print(f"  mask: {Path(sample['mask']).as_posix()}")

    print()
    print(f"total expected videos: {len(samples)}")
    print("No videos processed, no .npy files written, metadata unchanged.")


def extract_one_sample(
    sample: dict[str, object],
    cv2: Any,
    mediapipe: Any,
    numpy: Any,
    min_detection_rate: float,
    model_path: Path,
) -> dict[str, object]:
    """Extract landmarks and mask arrays for one video sample."""
    video_path = Path(sample["video"])
    landmark_path = Path(sample["landmarks"])
    mask_path = Path(sample["mask"])
    landmark_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        return {
            **sample,
            "total_frames": 0,
            "left_hand_detected_frames": 0,
            "right_hand_detected_frames": 0,
            "any_hand_detected_frames": 0,
            "two_hands_detected_frames": 0,
            "any_hand_detection_rate": 0.0,
            "two_hand_detection_rate": 0.0,
            "status": "missing_video",
            "issues": "input video missing",
        }

    landmark_rows: list[list[float]] = []
    mask_values: list[list[int]] = []
    frame_index = 0

    capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        return {
            **sample,
            "total_frames": 0,
            "left_hand_detected_frames": 0,
            "right_hand_detected_frames": 0,
            "any_hand_detected_frames": 0,
            "two_hands_detected_frames": 0,
            "any_hand_detection_rate": 0.0,
            "two_hand_detection_rate": 0.0,
            "status": "video_open_failed",
            "issues": "could not open input video",
        }

    fps = safe_fps(capture.get(cv2.CAP_PROP_FPS))
    detector = None

    try:
        api_name, detector, _ = create_hand_detector(mediapipe, model_path)
        while True:
            success, frame = capture.read()
            if not success:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detections = detect_hand_landmarks(
                api_name,
                detector,
                mediapipe,
                cv2,
                rgb_frame,
                frame_index,
                fps,
            )
            frame_index += 1

            row, mask = assign_hands_to_fixed_layout(detections)
            landmark_rows.append(row)
            mask_values.append(mask)
    finally:
        if detector is not None:
            detector.close()
        capture.release()

    total_frames = len(mask_values)
    left_hand_detected_frames = sum(mask[0] for mask in mask_values)
    right_hand_detected_frames = sum(mask[1] for mask in mask_values)
    any_hand_detected_frames = sum(1 for mask in mask_values if mask[0] or mask[1])
    two_hands_detected_frames = sum(1 for mask in mask_values if mask[0] and mask[1])
    any_hand_detection_rate = (
        any_hand_detected_frames / total_frames if total_frames else 0.0
    )
    two_hand_detection_rate = (
        two_hands_detected_frames / total_frames if total_frames else 0.0
    )
    passed = any_hand_detection_rate >= min_detection_rate

    landmarks_array = numpy.asarray(landmark_rows, dtype=numpy.float32)
    if total_frames == 0:
        landmarks_array = numpy.zeros((0, TWO_HAND_LANDMARK_VALUES), dtype=numpy.float32)
    mask_array = numpy.asarray(mask_values, dtype=numpy.uint8)
    if total_frames == 0:
        mask_array = numpy.zeros((0, HAND_MASK_VALUES), dtype=numpy.uint8)

    numpy.save(landmark_path, landmarks_array)
    numpy.save(mask_path, mask_array)

    return {
        **sample,
        "total_frames": total_frames,
        "left_hand_detected_frames": left_hand_detected_frames,
        "right_hand_detected_frames": right_hand_detected_frames,
        "any_hand_detected_frames": any_hand_detected_frames,
        "two_hands_detected_frames": two_hands_detected_frames,
        "any_hand_detection_rate": any_hand_detection_rate,
        "two_hand_detection_rate": two_hand_detection_rate,
        "status": "landmarks_extracted" if passed else "landmark_detection_failed",
        "issues": "" if passed else "any-hand detection rate below threshold",
    }


def read_metadata_rows() -> list[dict[str, str]]:
    """Read metadata.csv with a clear header check."""
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


def update_metadata(results: list[dict[str, object]], participant_id: str) -> None:
    """Update existing metadata rows without adding duplicates."""
    rows = read_metadata_rows()
    result_by_sample_id = {
        str(result["sample_id"]): result
        for result in results
        if result["status"] in {"landmarks_extracted", "landmark_detection_failed"}
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(METADATA_PATH, METADATA_BACKUP_PATH)

    for row in rows:
        if row.get("participant_id") != participant_id:
            continue

        sample_id = row.get("sample_id", "")
        result = result_by_sample_id.get(sample_id)
        if not result:
            continue

        row["landmark_path"] = Path(result["landmarks"]).as_posix()
        row["status"] = str(result["status"])

    with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
        writer = csv.DictWriter(metadata_file, fieldnames=METADATA_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def write_reports(results: list[dict[str, object]]) -> None:
    """Write CSV and Markdown extraction reports."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "video",
        "landmarks",
        "mask",
        "total_frames",
        "left_hand_detected_frames",
        "right_hand_detected_frames",
        "any_hand_detected_frames",
        "two_hands_detected_frames",
        "any_hand_detection_rate",
        "two_hand_detection_rate",
        "status",
        "issues",
    ]
    with CSV_REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    key: format_report_value(key, result[key])
                    for key in fieldnames
                }
            )

    passed = [result for result in results if result["status"] == "landmarks_extracted"]
    failed = [result for result in results if result["status"] == "landmark_detection_failed"]
    skipped = [result for result in results if result["status"] == "skipped_existing"]
    missing = [result for result in results if result["status"] == "missing_video"]

    failed_text = (
        "\n".join(f"- {item['sample_id']}: {item['issues']}" for item in failed + missing)
        if failed or missing
        else "- None"
    )
    content = f"""# Sprint 2.4 Landmark Extraction Report

## Landmark Format
- Landmark shape: `number_of_frames x 126`
- Columns `0-62`: left hand landmarks
- Columns `63-125`: right hand landmarks
- Mask shape: `number_of_frames x 2`
- Mask column `0`: left hand detected
- Mask column `1`: right hand detected

## Summary
- Total expected videos: {len(results)}
- Passed: {len(passed)}
- Failed: {len(failed)}
- Skipped existing: {len(skipped)}
- Missing videos: {len(missing)}

## Failed Or Missing Items
{failed_text}

## Report Files
- CSV report: {CSV_REPORT_PATH.as_posix()}
- Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}
"""
    MARKDOWN_REPORT_PATH.write_text(content, encoding="utf-8")


def format_report_value(key: str, value: object) -> object:
    """Format report values while allowing skipped rows to contain blanks."""
    if key in {"any_hand_detection_rate", "two_hand_detection_rate"} and isinstance(
        value, (float, int)
    ):
        return f"{value:.4f}"
    if key in {"video", "landmarks", "mask"}:
        return Path(value).as_posix()
    return value


def print_summary(results: list[dict[str, object]]) -> None:
    """Print the final extraction summary."""
    processed = [
        result
        for result in results
        if result["status"] in {"landmarks_extracted", "landmark_detection_failed"}
    ]
    skipped = [result for result in results if result["status"] == "skipped_existing"]
    passed = [result for result in results if result["status"] == "landmarks_extracted"]
    failed = [result for result in results if result["status"] == "landmark_detection_failed"]

    print()
    print("Sprint 2.4 Landmark Extraction Summary")
    print("--------------------------------------")
    print(f"total expected videos: {len(results)}")
    print(f"processed count: {len(processed)}")
    print(f"skipped existing count: {len(skipped)}")
    print(f"passed count: {len(passed)}")
    print(f"failed count: {len(failed)}")
    print(f"CSV report: {CSV_REPORT_PATH.as_posix()}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH.as_posix()}")
    print("next command: python ml/src/check_landmark_dataset.py --participant P02")


def main() -> int:
    """Run dry-run or real Sprint 2.4 landmark extraction."""
    args = parse_args()
    samples = iter_expected_samples(args.participant, args.repetitions)

    if args.dry_run:
        print_dry_run(samples)
        return 0

    try:
        cv2, mediapipe, numpy = import_required_runtime()
        results: list[dict[str, object]] = []
        for sample in samples:
            landmark_path = Path(sample["landmarks"])
            mask_path = Path(sample["mask"])
            if (landmark_path.exists() or mask_path.exists()) and not args.overwrite:
                results.append(
                    {
                        **sample,
                        "total_frames": "",
                        "left_hand_detected_frames": "",
                        "right_hand_detected_frames": "",
                        "any_hand_detected_frames": "",
                        "two_hands_detected_frames": "",
                        "any_hand_detection_rate": "",
                        "two_hand_detection_rate": "",
                        "status": "skipped_existing",
                        "issues": "landmark output already exists",
                    }
                )
                continue

            results.append(
                extract_one_sample(
                    sample,
                    cv2,
                    mediapipe,
                    numpy,
                    args.min_detection_rate,
                    Path(args.model_path),
                )
            )

        update_metadata(results, args.participant)
        write_reports(results)
        print_summary(results)
        return 0

    except (ImportError, OSError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

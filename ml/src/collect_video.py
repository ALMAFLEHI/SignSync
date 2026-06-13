"""Collect raw SignSync gesture videos for Phase 2, Sprint 2.2."""

from __future__ import annotations

import argparse
import csv
import importlib
import re
import time
from pathlib import Path
from typing import Any

from labels import ALPHABET, ALL_LABELS, BANKING_INTENTS_V1, DIGITS


PROJECT_NAME = "SignSync"
WINDOW_TITLE = "SignSync Data Collection"

ML_DIR = Path("ml")
RAW_VIDEO_DIR = ML_DIR / "data_raw" / "videos"
METADATA_PATH = ML_DIR / "metadata.csv"

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


def check_opencv_installed() -> Any:
    """Import OpenCV only when recording is needed and explain how to install it."""
    try:
        return importlib.import_module("cv2")
    except ImportError as exc:
        raise ImportError(
            "OpenCV is not installed. Install it with: pip install opencv-python"
        ) from exc


def parse_args() -> argparse.Namespace:
    """Parse command-line options for one raw video recording sample."""
    parser = argparse.ArgumentParser(
        description="Record one raw SignSync gesture video sample."
    )
    parser.add_argument("--participant", required=True, help="Participant ID, e.g. P01")
    parser.add_argument("--label", required=True, help="Dataset label, e.g. deposit")
    parser.add_argument("--repetition", required=True, type=int, help="Positive integer")
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam index")
    parser.add_argument("--frames", type=int, default=60, help="Frames to record")
    parser.add_argument("--fps", type=int, default=20, help="Target recording FPS")
    parser.add_argument("--width", type=int, default=640, help="Camera frame width")
    parser.add_argument("--height", type=int, default=480, help="Camera frame height")
    parser.add_argument("--notes", default="", help="Optional metadata notes")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing video file for the same sample ID",
    )
    return parser.parse_args()


def list_available_labels() -> None:
    """Print the Sprint 2.1 labels grouped for easy correction by the user."""
    print("Available labels:")
    print(f"Alphabet: {', '.join(ALPHABET)}")
    print(f"Digits: {', '.join(DIGITS)}")
    print(f"Banking intents: {', '.join(BANKING_INTENTS_V1)}")


def validate_participant_id(participant_id: str) -> str:
    """Validate participant IDs such as P01, P02, and P03."""
    normalized_participant_id = participant_id.strip().upper()
    if not re.fullmatch(r"P\d{2,}", normalized_participant_id):
        raise ValueError(
            "Invalid participant ID. Expected format is P followed by at least "
            "two digits, for example P01, P02, or P03."
        )
    return normalized_participant_id


def validate_label(label: str) -> str:
    """Validate the requested label against the Sprint 2.1 vocabulary."""
    normalized_label = label.strip()
    if normalized_label not in ALL_LABELS:
        print(f"Invalid label: {normalized_label}")
        list_available_labels()
        raise ValueError("Label must exist in ml/src/labels.py ALL_LABELS.")
    return normalized_label


def validate_positive_integer(value: int, field_name: str) -> int:
    """Keep numeric recording settings clear and safe."""
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer.")
    return value


def is_cancel_key(key_code: int) -> bool:
    """Treat either q or Q as a safe recording cancellation request."""
    normalized_key = key_code & 0xFF
    return normalized_key in (ord("q"), ord("Q"))


def ensure_metadata_file() -> None:
    """Create metadata.csv with the required headers if it does not exist."""
    if not METADATA_PATH.exists():
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
            writer = csv.writer(metadata_file)
            writer.writerow(METADATA_HEADERS)

    validate_metadata_headers()


def validate_metadata_headers() -> None:
    """Stop recording if metadata.csv exists with unexpected headers."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError("metadata.csv does not exist.")

    with METADATA_PATH.open("r", newline="", encoding="utf-8") as metadata_file:
        reader = csv.reader(metadata_file)
        headers = next(reader, None)

    if headers != METADATA_HEADERS:
        raise ValueError(
            "metadata.csv headers are incorrect. Expected headers are: "
            f"{', '.join(METADATA_HEADERS)}"
        )


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the standard sample ID used for the filename and metadata row."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def append_metadata(
    sample_id: str,
    participant_id: str,
    label: str,
    repetition: int,
    video_path: Path,
    notes: str,
) -> None:
    """Append one metadata row only after a successful complete recording."""
    with METADATA_PATH.open("a", newline="", encoding="utf-8") as metadata_file:
        writer = csv.writer(metadata_file)
        writer.writerow(
            [
                sample_id,
                participant_id,
                label,
                repetition,
                video_path.as_posix(),
                "",
                "raw_recorded",
                notes,
            ]
        )


def draw_overlay(
    cv2: Any,
    frame: Any,
    participant_id: str,
    label: str,
    repetition: int,
    frame_number: int,
    total_frames: int,
    status_text: str,
) -> Any:
    """Draw the live collection details on top of the webcam frame."""
    lines = [
        PROJECT_NAME,
        f"Participant: {participant_id}",
        f"Label: {label}",
        f"Repetition: R{repetition:02d}",
        f"Frames: {frame_number}/{total_frames}",
        "Press Q to cancel",
    ]

    for index, line in enumerate(lines):
        y_position = 30 + index * 28
        cv2.putText(
            frame,
            line,
            (20, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    if status_text:
        cv2.putText(
            frame,
            status_text,
            (220, 250),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.4,
            (0, 255, 0),
            3,
            cv2.LINE_AA,
        )

    return frame


def show_countdown(
    cv2: Any,
    capture: Any,
    participant_id: str,
    label: str,
    repetition: int,
    total_frames: int,
    width: int,
    height: int,
) -> bool:
    """Show 3, 2, 1, Recording before writing video frames."""
    for countdown_text in ["3", "2", "1", "Recording"]:
        countdown_seconds = 0.7 if countdown_text == "Recording" else 1.0
        end_time = time.monotonic() + countdown_seconds

        while time.monotonic() < end_time:
            success, frame = capture.read()
            if not success:
                raise RuntimeError("Could not read frames from the webcam.")

            frame = cv2.resize(frame, (width, height))
            frame = draw_overlay(
                cv2,
                frame,
                participant_id,
                label,
                repetition,
                0,
                total_frames,
                countdown_text,
            )
            cv2.imshow(WINDOW_TITLE, frame)

            if is_cancel_key(cv2.waitKey(1)):
                return False

    return True


def record_video(
    participant_id: str,
    label: str,
    repetition: int,
    output_path: Path,
    camera_index: int,
    frames: int,
    fps: int,
    width: int,
    height: int,
    overwrite: bool,
) -> int | None:
    """Record exactly the requested frames unless the user cancels with Q."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Output video already exists: {output_path.as_posix()}. "
                "Use --overwrite to replace it."
            )
        output_path.unlink()

    cv2 = check_opencv_installed()
    capture = cv2.VideoCapture(camera_index)
    writer = None
    recorded_frames = 0
    cancelled = False

    try:
        if not capture.isOpened():
            raise RuntimeError(
                "Could not open webcam. Possible fixes: check camera permissions, "
                "close other apps using the camera, or try --camera-index 1."
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        capture.set(cv2.CAP_PROP_FPS, fps)

        cv2.namedWindow(WINDOW_TITLE)

        countdown_completed = show_countdown(
            cv2,
            capture,
            participant_id,
            label,
            repetition,
            frames,
            width,
            height,
        )
        if not countdown_completed:
            cancelled = True
            return None

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path.as_posix(), fourcc, fps, (width, height))
        if not writer.isOpened():
            raise RuntimeError(f"Could not create video writer for {output_path.as_posix()}.")

        while recorded_frames < frames:
            success, frame = capture.read()
            if not success:
                raise RuntimeError("Could not read frames from the webcam.")

            frame = cv2.resize(frame, (width, height))
            recorded_frames += 1
            frame = draw_overlay(
                cv2,
                frame,
                participant_id,
                label,
                repetition,
                recorded_frames,
                frames,
                "Recording",
            )

            writer.write(frame)
            cv2.imshow(WINDOW_TITLE, frame)

            wait_time_ms = max(1, int(1000 / fps))
            if is_cancel_key(cv2.waitKey(wait_time_ms)):
                cancelled = True
                break

        if cancelled:
            return None

        return recorded_frames

    finally:
        capture.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()

        if cancelled and output_path.exists():
            output_path.unlink()


def main() -> int:
    """Run one safe Sprint 2.2 raw video collection workflow."""
    args = parse_args()

    try:
        participant_id = validate_participant_id(args.participant)
        label = validate_label(args.label)
        repetition = validate_positive_integer(args.repetition, "repetition")
        frames = validate_positive_integer(args.frames, "frames")
        fps = validate_positive_integer(args.fps, "fps")
        width = validate_positive_integer(args.width, "width")
        height = validate_positive_integer(args.height, "height")

        ensure_metadata_file()

        sample_id = build_sample_id(participant_id, label, repetition)
        output_path = RAW_VIDEO_DIR / label / f"{sample_id}.mp4"

        recorded_frames = record_video(
            participant_id=participant_id,
            label=label,
            repetition=repetition,
            output_path=output_path,
            camera_index=args.camera_index,
            frames=frames,
            fps=fps,
            width=width,
            height=height,
            overwrite=args.overwrite,
        )

        if recorded_frames is None:
            print("Recording cancelled. No metadata saved.")
            return 1

        recording_details = (
            f"frames={recorded_frames}; fps={fps}; width={width}; height={height}"
        )
        metadata_notes = (
            f"{args.notes}; {recording_details}" if args.notes else recording_details
        )
        append_metadata(
            sample_id=sample_id,
            participant_id=participant_id,
            label=label,
            repetition=repetition,
            video_path=output_path,
            notes=metadata_notes,
        )

        print()
        print("Sprint 2.2 Recording Summary")
        print("-----------------------------")
        print(f"sample_id: {sample_id}")
        print(f"saved video path: {output_path.as_posix()}")
        print(f"frame count: {recorded_frames}")
        print(f"metadata path: {METADATA_PATH.as_posix()}")
        print("Sprint 2.2 recording completed successfully.")
        return 0

    except (FileExistsError, ImportError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

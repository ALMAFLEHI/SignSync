"""Preview MediaPipe hand landmarks on a selected raw trial video."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

from trial_config import DEFAULT_PARTICIPANT_ID


RAW_VIDEO_DIR = Path("ml") / "data_raw" / "videos"
EVIDENCE_DIR = Path("docs") / "phase_2_evidence"
DEFAULT_HAND_MODEL_PATH = Path("ml") / "models" / "hand_landmarker.task"
WINDOW_TITLE = "SignSync Landmark Preview"


def parse_args() -> argparse.Namespace:
    """Parse preview options."""
    parser = argparse.ArgumentParser(
        description="Preview MediaPipe hand landmarks on one raw video."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT_ID)
    parser.add_argument("--label", required=True)
    parser.add_argument("--repetition", required=True, type=int)
    parser.add_argument("--save-preview", action="store_true")
    parser.add_argument("--model-path", default=DEFAULT_HAND_MODEL_PATH.as_posix())
    return parser.parse_args()


def import_preview_runtime() -> tuple[Any, Any]:
    """Import preview dependencies with a clear install hint."""
    try:
        cv2 = importlib.import_module("cv2")
        mediapipe = importlib.import_module("mediapipe")
    except ImportError as exc:
        raise ImportError(
            "OpenCV and MediaPipe are required. Install with: "
            "python -m pip install -r requirements_sprint_2_4.txt"
        ) from exc
    return cv2, mediapipe


def create_hand_detector(mediapipe: Any, model_path: Path) -> tuple[str, Any, Any]:
    """Create a hand detector using legacy solutions or Tasks HandLandmarker."""
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
    rgb_frame: Any,
    frame_index: int,
    fps: float,
) -> list[dict[str, object]]:
    """Return all detected hands with landmarks and handedness labels."""
    if api_name == "legacy_solutions":
        results = detector.process(rgb_frame)
        if not results.multi_hand_landmarks:
            return []
        handedness_groups = results.multi_handedness or []
        detections: list[dict[str, object]] = []
        for index, hand in enumerate(results.multi_hand_landmarks[:2]):
            detections.append(
                {
                    "landmarks": list(hand.landmark),
                    "handedness": handedness_from_group(
                        handedness_groups[index].classification
                        if index < len(handedness_groups)
                        else []
                    ),
                }
            )
        return detections

    timestamp_ms = int((frame_index * 1000) / max(fps, 1.0))
    mp_image = mediapipe.Image(
        image_format=mediapipe.ImageFormat.SRGB,
        data=rgb_frame,
    )
    results = detector.detect_for_video(mp_image, timestamp_ms)
    detections = []
    handedness_groups = results.handedness or []
    for index, hand in enumerate(results.hand_landmarks[:2]):
        detections.append(
            {
                "landmarks": list(hand),
                "handedness": handedness_from_group(
                    handedness_groups[index] if index < len(handedness_groups) else []
                ),
            }
        )
    return detections


def handedness_from_group(categories: Any) -> str:
    """Return left/right when MediaPipe provides a handedness category."""
    if not categories:
        return ""
    category = categories[0]
    label = (
        getattr(category, "category_name", "")
        or getattr(category, "label", "")
        or ""
    )
    normalized = str(label).strip().lower()
    if normalized.startswith("left"):
        return "left"
    if normalized.startswith("right"):
        return "right"
    return ""


def hand_connections(api_name: str, api_module: Any) -> list[Any]:
    """Return hand landmark connections for drawing preview lines."""
    if api_name == "legacy_solutions":
        return list(api_module.HAND_CONNECTIONS)
    return list(api_module.HandLandmarksConnections.HAND_CONNECTIONS)


def draw_hand_landmarks(
    cv2: Any,
    frame: Any,
    landmarks: list[Any],
    connections: list[Any],
    handedness: str,
) -> None:
    """Draw MediaPipe landmarks with OpenCV for both legacy and Tasks APIs."""
    height, width = frame.shape[:2]
    points: list[tuple[int, int]] = [
        (int(landmark.x * width), int(landmark.y * height)) for landmark in landmarks
    ]

    for connection in connections:
        start_index = connection.start
        end_index = connection.end
        if start_index < len(points) and end_index < len(points):
            cv2.line(frame, points[start_index], points[end_index], (0, 255, 0), 2)

    for point in points:
        cv2.circle(frame, point, 4, (0, 0, 255), -1)

    if points:
        label = handedness.title() if handedness else "Hand"
        cv2.putText(
            frame,
            label,
            (points[0][0], max(points[0][1] - 12, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def safe_fps(raw_fps: float) -> float:
    """Use a stable fallback FPS when OpenCV reports an invalid value."""
    return raw_fps if raw_fps and raw_fps > 0 else 20.0


def build_sample_id(participant_id: str, label: str, repetition: int) -> str:
    """Build the selected sample ID."""
    return f"{participant_id}_{label}_R{repetition:02d}"


def video_path_for_sample(participant_id: str, label: str, repetition: int) -> Path:
    """Return the raw video path for the selected sample."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return RAW_VIDEO_DIR / label / f"{sample_id}.mp4"


def preview_output_path(participant_id: str, label: str, repetition: int) -> Path:
    """Return the optional evidence preview output path."""
    sample_id = build_sample_id(participant_id, label, repetition)
    return EVIDENCE_DIR / f"{sample_id}_landmark_preview.mp4"


def main() -> int:
    """Display landmarks on a preview window without changing raw videos."""
    args = parse_args()

    try:
        cv2, mediapipe = import_preview_runtime()
        api_name, detector, api_module = create_hand_detector(
            mediapipe,
            Path(args.model_path),
        )
        connections = hand_connections(api_name, api_module)
    except (FileNotFoundError, ImportError) as exc:
        print(f"Error: {exc}")
        return 1

    video_path = video_path_for_sample(args.participant, args.label, args.repetition)
    if not video_path.exists():
        print(f"Error: video not found: {video_path.as_posix()}")
        return 1

    capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        print(f"Error: could not open video: {video_path.as_posix()}")
        return 1

    fps = safe_fps(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = None
    if args.save_preview:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        output_path = preview_output_path(args.participant, args.label, args.repetition)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path.as_posix(), fourcc, fps, (width, height))

    frame_index = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detected_hands = detect_hand_landmarks(
                api_name,
                detector,
                mediapipe,
                rgb_frame,
                frame_index,
                fps,
            )
            frame_index += 1
            preview_frame = frame.copy()

            for detection in detected_hands:
                draw_hand_landmarks(
                    cv2,
                    preview_frame,
                    detection["landmarks"],
                    connections,
                    str(detection.get("handedness", "")),
                )

            cv2.imshow(WINDOW_TITLE, preview_frame)
            if writer is not None:
                writer.write(preview_frame)

            if (cv2.waitKey(1) & 0xFF) in (ord("q"), ord("Q")):
                break
    finally:
        detector.close()

    capture.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

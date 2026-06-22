"""Preview an existing Sprint 2.9 landmark and hand-mask output over its raw video."""

from __future__ import annotations

import argparse
from pathlib import Path

from full_landmark_extraction_config import (
    FULL_DATASET_PARTICIPANT,
    HAND_MASK_DIMENSION,
    LANDMARKS_PER_HAND,
    LANDMARK_OUTPUT_DIMENSION,
    expected_paths,
)


WINDOW_TITLE = "SignSync Full Landmark Preview"
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


def parse_args() -> argparse.Namespace:
    """Parse one processed sample to inspect."""
    parser = argparse.ArgumentParser(
        description="Preview existing Sprint 2.9 landmark outputs over a raw video."
    )
    parser.add_argument("--participant", default=FULL_DATASET_PARTICIPANT)
    parser.add_argument("--label", required=True)
    parser.add_argument("--repetition", required=True, type=int)
    return parser.parse_args()


def print_summary(video_path: Path, landmark_path: Path, mask_path: Path, landmarks, mask) -> None:
    """Print required inspection details before opening a preview window."""
    left_frames = int(mask[:, 0].sum())
    right_frames = int(mask[:, 1].sum())
    any_hand_frames = int(((mask[:, 0] > 0) | (mask[:, 1] > 0)).sum())
    frame_count = len(mask)
    print("Sprint 2.9 Full Landmark Preview Summary")
    print("----------------------------------------")
    print(f"raw video path: {video_path.as_posix()}")
    print(f"landmark path: {landmark_path.as_posix()}")
    print(f"mask path: {mask_path.as_posix()}")
    print(f"landmark shape: {tuple(landmarks.shape)}")
    print(f"mask shape: {tuple(mask.shape)}")
    print(f"left hand coverage: {left_frames}/{frame_count}")
    print(f"right hand coverage: {right_frames}/{frame_count}")
    print(f"any hand coverage: {any_hand_frames}/{frame_count}")


def draw_hand(cv2, frame, values, color) -> None:
    """Draw one normalized 21-point hand stored in the fixed 126-value layout."""
    height, width = frame.shape[:2]
    points = [
        (int(values[index * 3] * width), int(values[index * 3 + 1] * height))
        for index in range(LANDMARKS_PER_HAND)
    ]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], color, 2)
    for point in points:
        cv2.circle(frame, point, 3, color, -1)


def main() -> int:
    """Load and display existing landmark outputs without modifying any artifact."""
    args = parse_args()
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        print(f"Error: preview requires OpenCV and numpy: {exc}")
        return 1

    try:
        paths = expected_paths(args.participant, args.label, args.repetition)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    video_path = paths["video"]
    landmark_path = paths["landmarks"]
    mask_path = paths["mask"]
    for path, description in [
        (video_path, "raw video"),
        (landmark_path, "landmark output"),
        (mask_path, "mask output"),
    ]:
        if not path.exists():
            print(f"Error: {description} not found: {path.as_posix()}")
            return 1

    landmarks = np.load(landmark_path, allow_pickle=False)
    mask = np.load(mask_path, allow_pickle=False)
    if landmarks.ndim != 2 or landmarks.shape[1] != LANDMARK_OUTPUT_DIMENSION:
        print(f"Error: invalid landmark shape: {tuple(landmarks.shape)}")
        return 1
    if mask.ndim != 2 or mask.shape[1] != HAND_MASK_DIMENSION or len(mask) != len(landmarks):
        print(f"Error: invalid mask shape: {tuple(mask.shape)}")
        return 1

    print_summary(video_path, landmark_path, mask_path, landmarks, mask)
    capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        print(f"Error: could not open raw video: {video_path.as_posix()}")
        return 1

    frame_index = 0
    try:
        while frame_index < len(landmarks):
            success, frame = capture.read()
            if not success:
                break
            preview_frame = frame.copy()
            if mask[frame_index, 0]:
                draw_hand(cv2, preview_frame, landmarks[frame_index, :63], (0, 255, 0))
            if mask[frame_index, 1]:
                draw_hand(cv2, preview_frame, landmarks[frame_index, 63:], (0, 165, 255))
            cv2.imshow(WINDOW_TITLE, preview_frame)
            frame_index += 1
            if (cv2.waitKey(1) & 0xFF) in (ord("q"), ord("Q")):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

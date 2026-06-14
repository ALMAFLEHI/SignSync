"""Check Sprint 2.4 MediaPipe landmark extraction dependencies."""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
from pathlib import Path


REQUIRED_PACKAGES = [
    ("cv2", "opencv-python"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("mediapipe", "mediapipe"),
]

DEFAULT_HAND_MODEL_PATH = Path("ml") / "models" / "hand_landmarker.task"


def get_version(module: object, package_name: str) -> str:
    """Return the best available version string for an imported package."""
    module_version = getattr(module, "__version__", None)
    if module_version:
        return str(module_version)

    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "version unknown"


def check_package(import_name: str, package_name: str) -> bool:
    """Import one package and print a clear installed/missing result."""
    try:
        module = importlib.import_module(import_name)
    except ImportError:
        print(f"FAIL: {package_name} is not installed.")
        return False

    print(f"PASS: {package_name} installed ({get_version(module, package_name)})")
    return True


def check_mediapipe_hands_api() -> bool:
    """Verify that the installed MediaPipe package can create a hand detector."""
    try:
        mediapipe = importlib.import_module("mediapipe")
    except ImportError:
        print("FAIL: MediaPipe Hands API could not be checked because mediapipe is missing.")
        return False

    if hasattr(mediapipe, "solutions"):
        try:
            hands_solution = mediapipe.solutions.hands
            detector = hands_solution.Hands(
                static_image_mode=False,
                max_num_hands=2,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            detector.close()
        except Exception as exc:  # noqa: BLE001 - print clean setup result.
            print(f"FAIL: MediaPipe legacy Hands API failed: {exc}")
            return False

        print("PASS: MediaPipe Hands API available through mp.solutions.hands")
        return True

    try:
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python import vision
    except ImportError as exc:
        print(f"FAIL: MediaPipe Tasks HandLandmarker API is unavailable: {exc}")
        return False

    if not DEFAULT_HAND_MODEL_PATH.exists():
        print(
            "FAIL: MediaPipe Tasks HandLandmarker model is missing. "
            f"Expected: {DEFAULT_HAND_MODEL_PATH.as_posix()}"
        )
        return False

    try:
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=DEFAULT_HAND_MODEL_PATH.as_posix()
            ),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        detector = vision.HandLandmarker.create_from_options(options)
        detector.close()
    except Exception as exc:  # noqa: BLE001 - print clean setup result.
        print(f"FAIL: MediaPipe Tasks HandLandmarker API failed: {exc}")
        return False

    print("PASS: MediaPipe Hands API available through Tasks HandLandmarker")
    return True


def main() -> int:
    """Run dependency checks without webcam access or video processing."""
    print("Sprint 2.4 MediaPipe Setup Check")
    print("---------------------------------")
    print(f"Python: {sys.version.split()[0]}")

    results = [
        check_package(import_name, package_name)
        for import_name, package_name in REQUIRED_PACKAGES
    ]
    hands_api_result = check_mediapipe_hands_api()

    print()
    if all(results) and hands_api_result:
        print("Setup summary: PASS")
        return 0

    print("Setup summary: FAIL")
    print("Install missing Sprint 2.4 packages with:")
    print("python -m pip install -r requirements_sprint_2_4.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

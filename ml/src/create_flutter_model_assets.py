"""Prepare Sprint 2.13 model assets for later Flutter integration."""

from __future__ import annotations

import json
import shutil

from tflite_model_config import (
    DATASET_VERSION,
    FEATURE_ORDER,
    FLUTTER_ASSETS_DIR,
    FLUTTER_ASSETS_REPORT_MD_PATH,
    INPUT_FEATURE_WIDTH,
    LANDMARK_DIMENSION,
    MODEL_LABEL_GROUPS_PATH,
    MODEL_LABEL_NAMES_PATH,
    OUTPUT_CLASSES,
    SOURCE_LABEL_MAPPING_PATH,
    TARGET_FRAMES,
    TFLITE_DYNAMIC_RANGE_PATH,
    TFLITE_FLOAT32_PATH,
)


def require_file(path) -> None:
    """Raise a clear error if a required model artifact is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required artifact: {path.as_posix()}")


def copy_if_exists(source, destination_name: str) -> str:
    """Copy an artifact to the Flutter asset staging folder when present."""
    if not source.exists():
        return "missing"
    destination = FLUTTER_ASSETS_DIR / destination_name
    shutil.copy2(source, destination)
    return destination.as_posix()


def main() -> int:
    """Create model asset files only; do not create Flutter app code."""
    try:
        require_file(TFLITE_FLOAT32_PATH)
        require_file(MODEL_LABEL_NAMES_PATH)
        require_file(MODEL_LABEL_GROUPS_PATH)
        require_file(SOURCE_LABEL_MAPPING_PATH)
        labels = json.loads(MODEL_LABEL_NAMES_PATH.read_text(encoding="utf-8"))
        groups = json.loads(MODEL_LABEL_GROUPS_PATH.read_text(encoding="utf-8"))
        mapping = json.loads(SOURCE_LABEL_MAPPING_PATH.read_text(encoding="utf-8"))

        FLUTTER_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        float_asset = copy_if_exists(TFLITE_FLOAT32_PATH, "model_float32.tflite")
        dynamic_asset = copy_if_exists(TFLITE_DYNAMIC_RANGE_PATH, "model_dynamic_range.tflite")
        (FLUTTER_ASSETS_DIR / "labels.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
        (FLUTTER_ASSETS_DIR / "label_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        (FLUTTER_ASSETS_DIR / "label_groups.json").write_text(json.dumps(groups, indent=2), encoding="utf-8")

        metadata = {
            "model_version": DATASET_VERSION,
            "input_type": "statistical_features",
            "input_shape": [1, INPUT_FEATURE_WIDTH],
            "source_sequence_shape": [TARGET_FRAMES, LANDMARK_DIMENSION],
            "landmark_dimension": LANDMARK_DIMENSION,
            "target_frames": TARGET_FRAMES,
            "feature_order": FEATURE_ORDER,
            "output_shape": [1, OUTPUT_CLASSES],
            "total_labels": OUTPUT_CLASSES,
            "normal_mode_labels": len(groups.get("normal_mode", [])),
            "number_mode_labels": len(groups.get("number_mode", [])),
            "label_order_matches_output_indices": True,
            "flutter_note": (
                "Collect 60 frames of MediaPipe landmarks, compute mean/std/min/max/"
                "first_frame/last_frame features, run TFLite inference, and map output "
                "index to labels.txt."
            ),
        }
        (FLUTTER_ASSETS_DIR / "tflite_model_metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

        content = f"""# Sprint 2.13 Flutter Model Assets Report

## Asset Folder
{FLUTTER_ASSETS_DIR.as_posix()}

## Files
- Float32 model: {float_asset}
- Dynamic range model: {dynamic_asset}
- labels.txt
- label_mapping.json
- label_groups.json
- tflite_model_metadata.json

## Scope Boundary
This script creates model asset files only. It does not create Flutter app code or UI files.
"""
        FLUTTER_ASSETS_REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLUTTER_ASSETS_REPORT_MD_PATH.write_text(content, encoding="utf-8")
        print("Sprint 2.13 Flutter Model Assets Summary")
        print("----------------------------------------")
        print(f"asset folder: {FLUTTER_ASSETS_DIR.as_posix()}")
        print(f"float32 model: {float_asset}")
        print(f"dynamic range model: {dynamic_asset}")
        print(f"report: {FLUTTER_ASSETS_REPORT_MD_PATH.as_posix()}")
        return 0
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Export the locked Sprint 2.17 Keras winner to isolated TFLite candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sprint_2_17_account_corrected_v2_config import (
    DYNAMIC_MODEL_NAME,
    FINAL_LABELS,
    FLOAT32_MODEL_NAME,
    KERAS_MODEL_NAME,
    METADATA_DIR,
    METRICS_DIR,
    MODEL_DIR,
    OUTPUT_CLASSES,
    ROOT,
)
from sprint_2_17_utils import relative_path, sha256_file, utc_now, write_json


KERAS_MODEL = MODEL_DIR / KERAS_MODEL_NAME
FLOAT32_MODEL = MODEL_DIR / FLOAT32_MODEL_NAME
DYNAMIC_MODEL = MODEL_DIR / DYNAMIC_MODEL_NAME


def main() -> int:
    """Convert only the evaluated and hash-locked Keras candidate."""
    winner_lock = json.loads(
        (METADATA_DIR / "winner_lock.json").read_text(encoding="utf-8")
    )
    if winner_lock.get("status") != "winner_locked_test_evaluated":
        raise ValueError("The winner must complete its one-time test evaluation first.")
    if winner_lock.get("test_evaluation_status") != "completed_once":
        raise ValueError("The final test evaluation is not recorded as completed once.")
    if not (METRICS_DIR / "final_test_metrics.json").exists():
        raise FileNotFoundError("Final locked test metrics are missing.")
    if sha256_file(KERAS_MODEL) != winner_lock["locked_keras_sha256"]:
        raise ValueError("The locked Keras winner hash changed before export.")
    for path in (FLOAT32_MODEL, DYNAMIC_MODEL):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite candidate: {relative_path(path)}")
        if "flutter_app" in path.parts:
            raise ValueError("Sprint 2.17 exports must never target Flutter assets.")

    import tensorflow as tf

    model = tf.keras.models.load_model(KERAS_MODEL)
    _validate_keras_contract(model)

    float_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    FLOAT32_MODEL.write_bytes(float_converter.convert())

    dynamic_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    dynamic_converter.optimizations = [tf.lite.Optimize.DEFAULT]
    DYNAMIC_MODEL.write_bytes(dynamic_converter.convert())

    export = {
        "created_at": utc_now(),
        "source_keras_model": relative_path(KERAS_MODEL),
        "source_keras_sha256": sha256_file(KERAS_MODEL),
        "float32_tflite": relative_path(FLOAT32_MODEL),
        "float32_tflite_sha256": sha256_file(FLOAT32_MODEL),
        "dynamic_range_tflite": relative_path(DYNAMIC_MODEL),
        "dynamic_range_tflite_sha256": sha256_file(DYNAMIC_MODEL),
        "input_shape": [1, 756],
        "output_shape": [1, OUTPUT_CLASSES],
        "label_count": len(FINAL_LABELS),
        "deployment_status": "candidate_not_deployed",
        "flutter_assets_modified": False,
    }
    write_json(METADATA_DIR / "tflite_export.json", export)

    print("Sprint 2.17 TensorFlow Lite Export")
    print("----------------------------------")
    print(f"Keras: {relative_path(KERAS_MODEL)}")
    print(f"Float32 TFLite: {relative_path(FLOAT32_MODEL)}")
    print(f"Dynamic-range TFLite: {relative_path(DYNAMIC_MODEL)}")
    print("Input/output contract: [1, 756] -> [1, 40]")
    print("Deployment status: candidate_not_deployed")
    print("PASS: isolated Sprint 2.17 TFLite candidates exported.")
    return 0


def _validate_keras_contract(model: Any) -> None:
    if model.input_shape != (None, 756):
        raise ValueError(f"Unexpected locked Keras input shape: {model.input_shape}")
    if model.output_shape != (None, OUTPUT_CLASSES):
        raise ValueError(f"Unexpected locked Keras output shape: {model.output_shape}")
    output_layer = model.layers[-1]
    activation_name = getattr(output_layer.activation, "__name__", "")
    if activation_name != "softmax":
        raise ValueError("The locked Keras output must use softmax probabilities.")


if __name__ == "__main__":
    raise SystemExit(main())

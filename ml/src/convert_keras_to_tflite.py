"""Convert the Sprint 2.13 Keras model to TensorFlow Lite formats."""

from __future__ import annotations

from tflite_model_config import (
    KERAS_MODEL_PATH,
    TFLITE_CONVERSION_REPORT_MD_PATH,
    TFLITE_DYNAMIC_RANGE_PATH,
    TFLITE_FLOAT32_PATH,
)


def import_tensorflow():
    """Import TensorFlow only when conversion runs."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001
        raise ImportError("TensorFlow is not available in this environment.") from exc
    return tf


def file_size_text(path) -> str:
    """Return a compact file-size string for reports."""
    return f"{path.stat().st_size} bytes" if path.exists() else "missing"


def main() -> int:
    """Export float32 and dynamic-range TFLite models."""
    try:
        tf = import_tensorflow()
        if not KERAS_MODEL_PATH.exists():
            raise FileNotFoundError(f"Keras model is missing: {KERAS_MODEL_PATH.as_posix()}")
        model = tf.keras.models.load_model(KERAS_MODEL_PATH)

        TFLITE_FLOAT32_PATH.parent.mkdir(parents=True, exist_ok=True)
        float_converter = tf.lite.TFLiteConverter.from_keras_model(model)
        float_tflite = float_converter.convert()
        TFLITE_FLOAT32_PATH.write_bytes(float_tflite)

        quantization_issue = ""
        try:
            quant_converter = tf.lite.TFLiteConverter.from_keras_model(model)
            quant_converter.optimizations = [tf.lite.Optimize.DEFAULT]
            quant_tflite = quant_converter.convert()
            TFLITE_DYNAMIC_RANGE_PATH.write_bytes(quant_tflite)
        except Exception as exc:  # noqa: BLE001 - float32 export can still be valid.
            quantization_issue = str(exc)

        content = f"""# Sprint 2.13 TFLite Conversion Report

## Outputs
- Float32 TFLite: {TFLITE_FLOAT32_PATH.as_posix()} ({file_size_text(TFLITE_FLOAT32_PATH)})
- Dynamic range TFLite: {TFLITE_DYNAMIC_RANGE_PATH.as_posix()} ({file_size_text(TFLITE_DYNAMIC_RANGE_PATH)})

## Quantization Issue
{quantization_issue if quantization_issue else '- None'}

## Model Contract
- Input shape: `[1, 756]`
- Input dtype: `float32`
- Output shape: `[1, 86]`
- Output dtype: `float32`
"""
        TFLITE_CONVERSION_REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        TFLITE_CONVERSION_REPORT_MD_PATH.write_text(content, encoding="utf-8")
        print("Sprint 2.13 TFLite Conversion Summary")
        print("-------------------------------------")
        print(f"float32 TFLite: {TFLITE_FLOAT32_PATH.as_posix()} ({file_size_text(TFLITE_FLOAT32_PATH)})")
        print(f"dynamic range TFLite: {TFLITE_DYNAMIC_RANGE_PATH.as_posix()} ({file_size_text(TFLITE_DYNAMIC_RANGE_PATH)})")
        print(f"report: {TFLITE_CONVERSION_REPORT_MD_PATH.as_posix()}")
        return 0
    except (ImportError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

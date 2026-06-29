"""Predict one prepared expanded V2 sample using an exported Sprint 2.13 TFLite model."""

from __future__ import annotations

import argparse

import numpy as np

from tflite_model_config import FEATURE_DATASET_PATH, TFLITE_FLOAT32_PATH


def parse_args() -> argparse.Namespace:
    """Parse sample selection and optional TFLite model path."""
    parser = argparse.ArgumentParser(description="Predict one sample with the Sprint 2.13 TFLite model.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--sample-id")
    selection.add_argument("--label")
    parser.add_argument("--repetition", type=int)
    parser.add_argument("--participant", default="P02")
    parser.add_argument("--model-path", default=TFLITE_FLOAT32_PATH.as_posix())
    return parser.parse_args()


def import_tensorflow():
    """Import TensorFlow only when prediction runs."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001
        raise ImportError("TensorFlow is not available in this environment.") from exc
    return tf


def selected_sample_id(args: argparse.Namespace) -> str:
    """Return a direct sample ID or construct one from label/repetition."""
    if args.sample_id:
        return args.sample_id
    if args.repetition is None or args.repetition < 1:
        raise ValueError("--repetition must be supplied with --label.")
    return f"{args.participant}_{args.label}_R{args.repetition:02d}"


def main() -> int:
    """Load feature dataset and TFLite model, then predict one sample."""
    try:
        tf = import_tensorflow()
        args = parse_args()
        sample_id = selected_sample_id(args)
        model_path = args.model_path
        if not FEATURE_DATASET_PATH.exists():
            raise FileNotFoundError(f"Feature dataset is missing: {FEATURE_DATASET_PATH.as_posix()}")
        with np.load(FEATURE_DATASET_PATH, allow_pickle=False) as dataset:
            sample_ids = dataset["sample_ids"].astype(str)
            labels = dataset["labels"].astype(str)
            y = dataset["y"]
            label_names = dataset["label_names"].astype(str)
            X_features = dataset["X_features"].astype(np.float32)
        matches = np.where(sample_ids == sample_id)[0]
        if len(matches) != 1:
            raise ValueError(f"Expected one matching sample ID, found {len(matches)}: {sample_id}")
        index = int(matches[0])

        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        input_detail = interpreter.get_input_details()[0]
        output_detail = interpreter.get_output_details()[0]
        interpreter.set_tensor(input_detail["index"], X_features[index:index + 1])
        interpreter.invoke()
        probabilities = interpreter.get_tensor(output_detail["index"])[0]
        predicted_index = int(np.argmax(probabilities))
        true_index = int(y[index])

        print("Sprint 2.13 TFLite Sample Prediction")
        print("------------------------------------")
        print(f"sample ID: {sample_id}")
        print(f"true label: {labels[index]}")
        print(f"predicted label: {label_names[predicted_index]}")
        print(f"result: {'correct' if predicted_index == true_index else 'incorrect'}")
        print(f"confidence: {float(probabilities[predicted_index]):.4f}")
        print("top 5 predictions:")
        for probability_index in np.argsort(probabilities)[::-1][:5]:
            label_index = int(probability_index)
            print(f"- {label_names[label_index]}: {float(probabilities[label_index]):.4f}")
        return 0
    except (ImportError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

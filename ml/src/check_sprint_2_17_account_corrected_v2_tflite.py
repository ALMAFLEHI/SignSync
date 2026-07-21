"""Verify Sprint 2.17 TFLite contracts, parity, size, and desktop latency."""

from __future__ import annotations

import json
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_17_account_corrected_v2_config import (
    DYNAMIC_MODEL_NAME,
    FINAL_LABELS,
    FLOAT32_MODEL_NAME,
    KERAS_MODEL_NAME,
    METADATA_DIR,
    METRICS_DIR,
    MODEL_DIR,
    OUTPUT_CLASSES,
    PHONE_TEST_FEATURES,
    REPORTS_DIR,
)
from sprint_2_17_utils import relative_path, sha256_file, utc_now, write_csv, write_json


KERAS_MODEL = MODEL_DIR / KERAS_MODEL_NAME
FLOAT32_MODEL = MODEL_DIR / FLOAT32_MODEL_NAME
DYNAMIC_MODEL = MODEL_DIR / DYNAMIC_MODEL_NAME
PARITY_SAMPLE_COUNT = 40
WARMUP_RUNS = 10
MEASURED_RUNS = 100


def main() -> int:
    """Run contract and parity checks without changing the locked model."""
    _validate_preconditions()
    import tensorflow as tf

    with np.load(PHONE_TEST_FEATURES, allow_pickle=False) as archive:
        test = {key: archive[key] for key in archive.files}
    final_predictions = json.loads(
        (METRICS_DIR / "final_test_predictions.json").read_text(encoding="utf-8")
    )
    parity_indices = _select_parity_indices(final_predictions)
    X = test["X"][parity_indices].astype(np.float32)
    y = test["y"][parity_indices].astype(np.int64)
    sample_ids = test["sample_ids"][parity_indices].astype(str)

    keras_model = tf.keras.models.load_model(KERAS_MODEL)
    if keras_model.input_shape != (None, 756) or keras_model.output_shape != (
        None,
        OUTPUT_CLASSES,
    ):
        raise ValueError("The locked Keras contract is not 756 -> 40.")
    keras_probabilities = np.asarray(keras_model.predict(X, verbose=0), dtype=np.float32)

    float_probabilities, float_contract = _tflite_predict(tf, FLOAT32_MODEL, X)
    dynamic_probabilities, dynamic_contract = _tflite_predict(tf, DYNAMIC_MODEL, X)
    for name, probabilities in (
        ("Keras", keras_probabilities),
        ("float32 TFLite", float_probabilities),
        ("dynamic-range TFLite", dynamic_probabilities),
    ):
        _validate_probabilities(name, probabilities)

    keras_top1 = np.argmax(keras_probabilities, axis=1)
    float_top1 = np.argmax(float_probabilities, axis=1)
    dynamic_top1 = np.argmax(dynamic_probabilities, axis=1)
    float_agreement = float(np.mean(keras_top1 == float_top1))
    dynamic_agreement = float(np.mean(keras_top1 == dynamic_top1))
    if float_agreement != 1.0:
        raise ValueError(
            f"Float32 TFLite top-1 parity failed: {float_agreement:.4f}; candidate rejected."
        )

    rows = []
    for row_index, source_index in enumerate(parity_indices):
        float_difference = np.abs(
            keras_probabilities[row_index] - float_probabilities[row_index]
        )
        dynamic_difference = np.abs(
            keras_probabilities[row_index] - dynamic_probabilities[row_index]
        )
        rows.append(
            {
                "sample_id": sample_ids[row_index],
                "actual_label": FINAL_LABELS[int(y[row_index])],
                "source_test_index": int(source_index),
                "priority": (
                    "misclassified_or_low_confidence"
                    if not bool(final_predictions[source_index]["correct"])
                    or float(final_predictions[source_index]["confidence"]) < 0.90
                    else "one_per_class"
                ),
                "keras_top1": FINAL_LABELS[int(keras_top1[row_index])],
                "float32_top1": FINAL_LABELS[int(float_top1[row_index])],
                "dynamic_top1": FINAL_LABELS[int(dynamic_top1[row_index])],
                "float32_top1_agrees": bool(keras_top1[row_index] == float_top1[row_index]),
                "dynamic_top1_agrees": bool(
                    keras_top1[row_index] == dynamic_top1[row_index]
                ),
                "float32_max_abs_difference": float(np.max(float_difference)),
                "float32_mean_abs_difference": float(np.mean(float_difference)),
                "dynamic_max_abs_difference": float(np.max(dynamic_difference)),
                "dynamic_mean_abs_difference": float(np.mean(dynamic_difference)),
            }
        )
    write_csv(METRICS_DIR / "tflite_parity.csv", rows, list(rows[0]))

    latency = {
        "float32_tflite": _measure_latency(tf, FLOAT32_MODEL, X[0]),
        "dynamic_range_tflite": _measure_latency(tf, DYNAMIC_MODEL, X[0]),
    }
    result = {
        "created_at": utc_now(),
        "status": "PASS",
        "parity_samples": PARITY_SAMPLE_COUNT,
        "selection": (
            "one locked test sample per class; each class prioritizes a test error, "
            "then its lowest-confidence sample"
        ),
        "label_order": FINAL_LABELS,
        "keras_contract": {
            "input_shape": [1, 756],
            "output_shape": [1, 40],
            "input_dtype": "float32",
            "output_dtype": "float32",
        },
        "float32_contract": float_contract,
        "dynamic_range_contract": dynamic_contract,
        "keras_float32_top1_agreement": float_agreement,
        "keras_dynamic_top1_agreement": dynamic_agreement,
        "float32_global_max_abs_difference": float(
            np.max(np.abs(keras_probabilities - float_probabilities))
        ),
        "float32_global_mean_abs_difference": float(
            np.mean(np.abs(keras_probabilities - float_probabilities))
        ),
        "dynamic_global_max_abs_difference": float(
            np.max(np.abs(keras_probabilities - dynamic_probabilities))
        ),
        "dynamic_global_mean_abs_difference": float(
            np.mean(np.abs(keras_probabilities - dynamic_probabilities))
        ),
        "model_sizes_bytes": {
            "keras": KERAS_MODEL.stat().st_size,
            "float32_tflite": FLOAT32_MODEL.stat().st_size,
            "dynamic_range_tflite": DYNAMIC_MODEL.stat().st_size,
        },
        "model_sha256": {
            "keras": sha256_file(KERAS_MODEL),
            "float32_tflite": sha256_file(FLOAT32_MODEL),
            "dynamic_range_tflite": sha256_file(DYNAMIC_MODEL),
        },
        "desktop_latency": latency,
        "deployment_status": "candidate_not_deployed",
    }
    write_json(METADATA_DIR / "tflite_verification.json", result)
    _write_report(result)

    print("Sprint 2.17 TensorFlow Lite Verification")
    print("----------------------------------------")
    print("Float32 contract: [1, 756] float32 -> [1, 40] float32")
    print("Dynamic contract: [1, 756] float32 -> [1, 40] float32")
    print(f"Parity samples: {PARITY_SAMPLE_COUNT}")
    print(f"Keras/float32 top-1 agreement: {float_agreement:.4f}")
    print(f"Keras/dynamic top-1 agreement: {dynamic_agreement:.4f}")
    print(
        "Float32 desktop latency mean/median/P95 ms: "
        f"{latency['float32_tflite']['mean_ms']:.3f}/"
        f"{latency['float32_tflite']['median_ms']:.3f}/"
        f"{latency['float32_tflite']['p95_ms']:.3f}"
    )
    print(
        "Dynamic desktop latency mean/median/P95 ms: "
        f"{latency['dynamic_range_tflite']['mean_ms']:.3f}/"
        f"{latency['dynamic_range_tflite']['median_ms']:.3f}/"
        f"{latency['dynamic_range_tflite']['p95_ms']:.3f}"
    )
    print("PASS: TFLite contracts, probabilities, and parity verified.")
    return 0


def _validate_preconditions() -> None:
    winner_lock = json.loads(
        (METADATA_DIR / "winner_lock.json").read_text(encoding="utf-8")
    )
    if winner_lock.get("status") != "winner_locked_test_evaluated":
        raise ValueError("The locked winner has not completed final evaluation.")
    if not (METRICS_DIR / "final_test_metrics.json").exists():
        raise FileNotFoundError("Final metrics are required before parity testing.")
    if sha256_file(KERAS_MODEL) != winner_lock["locked_keras_sha256"]:
        raise ValueError("The locked Keras hash changed.")
    for model in (FLOAT32_MODEL, DYNAMIC_MODEL):
        if not model.is_file() or model.stat().st_size == 0:
            raise FileNotFoundError(f"Missing exported model: {relative_path(model)}")
    labels = json.loads((METADATA_DIR / "labels_40.json").read_text(encoding="utf-8"))
    if labels != FINAL_LABELS:
        raise ValueError("Candidate label metadata does not preserve frozen order.")


def _select_parity_indices(predictions: list[dict[str, Any]]) -> np.ndarray:
    if len(predictions) != 200:
        raise ValueError("Final prediction ledger must contain 200 locked test rows.")
    by_label: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(predictions):
        by_label[str(row["actual_label"])].append(index)
    selected = []
    for label in FINAL_LABELS:
        candidates = by_label[label]
        if len(candidates) != 5:
            raise ValueError(f"Expected five locked test rows for {label}.")
        selected.append(
            min(
                candidates,
                key=lambda index: (
                    bool(predictions[index]["correct"]),
                    float(predictions[index]["confidence"]),
                    str(predictions[index]["sample_id"]),
                ),
            )
        )
    return np.asarray(selected, dtype=np.int64)


def _tflite_predict(
    tf: Any, model_path: Path, X: np.ndarray
) -> tuple[np.ndarray, dict[str, Any]]:
    interpreter = tf.lite.Interpreter(model_path=model_path.as_posix())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    contract = {
        "model": relative_path(model_path),
        "loads_successfully": True,
        "input_shape": input_detail["shape"].astype(int).tolist(),
        "input_dtype": np.dtype(input_detail["dtype"]).name,
        "output_shape": output_detail["shape"].astype(int).tolist(),
        "output_dtype": np.dtype(output_detail["dtype"]).name,
    }
    if contract["input_shape"] != [1, 756] or contract["input_dtype"] != "float32":
        raise ValueError(f"Invalid input contract for {relative_path(model_path)}: {contract}")
    if contract["output_shape"] != [1, 40] or contract["output_dtype"] != "float32":
        raise ValueError(f"Invalid output contract for {relative_path(model_path)}: {contract}")
    outputs = []
    for feature in X:
        interpreter.set_tensor(
            input_detail["index"], feature.reshape(1, 756).astype(np.float32)
        )
        interpreter.invoke()
        outputs.append(interpreter.get_tensor(output_detail["index"])[0].copy())
    return np.asarray(outputs, dtype=np.float32), contract


def _validate_probabilities(name: str, probabilities: np.ndarray) -> None:
    if probabilities.shape != (PARITY_SAMPLE_COUNT, OUTPUT_CLASSES):
        raise ValueError(f"{name} probability shape changed: {probabilities.shape}")
    if not np.isfinite(probabilities).all():
        raise ValueError(f"{name} produced NaN or infinity.")
    if np.any(probabilities < -1e-6) or np.any(probabilities > 1.0 + 1e-6):
        raise ValueError(f"{name} outputs are outside the probability range.")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-4):
        raise ValueError(f"{name} outputs do not sum to one.")


def _measure_latency(tf: Any, model_path: Path, feature: np.ndarray) -> dict[str, Any]:
    interpreter = tf.lite.Interpreter(model_path=model_path.as_posix())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    value = feature.reshape(1, 756).astype(np.float32)
    for _ in range(WARMUP_RUNS):
        interpreter.set_tensor(input_detail["index"], value)
        interpreter.invoke()
    durations = []
    for _ in range(MEASURED_RUNS):
        interpreter.set_tensor(input_detail["index"], value)
        started = time.perf_counter_ns()
        interpreter.invoke()
        durations.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return {
        "scope": "development-machine TFLite interpreter latency; not Samsung A55 latency",
        "warmup_runs": WARMUP_RUNS,
        "measured_runs": MEASURED_RUNS,
        "mean_ms": float(statistics.fmean(durations)),
        "median_ms": float(statistics.median(durations)),
        "p95_ms": float(np.percentile(durations, 95)),
        "minimum_ms": float(min(durations)),
        "maximum_ms": float(max(durations)),
    }


def _write_report(result: dict[str, Any]) -> None:
    float_latency = result["desktop_latency"]["float32_tflite"]
    dynamic_latency = result["desktop_latency"]["dynamic_range_tflite"]
    sizes = result["model_sizes_bytes"]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "tflite_parity_report.md").write_text(
        f"""# Sprint 2.17 Keras-TFLite Parity and Runtime Report

## Contract

Both TFLite candidates load with a float32 `[1, 756]` input and float32 `[1, 40]` output. The output order is the frozen 40-intent metadata order; it contains no alphabet, digit, or removed-label classes.

## Parity

- Samples: {result['parity_samples']} (one locked test sample per class, prioritizing errors and low confidence)
- Keras to float32 TFLite top-1 agreement: {result['keras_float32_top1_agreement']:.4f}
- Keras to dynamic-range TFLite top-1 agreement: {result['keras_dynamic_top1_agreement']:.4f}
- Float32 maximum absolute probability difference: {result['float32_global_max_abs_difference']:.8f}
- Dynamic maximum absolute probability difference: {result['dynamic_global_max_abs_difference']:.8f}

The parity run verifies conversion consistency and does not alter the already closed aggregate test evaluation.

## Sizes

- Keras: {sizes['keras']} bytes
- Float32 TFLite: {sizes['float32_tflite']} bytes
- Dynamic-range TFLite: {sizes['dynamic_range_tflite']} bytes

## Development-Machine Latency

| Model | Warm-up | Runs | Mean ms | Median ms | P95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Float32 TFLite | {float_latency['warmup_runs']} | {float_latency['measured_runs']} | {float_latency['mean_ms']:.3f} | {float_latency['median_ms']:.3f} | {float_latency['p95_ms']:.3f} |
| Dynamic-range TFLite | {dynamic_latency['warmup_runs']} | {dynamic_latency['measured_runs']} | {dynamic_latency['mean_ms']:.3f} | {dynamic_latency['median_ms']:.3f} | {dynamic_latency['p95_ms']:.3f} |

These measurements are desktop development-machine interpreter latency, not Samsung Galaxy A55 mobile latency. The candidate remains `candidate_not_deployed`.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

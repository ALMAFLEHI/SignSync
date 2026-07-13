"""Validate the Sprint 2.16A Experiment B Flutter deployment end to end."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "ml" / "models" / "sprint_2_16A_v3_40" / "with_augmentation"
FLUTTER_ASSETS = ROOT / "flutter_app" / "assets"
BACKUP_DIR = (
    FLUTTER_ASSETS / "model_backups" / "pre_sprint_2_16A_experiment_B"
)
ACTIVE_SCOPE_PATH = ROOT / "ml" / "config" / "signsync_active_scope_v3_40.json"
PREDICTION_FIXTURE_PATH = (
    ROOT
    / "flutter_app"
    / "test"
    / "fixtures"
    / "experiment_b_tflite_predictions.json"
)
VALIDATION_PATH = (
    ROOT
    / "docs"
    / "phase_2_evidence"
    / "sprint_2_16A_flutter_deployment_validation.json"
)
PHONE_FIXTURES = {
    "P02_PHONE_transfer_R21": "transfer",
    "P02_PHONE_document_R21": "document",
    "P02_PHONE_signature_R21": "signature",
    "P02_PHONE_atm_R21": "atm",
}


def import_tensorflow() -> Any:
    """Import TensorFlow only when the deployment check runs."""
    try:
        import tensorflow as tf
    except Exception as exc:  # noqa: BLE001
        raise ImportError("TensorFlow is required for TFLite deployment validation.") from exc
    return tf


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Return a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def statistical_features(sequence: np.ndarray) -> np.ndarray:
    """Apply the unchanged Flutter-compatible 60x126 to 756 feature formula."""
    if sequence.shape != (60, 126):
        raise ValueError(f"Expected sequence shape (60, 126), found {sequence.shape}.")
    features = np.concatenate(
        [
            sequence.mean(axis=0),
            sequence.std(axis=0, ddof=0),
            sequence.min(axis=0),
            sequence.max(axis=0),
            sequence[0],
            sequence[-1],
        ]
    ).astype(np.float32)
    if features.shape != (756,) or not np.isfinite(features).all():
        raise ValueError("Feature computation did not produce 756 finite values.")
    return features


def inspect_interpreter(tf: Any, model_path: Path) -> tuple[Any, dict[str, Any]]:
    """Load one TFLite file and return its allocated interpreter contract."""
    interpreter = tf.lite.Interpreter(model_path=model_path.as_posix())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    return interpreter, {
        "path": model_path.relative_to(ROOT).as_posix(),
        "sha256": sha256(model_path),
        "file_size_bytes": model_path.stat().st_size,
        "input_shape": input_detail["shape"].astype(int).tolist(),
        "output_shape": output_detail["shape"].astype(int).tolist(),
        "input_dtype": np.dtype(input_detail["dtype"]).name,
        "output_dtype": np.dtype(output_detail["dtype"]).name,
    }


def predict(interpreter: Any, features: np.ndarray) -> np.ndarray:
    """Run one deterministic TFLite prediction."""
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    interpreter.set_tensor(input_detail["index"], features.reshape(1, 756))
    interpreter.invoke()
    return interpreter.get_tensor(output_detail["index"])[0].astype(np.float32)


def validate_backup_manifest() -> list[dict[str, Any]]:
    """Confirm every rollback file still matches its recorded hash and size."""
    manifest = read_json(BACKUP_DIR / "backup_manifest.json")
    rows = manifest["files"]
    if len(rows) != 6:
        raise ValueError("The rollback manifest must contain six original assets.")
    for row in rows:
        backup_path = ROOT / row["backup_path"]
        if not backup_path.is_file():
            raise FileNotFoundError(f"Backup asset is missing: {backup_path}")
        if backup_path.stat().st_size != row["file_size_bytes"]:
            raise ValueError(f"Backup size mismatch: {backup_path}")
        if sha256(backup_path) != row["sha256"]:
            raise ValueError(f"Backup hash mismatch: {backup_path}")
    return rows


def validate_metadata() -> dict[str, Any]:
    """Validate deployed labels, modes, mappings, and preprocessing order."""
    scope = read_json(ACTIVE_SCOPE_PATH)
    labels = [
        label.strip()
        for label in (FLUTTER_ASSETS / "metadata" / "labels.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if label.strip()
    ]
    mapping = read_json(FLUTTER_ASSETS / "metadata" / "label_mapping.json")
    groups = read_json(FLUTTER_ASSETS / "metadata" / "label_groups.json")
    model_metadata = read_json(
        FLUTTER_ASSETS / "metadata" / "tflite_model_metadata.json"
    )
    preprocessing = read_json(
        FLUTTER_ASSETS / "metadata" / "preprocessing_config.json"
    )
    expected_labels = [
        *groups["alphabet_mode"],
        *groups["number_mode"],
        *groups["banking_intent_mode"],
    ]
    if labels != expected_labels or labels != groups["all_labels"]:
        raise ValueError("Deployed label order does not match all three modes.")
    if mapping != {label: index for index, label in enumerate(labels)}:
        raise ValueError("Deployed mapping does not match label order.")
    if len(groups["alphabet_mode"]) != 26:
        raise ValueError("Alphabet Mode must contain 26 labels.")
    if len(groups["number_mode"]) != 10:
        raise ValueError("Number Mode must contain 10 labels.")
    if groups["banking_intent_mode"] != scope["active_banking_intents"]:
        raise ValueError("Banking Mode does not match the active 40-intent scope.")
    if set(scope["removed_banking_intents"]).intersection(labels):
        raise ValueError("A removed label appears in the deployed model.")
    if model_metadata["input_shape"] != [1, 756]:
        raise ValueError("Deployed metadata input shape is invalid.")
    if model_metadata["output_shape"] != [1, 76]:
        raise ValueError("Deployed metadata output shape is invalid.")
    if model_metadata["total_labels"] != 76:
        raise ValueError("Deployed metadata label count is invalid.")
    if preprocessing != read_json(SOURCE_DIR / "preprocessing_config.json"):
        raise ValueError("Deployed preprocessing config differs from Experiment B.")
    return {
        "labels": labels,
        "groups": groups,
        "model_metadata": model_metadata,
        "preprocessing": preprocessing,
    }


def main() -> int:
    """Run binary, metadata, parity, backup, and deterministic prediction checks."""
    tf = import_tensorflow()
    backup_rows = validate_backup_manifest()
    metadata = validate_metadata()
    labels = metadata["labels"]

    old_interpreter, old_contract = inspect_interpreter(
        tf, BACKUP_DIR / "models" / "model_dynamic_range.tflite"
    )
    del old_interpreter
    dynamic_interpreter, dynamic_contract = inspect_interpreter(
        tf, FLUTTER_ASSETS / "models" / "model_dynamic_range.tflite"
    )
    float_interpreter, float_contract = inspect_interpreter(
        tf, FLUTTER_ASSETS / "models" / "model_float32.tflite"
    )
    if old_contract["input_shape"] != [1, 756] or old_contract["output_shape"] != [1, 86]:
        raise ValueError("Backed-up model does not have the expected old contract.")
    for contract in (dynamic_contract, float_contract):
        if contract["input_shape"] != [1, 756] or contract["output_shape"] != [1, 76]:
            raise ValueError(f"Invalid deployed TFLite shape: {contract}")
        if contract["input_dtype"] != "float32" or contract["output_dtype"] != "float32":
            raise ValueError(f"Invalid deployed TFLite dtype: {contract}")

    source_hashes = {
        "dynamic_range": sha256(SOURCE_DIR / "model_dynamic_range.tflite"),
        "float32": sha256(SOURCE_DIR / "model_float32.tflite"),
    }
    if dynamic_contract["sha256"] != source_hashes["dynamic_range"]:
        raise ValueError("Deployed dynamic model differs from Experiment B source.")
    if float_contract["sha256"] != source_hashes["float32"]:
        raise ValueError("Deployed float model differs from Experiment B source.")

    parity_fixture = read_json(
        ROOT
        / "ml"
        / "data_phone"
        / "fixtures"
        / "P02_PHONE_transfer_R21_feature_parity.json"
    )
    parity_features = statistical_features(
        np.asarray(parity_fixture["frames"], dtype=np.float32)
    )
    expected_features = np.asarray(
        parity_fixture["expected_features_float32"], dtype=np.float32
    )
    max_feature_difference = float(np.max(np.abs(parity_features - expected_features)))
    if max_feature_difference > 1e-5:
        raise ValueError(f"Flutter feature parity failed: {max_feature_difference}")

    prediction_rows: list[dict[str, Any]] = []
    for sample_id, expected_label in PHONE_FIXTURES.items():
        sample = read_json(
            ROOT / "ml" / "data_phone" / "landmark_samples" / f"{sample_id}.json"
        )
        features = statistical_features(np.asarray(sample["frames"], dtype=np.float32))
        dynamic_probabilities = predict(dynamic_interpreter, features)
        float_probabilities = predict(float_interpreter, features)
        dynamic_index = int(np.argmax(dynamic_probabilities))
        float_index = int(np.argmax(float_probabilities))
        top_indices = np.argsort(dynamic_probabilities)[::-1][:2]
        predicted_label = labels[dynamic_index]
        if predicted_label != expected_label or float_index != dynamic_index:
            raise ValueError(
                f"Deterministic prediction failed for {sample_id}: "
                f"dynamic={predicted_label}, float={labels[float_index]}, "
                f"expected={expected_label}"
            )
        prediction_rows.append(
            {
                "sample_id": sample_id,
                "expected_label": expected_label,
                "dynamic_top1": predicted_label,
                "dynamic_top1_confidence": float(dynamic_probabilities[dynamic_index]),
                "dynamic_top2": labels[int(top_indices[1])],
                "dynamic_top2_confidence": float(dynamic_probabilities[int(top_indices[1])]),
                "float_top1": labels[float_index],
                "float_dynamic_max_abs_difference": float(
                    np.max(np.abs(float_probabilities - dynamic_probabilities))
                ),
            }
        )

    PREDICTION_FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREDICTION_FIXTURE_PATH.write_text(
        json.dumps(
            {
                "fixture_version": "sprint_2_16A_experiment_B_deployment_v1",
                "model_sha256": dynamic_contract["sha256"],
                "input_shape": [1, 756],
                "output_shape": [1, 76],
                "predictions": prediction_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = {
        "status": "PASS",
        "selected_primary_model": dynamic_contract,
        "deployed_fallback_model": float_contract,
        "old_primary_model": old_contract,
        "old_label_count": 86,
        "new_label_count": len(labels),
        "mode_counts": {
            "alphabet": len(metadata["groups"]["alphabet_mode"]),
            "number": len(metadata["groups"]["number_mode"]),
            "banking_intent": len(metadata["groups"]["banking_intent_mode"]),
        },
        "removed_labels_present": [],
        "backup_files_verified": len(backup_rows),
        "feature_parity_max_abs_difference": max_feature_difference,
        "deterministic_predictions": prediction_rows,
    }
    VALIDATION_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("PASS: Sprint 2.16A Flutter deployment validation passed.")
    print("Old tensor contract: float32 [1, 756] -> float32 [1, 86]")
    print("New tensor contract: float32 [1, 756] -> float32 [1, 76]")
    print("Labels: 76; modes: alphabet 26 / number 10 / banking 40")
    print(f"Feature parity max difference: {max_feature_difference:.9g}")
    print(f"Deterministic TFLite predictions passed: {len(prediction_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

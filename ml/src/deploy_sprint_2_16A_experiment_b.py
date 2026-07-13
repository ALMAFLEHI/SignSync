"""Safely deploy the reviewed Sprint 2.16A Experiment B assets to Flutter."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "ml" / "models" / "sprint_2_16A_v3_40" / "with_augmentation"
ACTIVE_SCOPE_PATH = ROOT / "ml" / "config" / "signsync_active_scope_v3_40.json"
FLUTTER_ASSETS = ROOT / "flutter_app" / "assets"
BACKUP_DIR = (
    FLUTTER_ASSETS
    / "model_backups"
    / "pre_sprint_2_16A_experiment_B"
)
STAGING_DIR = FLUTTER_ASSETS / ".sprint_2_16A_experiment_B_staging"

CURRENT_ASSET_PATHS = [
    Path("models/model_dynamic_range.tflite"),
    Path("models/model_float32.tflite"),
    Path("metadata/labels.txt"),
    Path("metadata/label_mapping.json"),
    Path("metadata/label_groups.json"),
    Path("metadata/tflite_model_metadata.json"),
]

SOURCE_ASSETS = {
    Path("models/model_dynamic_range.tflite"): SOURCE_DIR
    / "model_dynamic_range.tflite",
    Path("models/model_float32.tflite"): SOURCE_DIR / "model_float32.tflite",
    Path("metadata/labels.txt"): SOURCE_DIR / "labels.txt",
    Path("metadata/label_mapping.json"): SOURCE_DIR / "label_mapping.json",
    Path("metadata/label_groups.json"): SOURCE_DIR / "label_groups.json",
    Path("metadata/preprocessing_config.json"): SOURCE_DIR
    / "preprocessing_config.json",
}


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Return a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_source() -> dict[str, Any]:
    """Validate the reviewed source model and active metadata contract."""
    required = [
        *SOURCE_ASSETS.values(),
        SOURCE_DIR / "tflite_verification.json",
        SOURCE_DIR / "training_config.json",
        ACTIVE_SCOPE_PATH,
    ]
    missing = [path.as_posix() for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing deployment source files: {missing}")

    labels = [
        label.strip()
        for label in (SOURCE_DIR / "labels.txt").read_text(encoding="utf-8").splitlines()
        if label.strip()
    ]
    mapping = read_json(SOURCE_DIR / "label_mapping.json")
    groups = read_json(SOURCE_DIR / "label_groups.json")
    verification = read_json(SOURCE_DIR / "tflite_verification.json")
    preprocessing = read_json(SOURCE_DIR / "preprocessing_config.json")
    scope = read_json(ACTIVE_SCOPE_PATH)

    expected_labels = [
        *groups["alphabet_mode"],
        *groups["number_mode"],
        *groups["banking_intent_mode"],
    ]
    if labels != expected_labels or labels != groups["all_labels"]:
        raise ValueError("Experiment B label order does not match its mode groups.")
    if len(labels) != 76 or len(set(labels)) != 76:
        raise ValueError("Experiment B must contain exactly 76 unique labels.")
    if mapping != {label: index for index, label in enumerate(labels)}:
        raise ValueError("Experiment B label mapping does not match labels.txt order.")
    if groups["banking_intent_mode"] != scope["active_banking_intents"]:
        raise ValueError("Experiment B banking labels do not match active V3 scope.")
    if groups["removed_banking_intents"] != scope["removed_banking_intents"]:
        raise ValueError("Experiment B removed-label metadata does not match V3 scope.")
    if set(groups["removed_banking_intents"]).intersection(labels):
        raise ValueError("A removed banking label appears in Experiment B output labels.")
    if preprocessing["source_sequence_shape"] != [60, 126]:
        raise ValueError("Unexpected source sequence shape.")
    if preprocessing["feature_width"] != 756:
        raise ValueError("Unexpected feature width.")
    if preprocessing["feature_order"] != [
        "mean",
        "std",
        "min",
        "max",
        "first_frame",
        "last_frame",
    ]:
        raise ValueError("Unexpected feature order.")
    if preprocessing["standard_deviation_ddof"] != 0:
        raise ValueError("Flutter requires population standard deviation (ddof=0).")
    if preprocessing["left_hand_indices"] != [0, 62]:
        raise ValueError("Unexpected left-hand slot contract.")
    if preprocessing["right_hand_indices"] != [63, 125]:
        raise ValueError("Unexpected right-hand slot contract.")

    for variant in ("float32", "dynamic_range"):
        result = verification[variant]
        if not result["loads_successfully"]:
            raise ValueError(f"Experiment B {variant} model was not verified.")
        if result["input_shape"] != [1, 756] or result["output_shape"] != [1, 76]:
            raise ValueError(f"Experiment B {variant} tensor shape is invalid.")
        if result["input_dtype"] != "float32" or result["output_dtype"] != "float32":
            raise ValueError(f"Experiment B {variant} dtype contract is invalid.")
        if result["top1_agreement_with_keras"] != 1.0:
            raise ValueError(f"Experiment B {variant} failed top-1 parity.")

    return {
        "labels": labels,
        "groups": groups,
        "verification": verification,
        "preprocessing": preprocessing,
        "scope": scope,
    }


def create_model_metadata(source: dict[str, Any]) -> dict[str, Any]:
    """Build Flutter metadata from the verified source-of-truth files."""
    groups = source["groups"]
    verification = source["verification"]
    preprocessing = source["preprocessing"]
    return {
        "model_version": "sprint_2_16A_v3_40_experiment_B",
        "experiment": "with_augmentation",
        "primary_deployment_variant": "dynamic_range",
        "source_model": (
            "ml/models/sprint_2_16A_v3_40/with_augmentation/"
            "model_dynamic_range.tflite"
        ),
        "fallback_model": (
            "ml/models/sprint_2_16A_v3_40/with_augmentation/"
            "model_float32.tflite"
        ),
        "input_type": "statistical_features",
        "input_shape": verification["dynamic_range"]["input_shape"],
        "output_shape": verification["dynamic_range"]["output_shape"],
        "input_dtype": verification["dynamic_range"]["input_dtype"],
        "output_dtype": verification["dynamic_range"]["output_dtype"],
        "source_sequence_shape": preprocessing["source_sequence_shape"],
        "feature_order": preprocessing["feature_order"],
        "feature_width": preprocessing["feature_width"],
        "standard_deviation_ddof": preprocessing["standard_deviation_ddof"],
        "left_hand_indices": preprocessing["left_hand_indices"],
        "right_hand_indices": preprocessing["right_hand_indices"],
        "missing_hand_representation": "zeros",
        "total_labels": len(source["labels"]),
        "alphabet_mode_labels": len(groups["alphabet_mode"]),
        "number_mode_labels": len(groups["number_mode"]),
        "banking_intent_mode_labels": len(groups["banking_intent_mode"]),
        "label_order_matches_output_indices": True,
        "removed_labels_present": [],
        "source_sha256": {
            "dynamic_range_tflite": sha256(SOURCE_ASSETS[Path("models/model_dynamic_range.tflite")]),
            "float32_tflite": sha256(SOURCE_ASSETS[Path("models/model_float32.tflite")]),
            "labels": sha256(SOURCE_ASSETS[Path("metadata/labels.txt")]),
            "label_mapping": sha256(SOURCE_ASSETS[Path("metadata/label_mapping.json")]),
            "label_groups": sha256(SOURCE_ASSETS[Path("metadata/label_groups.json")]),
            "preprocessing_config": sha256(
                SOURCE_ASSETS[Path("metadata/preprocessing_config.json")]
            ),
        },
    }


def create_backup() -> list[dict[str, Any]]:
    """Create a non-overwriting rollback copy of the deployed 86-class assets."""
    if BACKUP_DIR.exists():
        raise FileExistsError(
            f"Backup already exists and will not be overwritten: {BACKUP_DIR}"
        )
    BACKUP_DIR.mkdir(parents=True, exist_ok=False)
    manifest_rows: list[dict[str, Any]] = []
    for relative_path in CURRENT_ASSET_PATHS:
        source_path = FLUTTER_ASSETS / relative_path
        if not source_path.is_file():
            raise FileNotFoundError(f"Current Flutter asset is missing: {source_path}")
        backup_path = BACKUP_DIR / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, backup_path)
        manifest_rows.append(
            {
                "source_file": source_path.relative_to(ROOT).as_posix(),
                "backup_path": backup_path.relative_to(ROOT).as_posix(),
                "file_size_bytes": source_path.stat().st_size,
                "sha256": sha256(source_path),
            }
        )
    manifest = {
        "backup_version": "pre_sprint_2_16A_experiment_B",
        "purpose": "Rollback snapshot of the deployed Sprint 2.13 86-class Flutter assets.",
        "old_contract": {
            "input_shape": [1, 756],
            "output_shape": [1, 86],
            "label_count": 86,
        },
        "files": manifest_rows,
    }
    (BACKUP_DIR / "backup_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest_rows


def stage_assets(source: dict[str, Any]) -> list[Path]:
    """Copy and validate all new assets before replacing any live asset."""
    if STAGING_DIR.exists():
        raise FileExistsError(f"Staging directory already exists: {STAGING_DIR}")
    staged_paths: list[Path] = []
    for relative_path, source_path in SOURCE_ASSETS.items():
        staged_path = STAGING_DIR / relative_path
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, staged_path)
        if sha256(staged_path) != sha256(source_path):
            raise OSError(f"Staged hash mismatch: {relative_path.as_posix()}")
        staged_paths.append(relative_path)

    metadata_path = STAGING_DIR / "metadata" / "tflite_model_metadata.json"
    metadata_path.write_text(
        json.dumps(create_model_metadata(source), indent=2), encoding="utf-8"
    )
    staged_paths.append(Path("metadata/tflite_model_metadata.json"))

    staged_labels = [
        label.strip()
        for label in (STAGING_DIR / "metadata" / "labels.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if label.strip()
    ]
    staged_metadata = read_json(metadata_path)
    if staged_labels != source["labels"] or staged_metadata["total_labels"] != 76:
        raise ValueError("Staged model metadata failed final validation.")
    return staged_paths


def replace_assets(staged_paths: list[Path]) -> None:
    """Replace the validated asset set, restoring the backup on failure."""
    replaced: list[Path] = []
    try:
        for relative_path in staged_paths:
            target_path = FLUTTER_ASSETS / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(STAGING_DIR / relative_path, target_path)
            replaced.append(relative_path)
    except Exception:
        for relative_path in replaced:
            backup_path = BACKUP_DIR / relative_path
            target_path = FLUTTER_ASSETS / relative_path
            if backup_path.is_file():
                shutil.copy2(backup_path, target_path)
            elif target_path.exists():
                target_path.unlink()
        raise
    finally:
        for directory in (STAGING_DIR / "models", STAGING_DIR / "metadata", STAGING_DIR):
            if directory.exists():
                directory.rmdir()


def main() -> int:
    """Back up the 86-class assets and deploy reviewed Experiment B together."""
    source = validate_source()
    backup_rows = create_backup()
    staged_paths = stage_assets(source)
    replace_assets(staged_paths)

    print("PASS: Sprint 2.16A Experiment B Flutter deployment completed.")
    print(f"Backup files: {len(backup_rows)}")
    print("Primary model: model_dynamic_range.tflite")
    print("Fallback model: model_float32.tflite")
    print("Tensor contract: float32 [1, 756] -> float32 [1, 76]")
    print("Mode labels: alphabet 26 / number 10 / banking 40")
    print(f"Backup manifest: {BACKUP_DIR.relative_to(ROOT).as_posix()}/backup_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit the corrected-account Sprint 2.18 Flutter redeployment."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "ml" / "models" / "sprint_2_17_final_40class_account_corrected_v2"
SOURCE_MODELS = CANDIDATE / "models"
SOURCE_METADATA = CANDIDATE / "metadata"
FLUTTER = ROOT / "flutter_app"
DEPLOYED = FLUTTER / "assets" / "models"
EVIDENCE = ROOT / "docs" / "phase_2_evidence"
PHONE = ROOT / "ml" / "data_phone"
CORRECTION = PHONE / "corrections" / "account_20260719"
DEPLOYMENT_BACKUP = (
    FLUTTER / "assets" / "model_backups" /
    "pre_account_correction_sprint_2_18_20260719"
)
CORRECTED_BACKUP = PHONE / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
INVALID_BACKUP = (
    PHONE / "invalidated_backups" /
    "sprint_2_16B_banking_phone_samples_1000_backup_incorrect_account_20260719.zip"
)
EXPECTED_CORRECTED_BACKUP = (
    "07B5660E08640EA2EAC11216E41F4696D01BE52627CF3E1DD15D46F99C20286A"
)
EXPECTED_INVALID_BACKUP = (
    "F3F76C6BBE06305C7AE82E2772C5DACA7F76619444F7ECA892D7AA253986B70B"
)
EXPECTED_COLLECTION_PAGE = (
    "CDC0D7355AC0EC3CCC9EC9B88DEF8D88898BD1C2B1E9C0CFBD46DA6308604FC9"
)
FINAL_LABELS = [
    "deposit", "withdraw", "balance", "transfer", "account", "card", "pin",
    "password", "identity_verification", "cash", "payment", "fee", "loan",
    "savings", "open_account", "close_account", "fraud", "block_card", "help",
    "confirm", "statement", "document", "bill_payment", "atm", "branch",
    "cheque", "interest_rate", "credit_card", "debit_card", "lost_card",
    "replace_card", "change_pin", "reset_password", "refund", "signature",
    "complaint", "appointment", "account_number", "card_limit", "daily_limit",
]


def main() -> int:
    """Verify corrected source, Flutter assets, runtime contract, and preservation."""
    manifest = read_json(DEPLOYED / "model_deployment_manifest.json")
    labels = read_json(DEPLOYED / "labels_40.json")
    recommendation = read_json(DEPLOYED / "confidence_recommendation_40class.json")
    change = read_json(CORRECTION / "dataset_change_summary.json")
    parity = read_json(SOURCE_METADATA / "tflite_verification.json")
    checks: dict[str, bool] = {}

    checksum_failures = verify_candidate_checksums()
    checks["corrected_candidate_checksums"] = not checksum_failures

    artifacts = artifact_rows()
    checks["source_to_flutter_hashes_match"] = all(row["match"] for row in artifacts)
    checks["exact_40_label_order"] = labels == FINAL_LABELS
    checks["account_index_4"] = labels.index("account") == 4
    checks["savings_index_13"] = labels.index("savings") == 13

    checks["corrected_manifest_identity"] = (
        manifest["model_version"] == "signsync_40class_account_corrected_v2"
        and manifest["dataset_version"] == "corrected_account_dataset_v2"
        and manifest["deployment_status"]
        == "deployed_for_account_savings_a55_verification"
    )
    checks["corrected_manifest_contract"] = (
        manifest["input_shape"] == [1, 756]
        and manifest["output_shape"] == [1, 40]
        and manifest["input_dtype"] == "float32"
        and manifest["output_dtype"] == "float32"
        and manifest["label_count"] == 40
    )
    checks["validation_selected_confidence_policy"] = (
        recommendation["minimum_confidence"] == 0.8
        and recommendation["minimum_top2_margin"] == 0.0
        and recommendation["selected_using"] == "phone validation only"
        and manifest["confidence_threshold"] == 0.8
        and manifest["minimum_margin"] == 0.0
    )
    checks["manifest_asset_hashes_match"] = verify_manifest_hashes(manifest, artifacts)

    query = read_json(FLUTTER / "assets" / "content" / "banking_queries.json")
    checks["query_mapping_exact"] = (
        [item["id"] for item in query["intents"]] == labels
        and sum(len(item["queries"]) for item in query["intents"]) == 160
    )

    app_config = (FLUTTER / "lib" / "config" / "app_config.dart").read_text(
        encoding="utf-8"
    )
    pubspec = (FLUTTER / "pubspec.yaml").read_text(encoding="utf-8")
    active = f"{app_config}\n{pubspec}"
    checks["active_runtime_uses_corrected_assets"] = all(
        name in active
        for name in (
            "signsync_40class_account_corrected_v2_dynamic_range.tflite",
            "signsync_40class_account_corrected_v2_float32.tflite",
        )
    )
    checks["invalid_v1_assets_not_active"] = all(
        name not in active
        for name in (
            "assets/models/signsync_40class_dynamic_range.tflite",
            "assets/models/signsync_40class_float32.tflite",
        )
    )

    contracts, inference = verify_real_models()
    checks["dynamic_tflite_contract"] = contracts["dynamic"]["passed"]
    checks["float32_tflite_contract"] = contracts["float32"]["passed"]
    checks["real_inference_finite_probabilities"] = inference["finite_probabilities"]
    checks["dynamic_float32_top1_agreement"] = inference["top1_agreement"]
    checks["offline_parity_passed"] = (
        parity["status"] == "PASS"
        and parity["keras_float32_top1_agreement"] == 1.0
        and parity["keras_dynamic_top1_agreement"] == 1.0
    )

    checks["corrected_dataset_integrity"] = (
        change["status"] == "PASS"
        and change["corrected_total"] == 1000
        and change["unchanged_non_account_samples"] == 975
        and change["replaced_account_samples"] == 25
        and not change["unexpected_changed_files"]
    )
    checks["corrected_backup_hash"] = sha256_file(CORRECTED_BACKUP) == EXPECTED_CORRECTED_BACKUP
    checks["invalid_backup_preserved"] = sha256_file(INVALID_BACKUP) == EXPECTED_INVALID_BACKUP
    checks["invalid_account_archive_preserved"] = len(
        list((PHONE / "invalidated" / "account_incorrect_gesture_20260719").glob("*.json"))
    ) == 25
    checks["old_package_superseded"] = (
        read_json(ROOT / "ml" / "models" / "sprint_2_17_final_40class_SUPERSEDED.json")["status"]
        == "SUPERSEDED - TRAINED WITH INCORRECT ACCOUNT GESTURE DATA"
    )
    checks["old_deployment_backup_complete"] = verify_deployment_backup()
    checks["collection_page_unchanged"] = sha256_file(
        FLUTTER / "lib" / "ui" / "phone_dataset_collection_page.dart"
    ) == EXPECTED_COLLECTION_PAGE
    checks.update(verify_package_ids())

    apk_path = FLUTTER / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
    apk = {
        "path": relative_path(apk_path),
        "exists": apk_path.is_file(),
        "size_bytes": apk_path.stat().st_size if apk_path.is_file() else None,
        "sha256": sha256_file(apk_path) if apk_path.is_file() else None,
    }
    checks["debug_apk_exists"] = bool(apk["exists"])

    report = {
        "project": "SignSync",
        "sprint": "2.18 corrective redeployment",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "candidate_checksum_failures": checksum_failures,
        "artifacts": artifacts,
        "deployment_manifest_sha256": sha256_file(
            DEPLOYED / "model_deployment_manifest.json"
        ),
        "contracts": contracts,
        "fixed_inference": inference,
        "corrected_backup_sha256": sha256_file(CORRECTED_BACKUP),
        "invalid_backup_sha256": sha256_file(INVALID_BACKUP),
        "apk": apk,
        "physical_a55_status": "pending_manual_account_savings_verification",
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    write_json(EVIDENCE / "account_corrected_deployment_validation.json", report)
    write_csv(
        EVIDENCE / "account_corrected_artifact_hash_comparison.csv",
        artifacts,
        list(artifacts[0]),
    )
    write_markdown(report)

    print("Corrected Account Flutter Deployment Audit")
    print("------------------------------------------")
    print(f"status: {report['status']}")
    print("contract: [1, 756] float32 -> [1, 40] float32")
    print("confidence policy: 0.80 confidence, 0.00 margin")
    print(f"source/deployed asset matches: {sum(row['match'] for row in artifacts)}/{len(artifacts)}")
    print(f"dataset: {change['corrected_total']} total; 25 corrected account; 975 unchanged")
    print(f"APK: {apk['path']} ({apk['size_bytes']} bytes)")
    if report["status"] != "PASS":
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Corrected deployment audit failed: {failed}")
    print("PASS: corrected Flutter deployment and preservation checks passed.")
    return 0


def artifact_rows() -> list[dict[str, Any]]:
    pairs = [
        (
            "dynamic_range_model",
            SOURCE_MODELS / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
            DEPLOYED / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
        ),
        (
            "float32_model",
            SOURCE_MODELS / "signsync_40class_account_corrected_v2_float32.tflite",
            DEPLOYED / "signsync_40class_account_corrected_v2_float32.tflite",
        ),
        ("labels", SOURCE_METADATA / "labels_40.json", DEPLOYED / "labels_40.json"),
        (
            "model_metadata",
            SOURCE_METADATA / "model_metadata.json",
            DEPLOYED / "model_metadata_40class.json",
        ),
        (
            "feature_contract",
            SOURCE_METADATA / "feature_contract.json",
            DEPLOYED / "feature_contract_40class.json",
        ),
        (
            "confidence_recommendation",
            SOURCE_METADATA / "confidence_recommendation.json",
            DEPLOYED / "confidence_recommendation_40class.json",
        ),
    ]
    return [
        {
            "role": role,
            "source_path": relative_path(source),
            "source_sha256": sha256_file(source),
            "deployed_path": relative_path(deployed),
            "deployed_sha256": sha256_file(deployed),
            "size_bytes": deployed.stat().st_size,
            "match": sha256_file(source) == sha256_file(deployed),
        }
        for role, source, deployed in pairs
    ]


def verify_candidate_checksums() -> list[str]:
    failures = []
    for line in (SOURCE_METADATA / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = CANDIDATE / Path(relative)
        if not path.is_file() or sha256_file(path) != expected.upper():
            failures.append(relative)
    return failures


def verify_manifest_hashes(manifest: dict[str, Any], artifacts: list[dict[str, Any]]) -> bool:
    by_role = {row["role"]: row["deployed_sha256"] for row in artifacts}
    hashes = manifest["deployed_asset_sha256"]
    return (
        hashes["dynamic_range"] == by_role["dynamic_range_model"]
        and hashes["float32"] == by_role["float32_model"]
        and hashes["labels"] == by_role["labels"]
        and hashes["model_metadata"] == by_role["model_metadata"]
        and hashes["feature_contract"] == by_role["feature_contract"]
        and hashes["confidence_recommendation"] == by_role["confidence_recommendation"]
    )


def verify_real_models() -> tuple[dict[str, Any], dict[str, Any]]:
    import tensorflow as tf

    with np.load(
        ROOT / "ml" / "data_phone" / "sprint_2_17_40class_account_corrected_v2"
        / "features" / "phone_test_features_locked.npz",
        allow_pickle=False,
    ) as archive:
        feature = archive["X"][0].astype(np.float32).reshape(1, 756)
        actual_index = int(archive["y"][0])
        sample_id = str(archive["sample_ids"][0])
    paths = {
        "dynamic": DEPLOYED / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
        "float32": DEPLOYED / "signsync_40class_account_corrected_v2_float32.tflite",
    }
    contracts: dict[str, Any] = {}
    outputs: dict[str, np.ndarray] = {}
    for name, path in paths.items():
        interpreter = tf.lite.Interpreter(model_path=path.as_posix())
        interpreter.allocate_tensors()
        input_detail = interpreter.get_input_details()[0]
        output_detail = interpreter.get_output_details()[0]
        interpreter.set_tensor(input_detail["index"], feature)
        interpreter.invoke()
        outputs[name] = interpreter.get_tensor(output_detail["index"])[0].astype(np.float32)
        contracts[name] = {
            "input_shape": input_detail["shape"].astype(int).tolist(),
            "output_shape": output_detail["shape"].astype(int).tolist(),
            "input_dtype": np.dtype(input_detail["dtype"]).name,
            "output_dtype": np.dtype(output_detail["dtype"]).name,
            "passed": (
                input_detail["shape"].astype(int).tolist() == [1, 756]
                and output_detail["shape"].astype(int).tolist() == [1, 40]
                and np.dtype(input_detail["dtype"]).name == "float32"
                and np.dtype(output_detail["dtype"]).name == "float32"
            ),
        }
    dynamic_top1 = int(np.argmax(outputs["dynamic"]))
    float_top1 = int(np.argmax(outputs["float32"]))
    finite = all(
        output.shape == (40,)
        and np.isfinite(output).all()
        and np.allclose(output.sum(), 1.0, atol=1e-4)
        for output in outputs.values()
    )
    return contracts, {
        "sample_id": sample_id,
        "actual_index": actual_index,
        "actual_label": FINAL_LABELS[actual_index],
        "dynamic_top1_index": dynamic_top1,
        "dynamic_top1_label": FINAL_LABELS[dynamic_top1],
        "float32_top1_index": float_top1,
        "float32_top1_label": FINAL_LABELS[float_top1],
        "top1_agreement": dynamic_top1 == float_top1,
        "finite_probabilities": finite,
        "maximum_absolute_difference": float(
            np.max(np.abs(outputs["dynamic"] - outputs["float32"]))
        ),
    }


def verify_deployment_backup() -> bool:
    required = {
        "README.md", "SHA256SUMS.txt", "backup_manifest.json", "app_config.dart.txt",
        "pubspec.yaml.txt", "signsync_40class_dynamic_range.tflite",
        "signsync_40class_float32.tflite", "labels_40.json",
        "model_metadata_40class.json", "feature_contract_40class.json",
        "confidence_recommendation_40class.json", "model_deployment_manifest.json",
    }
    if not all((DEPLOYMENT_BACKUP / name).is_file() for name in required):
        return False
    for line in (DEPLOYMENT_BACKUP / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        if sha256_file(DEPLOYMENT_BACKUP / name) != expected:
            return False
    return True


def verify_package_ids() -> dict[str, bool]:
    gradle = (FLUTTER / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    ios = (FLUTTER / "ios" / "Runner.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    return {
        "android_namespace_unchanged": 'namespace = "com.example.flutter_app"' in gradle,
        "android_application_id_unchanged": 'applicationId = "com.example.flutter_app"' in gradle,
        "ios_bundle_id_unchanged": "PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;" in ios,
    }


def write_markdown(report: dict[str, Any]) -> None:
    checks = "\n".join(
        f"- [{'x' if passed else ' '}] {name.replace('_', ' ')}"
        for name, passed in report["checks"].items()
    )
    (EVIDENCE / "account_corrected_deployment_validation.md").write_text(
        f"""# Corrected Account Flutter Deployment Validation

## Status: {report['status']}

The corrected-account v2 model is deployed under new versioned Flutter asset names. The previous Sprint 2.18 deployment is preserved as superseded evidence and is no longer active.

## Runtime Contract

- Input: float32 `[1,756]`
- Output: float32 `[1,40]`
- Policy: confidence `0.80`, minimum top-2 margin `0.00`
- Scope: banking intents only
- Physical Samsung A55 status: pending manual account-versus-savings verification

## Artifact and APK Evidence

- Deployment manifest SHA-256: `{report['deployment_manifest_sha256']}`
- Corrected backup SHA-256: `{report['corrected_backup_sha256']}`
- APK: `{report['apk']['path']}`
- APK size: {report['apk']['size_bytes']} bytes
- APK SHA-256: `{report['apk']['sha256']}`

## Checks

{checks}

No uninstall, storage clear, database, cloud processing, formal Sprint 2.19 evaluation, commit, or push is part of this corrective deployment.
""",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify the frozen Sprint 2.17 candidate deployment into Flutter."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
FLUTTER = ROOT / "flutter_app"
CANDIDATE = ROOT / "ml" / "models" / "sprint_2_17_final_40class"
SOURCE_MODELS = CANDIDATE / "models"
SOURCE_METADATA = CANDIDATE / "metadata"
DEPLOYED_MODELS = FLUTTER / "assets" / "models"
EVIDENCE = ROOT / "docs" / "phase_2_evidence"
PHONE_SAMPLES = ROOT / "ml" / "data_phone" / "landmark_samples"
PHONE_HASH_MANIFEST = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_17_40class"
    / "checksums"
    / "phone_source_json_sha256.csv"
)
PHONE_BACKUP = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
)
EXPECTED_BACKUP_SHA256 = (
    "F3F76C6BBE06305C7AE82E2772C5DACA7F76619444F7ECA892D7AA253986B70B"
)
EXPECTED_CANDIDATE_SHA256S_HASH = (
    "10B129E9C91F0CF89F0332F1460BB2D78160635C04BC1634DC9B4CF495CF584B"
)
EXPECTED_OLD_DYNAMIC_SHA256 = (
    "88CDC0367F40E50081E5BDE7644EDE242937061843CB68EA1235214E62308DDD"
)
EXPECTED_OLD_FLOAT32_SHA256 = (
    "36EC44E5EBEFD1C7DE56161A305324488BFD6CFC58337CA9B2679198F424FAC8"
)

FINAL_LABELS = [
    "deposit",
    "withdraw",
    "balance",
    "transfer",
    "account",
    "card",
    "pin",
    "password",
    "identity_verification",
    "cash",
    "payment",
    "fee",
    "loan",
    "savings",
    "open_account",
    "close_account",
    "fraud",
    "block_card",
    "help",
    "confirm",
    "statement",
    "document",
    "bill_payment",
    "atm",
    "branch",
    "cheque",
    "interest_rate",
    "credit_card",
    "debit_card",
    "lost_card",
    "replace_card",
    "change_pin",
    "reset_password",
    "refund",
    "signature",
    "complaint",
    "appointment",
    "account_number",
    "card_limit",
    "daily_limit",
]
REMOVED_LABELS = {
    "online_banking",
    "mobile_banking",
    "currency_exchange",
    "exchange_rate",
    "fixed_deposit",
    "customer_service",
    "update_details",
    "phone_number",
    "email_address",
    "address_change",
}


def main() -> int:
    """Run deployment, contract, preservation, and inference checks."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}
    package_failures = _verify_candidate_package()
    checks["candidate_package_checksums"] = not package_failures
    checks["candidate_sha256s_file_unchanged"] = (
        sha256_file(SOURCE_METADATA / "SHA256SUMS.txt")
        == EXPECTED_CANDIDATE_SHA256S_HASH
    )

    artifacts = _artifact_rows()
    checks["source_to_flutter_model_hashes"] = all(
        row["match"] == "True"
        for row in artifacts
        if row["role"] in {"dynamic_range_model", "float32_model", "labels"}
    )
    checks["all_deployment_assets_exist"] = all(
        (ROOT / row["deployed_path"]).is_file() for row in artifacts
    )

    labels = read_json(DEPLOYED_MODELS / "labels_40.json")
    checks["exact_40_label_order"] = labels == FINAL_LABELS
    checks["no_alphabet_or_digit_labels"] = not any(
        (len(label) == 1 and label.isalnum()) for label in labels
    )
    checks["no_removed_labels"] = not set(labels).intersection(REMOVED_LABELS)

    query = read_json(FLUTTER / "assets" / "content" / "banking_queries.json")
    query_ids = [intent["id"] for intent in query["intents"]]
    query_count = sum(len(intent["queries"]) for intent in query["intents"])
    checks["query_mapping_exact"] = query_ids == labels and query_count == 160

    recommendation = read_json(
        DEPLOYED_MODELS / "confidence_recommendation_40class.json"
    )
    checks["confidence_policy_frozen"] = (
        recommendation["minimum_confidence"] == 0.9
        and recommendation["minimum_top2_margin"] == 0.0
        and recommendation["selected_using"] == "phone validation only"
    )

    manifest_path = DEPLOYED_MODELS / "model_deployment_manifest.json"
    manifest = read_json(manifest_path)
    checks.update(_verify_deployment_manifest(manifest, artifacts, labels))

    contracts, inference = _verify_real_tflite_models()
    checks["dynamic_tflite_contract"] = contracts["dynamic_range"]["passed"]
    checks["float32_tflite_contract"] = contracts["float32"]["passed"]
    checks["real_inference_40_finite_probabilities"] = inference[
        "finite_40_probabilities"
    ]
    checks["dynamic_float32_fixed_fixture_agreement"] = inference[
        "top1_agreement"
    ]

    backup = (
        FLUTTER
        / "assets"
        / "model_backups"
        / "pre_sprint_2_18_76class_20260718_142840"
    )
    checks["old_76class_backup_complete"] = _verify_old_backup(backup)

    app_config = (FLUTTER / "lib" / "config" / "app_config.dart").read_text(
        encoding="utf-8"
    )
    pubspec = (FLUTTER / "pubspec.yaml").read_text(encoding="utf-8")
    active_text = f"{app_config}\n{pubspec}"
    checks["active_runtime_uses_versioned_40class_assets"] = all(
        value in active_text
        for value in (
            "signsync_40class_dynamic_range.tflite",
            "signsync_40class_float32.tflite",
            "labels_40.json",
            "model_deployment_manifest.json",
        )
    )
    checks["no_active_old_model_references"] = all(
        value not in active_text
        for value in (
            "assets/models/model_dynamic_range.tflite",
            "assets/models/model_float32.tflite",
            "assets/metadata/labels.txt",
        )
    )
    checks["banking_only_runtime"] = (
        "bankingOnlyRecognition = true" in app_config
        and "expectedOutputClasses = 40" in app_config
    )

    checks.update(_verify_package_identifiers())
    raw_paths = sorted(PHONE_SAMPLES.rglob("*.json"))
    checks["phone_sample_count_1000"] = len(raw_paths) == 1000
    checks["raw_phone_hashes_unchanged"] = _verify_phone_hashes()
    checks["phone_backup_hash_unchanged"] = (
        sha256_file(PHONE_BACKUP) == EXPECTED_BACKUP_SHA256
    )

    apk_path = FLUTTER / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
    apk = {
        "path": relative_path(apk_path),
        "exists": apk_path.is_file(),
        "size_bytes": apk_path.stat().st_size if apk_path.is_file() else None,
        "sha256": sha256_file(apk_path) if apk_path.is_file() else None,
    }
    source_model_hashes = {
        "keras": sha256_file(SOURCE_MODELS / "signsync_40class_final.keras"),
        "float32_tflite": sha256_file(
            SOURCE_MODELS / "signsync_40class_float32.tflite"
        ),
        "dynamic_range_tflite": sha256_file(
            SOURCE_MODELS / "signsync_40class_dynamic_range.tflite"
        ),
        "labels": sha256_file(SOURCE_METADATA / "labels_40.json"),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "project": "SignSync",
        "sprint": "2.18",
        "status": status,
        "checks": checks,
        "candidate_checksum_failures": package_failures,
        "label_count": len(labels),
        "query_count": query_count,
        "contracts": contracts,
        "fixed_fixture_inference": inference,
        "source_model_hashes": source_model_hashes,
        "artifact_hashes": artifacts,
        "deployment_manifest_sha256": sha256_file(manifest_path),
        "raw_phone_sample_count": len(raw_paths),
        "dataset_backup_sha256": sha256_file(PHONE_BACKUP),
        "apk": apk,
        "physical_a55_verification": "pending",
        "deployment_scope": "automated deployment verification only",
        "training_or_conversion_performed": False,
    }
    write_json(EVIDENCE / "sprint_2_18_deployment_validation.json", report)
    write_csv(
        EVIDENCE / "sprint_2_18_artifact_hash_comparison.csv",
        artifacts,
        [
            "role",
            "source_path",
            "source_sha256",
            "deployed_path",
            "deployed_sha256",
            "size_bytes",
            "match",
        ],
    )
    write_markdown(report)

    print("Sprint 2.18 Flutter Deployment Verification")
    print("-------------------------------------------")
    print(f"Candidate checksum failures: {len(package_failures)}")
    print(f"Deployed labels: {len(labels)}")
    print(f"Query mappings: {len(query_ids)} labels / {query_count} queries")
    print("Dynamic contract: [1, 756] float32 -> [1, 40] float32")
    print("Float32 contract: [1, 756] float32 -> [1, 40] float32")
    print(f"Fixed-fixture top-1 agreement: {inference['top1_agreement']}")
    print(f"Phone samples unchanged: {len(raw_paths)}")
    print(f"Dataset backup SHA-256: {sha256_file(PHONE_BACKUP)}")
    print(f"Physical Samsung A55 verification: pending")
    print(f"Status: {status}")
    if status != "PASS":
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"Deployment checks failed: {', '.join(failed)}")
    return 0


def _verify_candidate_package() -> list[str]:
    failures = []
    checksum_path = SOURCE_METADATA / "SHA256SUMS.txt"
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = CANDIDATE / Path(relative)
        if not path.is_file() or sha256_file(path) != expected.upper():
            failures.append(relative)
    return failures


def _artifact_rows() -> list[dict[str, object]]:
    pairs = [
        (
            "dynamic_range_model",
            SOURCE_MODELS / "signsync_40class_dynamic_range.tflite",
            DEPLOYED_MODELS / "signsync_40class_dynamic_range.tflite",
        ),
        (
            "float32_model",
            SOURCE_MODELS / "signsync_40class_float32.tflite",
            DEPLOYED_MODELS / "signsync_40class_float32.tflite",
        ),
        (
            "labels",
            SOURCE_METADATA / "labels_40.json",
            DEPLOYED_MODELS / "labels_40.json",
        ),
        (
            "model_metadata",
            SOURCE_METADATA / "model_metadata.json",
            DEPLOYED_MODELS / "model_metadata_40class.json",
        ),
        (
            "feature_contract",
            SOURCE_METADATA / "feature_contract.json",
            DEPLOYED_MODELS / "feature_contract_40class.json",
        ),
        (
            "confidence_recommendation",
            SOURCE_METADATA / "confidence_recommendation.json",
            DEPLOYED_MODELS / "confidence_recommendation_40class.json",
        ),
    ]
    rows = []
    for role, source, deployed in pairs:
        source_hash = sha256_file(source)
        deployed_hash = sha256_file(deployed)
        rows.append(
            {
                "role": role,
                "source_path": relative_path(source),
                "source_sha256": source_hash,
                "deployed_path": relative_path(deployed),
                "deployed_sha256": deployed_hash,
                "size_bytes": deployed.stat().st_size,
                "match": str(source_hash == deployed_hash),
            }
        )
    return rows


def _verify_deployment_manifest(
    manifest: dict[str, Any], artifacts: list[dict[str, object]], labels: list[str]
) -> dict[str, bool]:
    deployed_hashes = {
        str(row["role"]): str(row["deployed_sha256"]) for row in artifacts
    }
    manifest_hashes = manifest["deployed_asset_sha256"]
    return {
        "deployment_manifest_identity": (
            manifest["project"] == "SignSync"
            and manifest["sprint"] == "2.18"
            and manifest["model_version"] == "signsync_40class_sprint_2_17_v1"
            and manifest["deployment_status"] == "deployed_for_a55_verification"
        ),
        "deployment_manifest_contract": (
            manifest["input_shape"] == [1, 756]
            and manifest["output_shape"] == [1, 40]
            and manifest["input_dtype"] == "float32"
            and manifest["output_dtype"] == "float32"
            and manifest["label_count"] == len(labels) == 40
        ),
        "deployment_manifest_policy": (
            manifest["confidence_threshold"] == 0.9
            and manifest["minimum_margin"] == 0.0
            and manifest["recognition_scope"]["banking_intents_only"] is True
            and manifest["recognition_scope"]["alphabet_mode_active"] is False
            and manifest["recognition_scope"]["number_mode_active"] is False
        ),
        "deployment_manifest_hashes": (
            manifest_hashes["dynamic_range"]
            == deployed_hashes["dynamic_range_model"]
            and manifest_hashes["float32"] == deployed_hashes["float32_model"]
            and manifest_hashes["labels"] == deployed_hashes["labels"]
        ),
        "deployment_manifest_package_ids": (
            manifest["package_identifiers"]["android_namespace"]
            == "com.example.flutter_app"
            and manifest["package_identifiers"]["android_application_id"]
            == "com.example.flutter_app"
            and manifest["package_identifiers"]["ios_bundle_id"]
            == "com.example.flutterApp"
        ),
    }


def _verify_real_tflite_models() -> tuple[dict[str, Any], dict[str, Any]]:
    import tensorflow as tf

    paths = {
        "dynamic_range": DEPLOYED_MODELS / "signsync_40class_dynamic_range.tflite",
        "float32": DEPLOYED_MODELS / "signsync_40class_float32.tflite",
    }
    fixture = read_json(FLUTTER / "assets" / "test_features" / "P02_payment_R01.json")
    features = np.asarray(fixture["features"], dtype=np.float32).reshape(1, 756)
    contracts: dict[str, Any] = {}
    outputs: dict[str, np.ndarray] = {}
    for name, path in paths.items():
        interpreter = tf.lite.Interpreter(model_path=path.as_posix())
        interpreter.allocate_tensors()
        input_detail = interpreter.get_input_details()[0]
        output_detail = interpreter.get_output_details()[0]
        interpreter.set_tensor(input_detail["index"], features)
        interpreter.invoke()
        output = interpreter.get_tensor(output_detail["index"])[0].astype(np.float32)
        outputs[name] = output
        passed = (
            input_detail["shape"].astype(int).tolist() == [1, 756]
            and output_detail["shape"].astype(int).tolist() == [1, 40]
            and np.dtype(input_detail["dtype"]).name == "float32"
            and np.dtype(output_detail["dtype"]).name == "float32"
        )
        contracts[name] = {
            "input_shape": input_detail["shape"].astype(int).tolist(),
            "output_shape": output_detail["shape"].astype(int).tolist(),
            "input_dtype": np.dtype(input_detail["dtype"]).name,
            "output_dtype": np.dtype(output_detail["dtype"]).name,
            "passed": passed,
        }
    dynamic_top1 = int(np.argmax(outputs["dynamic_range"]))
    float_top1 = int(np.argmax(outputs["float32"]))
    finite = all(
        output.shape == (40,)
        and np.isfinite(output).all()
        and np.allclose(np.sum(output), 1.0, atol=1e-4)
        for output in outputs.values()
    )
    return contracts, {
        "fixture": "flutter_app/assets/test_features/P02_payment_R01.json",
        "fixture_label": fixture["true_label"],
        "dynamic_top1_index": dynamic_top1,
        "dynamic_top1_label": FINAL_LABELS[dynamic_top1],
        "float32_top1_index": float_top1,
        "float32_top1_label": FINAL_LABELS[float_top1],
        "top1_agreement": dynamic_top1 == float_top1,
        "finite_40_probabilities": finite,
        "maximum_absolute_probability_difference": float(
            np.max(np.abs(outputs["dynamic_range"] - outputs["float32"]))
        ),
    }


def _verify_old_backup(backup: Path) -> bool:
    required = [
        backup / "README.md",
        backup / "SHA256SUMS.txt",
        backup / "backup_manifest.json",
        backup / "models" / "model_dynamic_range.tflite",
        backup / "models" / "model_float32.tflite",
        backup / "metadata" / "labels.txt",
        backup / "runtime" / "app_config.dart.txt",
        backup / "apk" / "app-debug-pre-sprint-2-18.apk",
    ]
    return (
        all(path.is_file() for path in required)
        and sha256_file(backup / "models" / "model_dynamic_range.tflite")
        == EXPECTED_OLD_DYNAMIC_SHA256
        and sha256_file(backup / "models" / "model_float32.tflite")
        == EXPECTED_OLD_FLOAT32_SHA256
    )


def _verify_package_identifiers() -> dict[str, bool]:
    gradle = (FLUTTER / "android" / "app" / "build.gradle.kts").read_text(
        encoding="utf-8"
    )
    ios_project = (
        FLUTTER / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    ).read_text(encoding="utf-8")
    return {
        "android_namespace_unchanged": (
            'namespace = "com.example.flutter_app"' in gradle
        ),
        "android_application_id_unchanged": (
            'applicationId = "com.example.flutter_app"' in gradle
        ),
        "ios_bundle_id_unchanged": (
            "PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;" in ios_project
        ),
    }


def _verify_phone_hashes() -> bool:
    with PHONE_HASH_MANIFEST.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    return len(rows) == 1000 and all(
        sha256_file(ROOT / Path(row["source_path"])) == row["file_sha256"].upper()
        for row in rows
    )


def write_markdown(report: dict[str, Any]) -> None:
    checks = "\n".join(
        f"- [{'x' if passed else ' '}] {name.replace('_', ' ')}"
        for name, passed in report["checks"].items()
    )
    inference = report["fixed_fixture_inference"]
    apk = report["apk"]
    source_hashes = report["source_model_hashes"]
    artifact_hashes = "\n".join(
        f"- {row['role']}: source `{row['source_sha256']}`; "
        f"deployed `{row['deployed_sha256']}`; match {row['match']}"
        for row in report["artifact_hashes"]
    )
    (EVIDENCE / "sprint_2_18_deployment_validation.md").write_text(
        f"""# Sprint 2.18 Automated Deployment Validation

## Status: {report['status']}

The frozen Sprint 2.17 40-class candidate was copied without retraining, reconversion, or weight changes. Automated checks verify source-to-Flutter hashes, exact labels, real TFLite contracts, query mapping, confidence policy, active runtime paths, package identifiers, and dataset preservation.

## Contract

- Input: float32 `[1,756]`
- Output: float32 `[1,40]`
- Labels: 40 banking intents in frozen order
- Confidence threshold: 0.90
- Minimum margin: 0.00
- Default: dynamic-range TFLite
- Fallback/reference: float32 TFLite

## Complete SHA-256 Record

- Source Keras: `{source_hashes['keras']}`
- Source float32 TFLite: `{source_hashes['float32_tflite']}`
- Source dynamic-range TFLite: `{source_hashes['dynamic_range_tflite']}`
- Source labels: `{source_hashes['labels']}`
- Deployment manifest: `{report['deployment_manifest_sha256']}`

{artifact_hashes}

## Real Fixed-Fixture Inference

- Fixture: `{inference['fixture']}`
- Dynamic top-1: `{inference['dynamic_top1_label']}`
- Float32 top-1: `{inference['float32_top1_label']}`
- Top-1 agreement: {inference['top1_agreement']}
- Finite 40-value outputs: {inference['finite_40_probabilities']}

## APK

- Path: `{apk['path']}`
- Exists at checker run: {apk['exists']}
- Size: {apk['size_bytes']}
- SHA-256: `{apk['sha256']}`

## Checks

{checks}

## Boundary

Physical Samsung A55 verification, the all-40 live smoke test, focused weak-class attempts, and mobile timing observations remain pending. No physical success is claimed by this automated report, and Sprint 2.19 was not started.
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


def write_csv(
    path: Path, rows: list[dict[str, object]], fieldnames: list[str]
) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

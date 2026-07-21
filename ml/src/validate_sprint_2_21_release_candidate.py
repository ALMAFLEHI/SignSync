"""Fail-safe validation for the frozen SignSync Sprint 2.21 release candidate.

The validator is read-only. It never trains, converts, edits datasets, changes
queries, or rewrites protected artifacts. Any mismatch raises a clear error and
returns a non-zero exit code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MODEL_PACKAGE = (
    ROOT / "ml" / "models" / "sprint_2_17_final_40class_account_corrected_v2"
)
MODEL_DIR = MODEL_PACKAGE / "models"
MODEL_METADATA = MODEL_PACKAGE / "metadata"
MODEL_METRICS = MODEL_PACKAGE / "metrics"
PHONE_SAMPLES = ROOT / "ml" / "data_phone" / "landmark_samples"
RELEASE_ROOT = ROOT / "releases" / "SignSync_RC1"
QUERY_PATH = ROOT / "flutter_app" / "assets" / "content" / "banking_queries.json"

FINAL_LABELS = (
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
)
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
PROTECTED_ARTIFACTS = {
    "keras": (
        MODEL_DIR / "signsync_40class_account_corrected_v2.keras",
        "F1D543E0D0E5E8C699B53DA5DD7CAAEBC160695599C4C2D078C6FDDDD1DB120D",
    ),
    "float32_tflite": (
        MODEL_DIR / "signsync_40class_account_corrected_v2_float32.tflite",
        "D9686110BACFB1F1C5B3BFBF33B2C515393344869A3DCEAFF325903A34DF278C",
    ),
    "dynamic_range_tflite": (
        MODEL_DIR / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
        "BD46131FF20ECB96F240C867C60804A2D9F514AC4F56D63F64E8B60188187A17",
    ),
    "deployment_manifest": (
        ROOT
        / "flutter_app"
        / "assets"
        / "models"
        / "model_deployment_manifest.json",
        "F02E35864C87925A6D06D70F669411388B2F04112F757CB0DF2AAD1296A2F9F1",
    ),
    "dataset_manifest": (
        ROOT
        / "ml"
        / "data_phone"
        / "corrections"
        / "account_20260719"
        / "corrected_phone_source_json_sha256.csv",
        "677C4ED15F11CE4BEE07754948CCEB21E324BDC1C3481CF265E884F773710D03",
    ),
    "corrected_backup": (
        ROOT
        / "ml"
        / "data_phone"
        / "sprint_2_16B_banking_phone_samples_1000_backup.zip",
        "07B5660E08640EA2EAC11216E41F4696D01BE52627CF3E1DD15D46F99C20286A",
    ),
    "query_configuration": (
        QUERY_PATH,
        "6F52D50F8FBBF64CD43479A1A6135F3886164D7857B1430090589D2CCCEC6B51",
    ),
}
REQUIRED_DOCS = (
    "docs/sprints/sprint_2_21_final_stabilization_release_candidate.md",
    "docs/phase_2_evidence/sprint_2_21_release_validation.md",
    "docs/phase_2_evidence/sprint_2_21_privacy_offline_audit.md",
    "docs/phase_2_evidence/sprint_2_21_regression_matrix.md",
    "docs/phase_2_evidence/sprint_2_21_environment_manifest.md",
    "docs/phase_2_evidence/sprint_2_21_final_artifact_inventory.md",
    "docs/phase_2_evidence/sprint_2_21_known_limitations.md",
    "docs/phase_2_evidence/sprint_2_21_final_project_status.md",
    "docs/final/SignSync_installation_guide.md",
    "docs/final/SignSync_demonstration_guide.md",
    "docs/final/SignSync_user_workflow_guide.md",
    "docs/final/SignSync_developer_handover.md",
    "docs/final/SignSync_evidence_index.md",
    "docs/final/SignSync_requirements_traceability_matrix.md",
)
FIGURE_NAMES = (
    "Sprint_2_21_Final_Release_Status.png",
    "Sprint_2_21_Test_Summary_PASS.png",
    "Sprint_2_21_Regression_Matrix_PASS.png",
    "Sprint_2_21_Privacy_Offline_Audit_PASS.png",
    "Sprint_2_21_Model_Dataset_Query_Integrity_PASS.png",
    "Sprint_2_21_APK_Build_And_Hash.png",
    "Sprint_2_21_Requirements_Traceability.png",
    "Sprint_2_21_Final_Artifact_Inventory.png",
    "Sprint_2_21_Known_Limitations.png",
    "Sprint_2_21_Project_Completion_Summary.png",
)
REQUIRED_RELEASE_FILES = (
    "app/app-debug.apk",
    "app/APK_SHA256SUMS.txt",
    "model/final_model_manifest.json",
    "model/model_hashes.txt",
    "model/label_order.txt",
    "reports/final_release_validation_report.md",
    "reports/final_test_summary.md",
    "reports/privacy_offline_audit.md",
    "reports/known_limitations.md",
    "reports/final_project_status.md",
    "documentation/installation_guide.md",
    "documentation/demonstration_guide.md",
    "documentation/user_workflow_guide.md",
    "documentation/developer_handover.md",
    "documentation/evidence_index.md",
    "manifests/release_manifest.json",
    "manifests/environment_manifest.json",
    "manifests/artifact_inventory.csv",
    "manifests/protected_hashes.json",
    "manifests/SHA256SUMS.txt",
    "evidence/release_evidence_index.md",
    "SignSync_RC1_Source.zip",
    "SignSync_RC1_Evidence.zip",
)


class ReleaseValidationError(RuntimeError):
    """Raised when a frozen release requirement is not satisfied."""


def sha256_file(path: Path) -> str:
    """Return an uppercase SHA-256 digest without loading the whole file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseValidationError(message)


def validate_protected_artifacts() -> dict[str, str]:
    """Verify every immutable artifact before any other release claim."""
    actual: dict[str, str] = {}
    for name, (path, expected) in PROTECTED_ARTIFACTS.items():
        require(path.is_file(), f"Missing protected artifact: {path}")
        digest = sha256_file(path)
        require(digest == expected, f"Protected hash mismatch for {name}: {digest}")
        actual[name] = digest

    deployed = ROOT / "flutter_app" / "assets" / "models"
    for filename, key in (
        ("signsync_40class_account_corrected_v2_float32.tflite", "float32_tflite"),
        (
            "signsync_40class_account_corrected_v2_dynamic_range.tflite",
            "dynamic_range_tflite",
        ),
    ):
        require(
            sha256_file(deployed / filename) == actual[key],
            f"Deployed Flutter model differs from protected {key} model.",
        )
    return actual


def validate_dataset() -> Counter[str]:
    """Verify the corrected active phone dataset without modifying a sample."""
    paths = sorted(PHONE_SAMPLES.glob("*.json"))
    require(len(paths) == 1000, f"Expected 1000 active samples, found {len(paths)}.")
    counts: Counter[str] = Counter()
    sample_ids: set[str] = set()
    for path in paths:
        record = read_json(path)
        label = record.get("label")
        sample_id = record.get("sample_id")
        require(label in FINAL_LABELS, f"Forbidden active label in {path.name}: {label}")
        require(label not in REMOVED_LABELS, f"Removed label remains active: {label}")
        require(
            not (isinstance(label, str) and len(label) == 1 and label.isalnum()),
            f"Alphabet or digit label remains active: {label}",
        )
        require(sample_id not in sample_ids, f"Duplicate active sample_id: {sample_id}")
        sample_ids.add(sample_id)
        counts[label] += 1
    require(set(counts) == set(FINAL_LABELS), "Active label membership changed.")
    require(all(counts[label] == 25 for label in FINAL_LABELS), "Expected 25 samples per label.")
    expected_account = {f"P02_PHONE_account_R{i:02d}" for i in range(1, 26)}
    actual_account = {
        read_json(path).get("sample_id")
        for path in paths
        if read_json(path).get("label") == "account"
    }
    require(actual_account == expected_account, "The final corrected account set changed.")
    return counts


def validate_query_configuration() -> tuple[int, int]:
    configuration = read_json(QUERY_PATH)
    intents = configuration.get("intents", [])
    ids = [intent.get("id") for intent in intents]
    require(ids == list(FINAL_LABELS), "Frozen query intent order changed.")
    request_count = 0
    for intent in intents:
        queries = intent.get("queries", [])
        require(len(queries) == 4, f"{intent.get('id')} does not have four requests.")
        require(
            len({query.get("id") for query in queries}) == 4,
            f"{intent.get('id')} has duplicate request IDs.",
        )
        request_count += len(queries)
    require(request_count == 160, f"Expected 160 requests, found {request_count}.")
    return len(intents), request_count


def validate_model_and_metrics() -> dict[str, float | int]:
    labels = read_json(MODEL_METADATA / "labels_40.json")
    require(labels == list(FINAL_LABELS), "Final model label order changed.")
    verification = read_json(MODEL_METADATA / "tflite_verification.json")
    for contract_name in ("keras_contract", "float32_contract", "dynamic_range_contract"):
        contract = verification[contract_name]
        require(contract["input_shape"] == [1, 756], f"{contract_name} input changed.")
        require(contract["output_shape"] == [1, 40], f"{contract_name} output changed.")
        require(contract["input_dtype"] == "float32", f"{contract_name} input dtype changed.")
        require(contract["output_dtype"] == "float32", f"{contract_name} output dtype changed.")
    require(verification["keras_float32_top1_agreement"] == 1.0, "Float32 parity changed.")
    require(verification["keras_dynamic_top1_agreement"] == 1.0, "Dynamic parity changed.")

    metrics = read_json(MODEL_METRICS / "final_test_metrics.json")
    expected = {
        "test_samples": 200,
        "label_count": 40,
        "accuracy": 0.955,
        "macro_precision": 0.9625,
        "macro_recall": 0.955,
        "macro_f1": 0.9541666666666666,
        "weighted_f1": 0.9541666666666666,
        "accepted_samples": 195,
        "rejected_samples": 5,
        "coverage": 0.975,
        "accepted_accuracy": 0.9794871794871794,
    }
    for key, value in expected.items():
        actual = metrics.get(key)
        if isinstance(value, float):
            require(abs(float(actual) - value) < 1e-12, f"Metric changed: {key}={actual}")
        else:
            require(actual == value, f"Metric changed: {key}={actual}")

    with (MODEL_METRICS / "final_test_predictions.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 200, "Final corrected prediction count changed.")
    correct = sum(row["correct"].lower() == "true" for row in rows)
    require(correct == 191, f"Expected 191 correct predictions, found {correct}.")
    account_savings = sum(
        (row["actual_label"], row["predicted_label"])
        in {("account", "savings"), ("savings", "account")}
        for row in rows
    )
    require(account_savings == 0, "Direct account/savings confusion reappeared.")
    return {**expected, "correct_predictions": correct, "incorrect_predictions": 9}


def validate_release_source_configuration() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for filename in (
        "signsync_40class_account_corrected_v2_float32.tflite",
        "signsync_40class_account_corrected_v2_dynamic_range.tflite",
    ):
        require(
            f"!flutter_app/assets/models/{filename}" in gitignore,
            f"Final deployed model remains ignored: {filename}",
        )

    manifest = (
        ROOT / "flutter_app" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    ).read_text(encoding="utf-8")
    require('android:name="android.permission.CAMERA"' in manifest, "Camera permission missing.")
    for permission in (
        "INTERNET",
        "ACCESS_NETWORK_STATE",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE",
        "READ_PHONE_STATE",
    ):
        marker = f'android:name="android.permission.{permission}" tools:node="remove"'
        require(marker in manifest, f"Missing removal marker for {permission}.")

    gradle = (ROOT / "flutter_app" / "android" / "app" / "build.gradle.kts").read_text(
        encoding="utf-8"
    )
    require('applicationId = "com.example.flutter_app"' in gradle, "Android package changed.")
    ios_project = (
        ROOT / "flutter_app" / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    ).read_text(encoding="utf-8")
    require(
        "PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;" in ios_project,
        "iOS bundle identifier changed.",
    )
    app_config = (ROOT / "flutter_app" / "lib" / "config" / "app_config.dart").read_text(
        encoding="utf-8"
    )
    require("bankingIntentConfidenceThreshold = 0.80" in app_config, "Threshold changed.")
    require("minimumTop2Gap = 0.00" in app_config, "Minimum margin changed.")

    merged_release = (
        ROOT
        / "flutter_app"
        / "build"
        / "app"
        / "intermediates"
        / "merged_manifests"
        / "release"
        / "processReleaseManifest"
        / "AndroidManifest.xml"
    )
    if merged_release.is_file():
        packaged = merged_release.read_text(encoding="utf-8")
        require("android.permission.CAMERA" in packaged, "Release APK lost camera access.")
        for permission in (
            "android.permission.INTERNET",
            "android.permission.ACCESS_NETWORK_STATE",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.READ_PHONE_STATE",
        ):
            require(permission not in packaged, f"Release manifest retains {permission}.")


def _validate_zip(path: Path, required: tuple[str, ...], forbidden_parts: tuple[str, ...]) -> int:
    require(path.is_file(), f"Missing archive: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(names, f"Archive is empty: {path.name}")
        for name in names:
            pure = PurePosixPath(name)
            require(not pure.is_absolute() and ".." not in pure.parts, f"Unsafe ZIP path: {name}")
            lowered = name.lower()
            require(
                not any(part in lowered for part in forbidden_parts),
                f"Forbidden archive content in {path.name}: {name}",
            )
        for expected in required:
            require(expected in names, f"{path.name} is missing {expected}")
        bad = archive.testzip()
        require(bad is None, f"ZIP CRC validation failed for {bad}")
    return len(names)


def validate_release_package() -> dict[str, Any]:
    for relative in REQUIRED_DOCS:
        require((ROOT / relative).is_file(), f"Missing final document: {relative}")
    figure_root = ROOT / "docs" / "phase_2_evidence" / "screenshots" / "Sprint2.21"
    for name in FIGURE_NAMES:
        path = figure_root / name
        require(path.is_file() and path.stat().st_size > 1000, f"Missing evidence figure: {name}")
    for relative in REQUIRED_RELEASE_FILES:
        require((RELEASE_ROOT / relative).is_file(), f"Missing release file: {relative}")

    source_entries = _validate_zip(
        RELEASE_ROOT / "SignSync_RC1_Source.zip",
        (
            "flutter_app/lib/main.dart",
            "flutter_app/pubspec.yaml",
            "ml/src/validate_sprint_2_21_release_candidate.py",
            "ml/models/sprint_2_17_final_40class_account_corrected_v2/models/signsync_40class_account_corrected_v2_dynamic_range.tflite",
            "docs/final/SignSync_developer_handover.md",
        ),
        ("/.git/", "/build/", "/.dart_tool/", "/.venv", "data_raw/videos", "landmark_samples/"),
    )
    evidence_entries = _validate_zip(
        RELEASE_ROOT / "SignSync_RC1_Evidence.zip",
        (
            "docs/phase_2_evidence/screenshots/Sprint2.21/Sprint_2_21_Final_Release_Status.png",
            "ml/models/sprint_2_17_final_40class_account_corrected_v2/figures/confusion_matrix.png",
            "docs/phase_2_evidence/sprint_2_21_release_validation.md",
        ),
        ("/.git/", "/build/", "/.dart_tool/", "/.venv", "data_raw/videos", "landmark_samples/"),
    )

    sums_path = RELEASE_ROOT / "manifests" / "SHA256SUMS.txt"
    sum_rows = [line.split("  ", 1) for line in sums_path.read_text(encoding="ascii").splitlines() if line]
    for expected_hash, relative in sum_rows:
        path = RELEASE_ROOT / PurePosixPath(relative)
        require(path.is_file(), f"Checksum references missing file: {relative}")
        require(sha256_file(path) == expected_hash, f"Checksum mismatch: {relative}")

    manifest = read_json(RELEASE_ROOT / "manifests" / "release_manifest.json")
    require(manifest.get("status") == "PASS", "Release manifest status is not PASS.")
    require(manifest.get("release_candidate") == "SignSync_RC1", "Release identity changed.")
    require(manifest.get("package_id") == "com.example.flutter_app", "Manifest package ID changed.")
    require(manifest.get("version_name") == "1.0.0", "Manifest version name changed.")
    require(manifest.get("version_code") == 1, "Manifest version code changed.")
    require(manifest.get("source_archive", {}).get("sha256") == sha256_file(RELEASE_ROOT / "SignSync_RC1_Source.zip"), "Source archive hash mismatch in manifest.")
    require(
        manifest.get("evidence_archive", {}).get("hash_location")
        == "manifests/SHA256SUMS.txt",
        "Evidence archive must use the external checksum manifest to avoid self-reference.",
    )
    expected_evidence_hash = next(
        (digest for digest, relative in sum_rows if relative == "SignSync_RC1_Evidence.zip"),
        None,
    )
    require(
        expected_evidence_hash
        == sha256_file(RELEASE_ROOT / "SignSync_RC1_Evidence.zip"),
        "Evidence archive hash mismatch in checksum manifest.",
    )
    return {
        "source_archive_entries": source_entries,
        "evidence_archive_entries": evidence_entries,
        "checksum_entries": len(sum_rows),
    }


def validate_all(include_release: bool = True) -> dict[str, Any]:
    results: dict[str, Any] = {
        "protected_hashes": validate_protected_artifacts(),
        "dataset_distribution": dict(validate_dataset()),
        "query": validate_query_configuration(),
        "model_and_metrics": validate_model_and_metrics(),
    }
    validate_release_source_configuration()
    results["source_configuration"] = "PASS"
    if include_release:
        results["release_package"] = validate_release_package()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Validate protected core artifacts before release packaging.",
    )
    args = parser.parse_args()
    try:
        results = validate_all(include_release=not args.core_only)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ReleaseValidationError) as error:
        print(f"FAIL: Sprint 2.21 release validation failed: {error}", file=sys.stderr)
        return 1

    print("Sprint 2.21 Release Candidate Validation")
    print("----------------------------------------")
    print("PASS: protected model, dataset, backup, deployment, and query hashes")
    print("PASS: 1,000 active samples; 40 labels; 25 samples per label")
    print("PASS: model contract [1,756] -> [1,40]; threshold 0.80; margin 0.00")
    print("PASS: 200 locked predictions; 191 correct; account/savings confusion 0")
    print("PASS: final model assets are source-distributable and permissions are constrained")
    if not args.core_only:
        package = results["release_package"]
        print(
            "PASS: release package, checksums, documents, figures, and archives "
            f"({package['source_archive_entries']} source entries; "
            f"{package['evidence_archive_entries']} evidence entries)"
        )
    print("PASS: Sprint 2.21 release candidate validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

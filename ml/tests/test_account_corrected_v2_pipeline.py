"""Acceptance checks for the corrected-account 40-class pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHONE = ROOT / "ml" / "data_phone"
ACTIVE = PHONE / "landmark_samples"
CORRECTION = PHONE / "corrections" / "account_20260719"
INVALID_ACCOUNT = PHONE / "invalidated" / "account_incorrect_gesture_20260719"
DERIVED = PHONE / "sprint_2_17_40class_account_corrected_v2"
CANDIDATE = ROOT / "ml" / "models" / "sprint_2_17_final_40class_account_corrected_v2"
OLD_CANDIDATE = ROOT / "ml" / "models" / "sprint_2_17_final_40class"
FLUTTER = ROOT / "flutter_app"
FLUTTER_MODELS = FLUTTER / "assets" / "models"

FINAL_LABELS = [
    "deposit", "withdraw", "balance", "transfer", "account", "card", "pin",
    "password", "identity_verification", "cash", "payment", "fee", "loan",
    "savings", "open_account", "close_account", "fraud", "block_card", "help",
    "confirm", "statement", "document", "bill_payment", "atm", "branch",
    "cheque", "interest_rate", "credit_card", "debit_card", "lost_card",
    "replace_card", "change_pin", "reset_password", "refund", "signature",
    "complaint", "appointment", "account_number", "card_limit", "daily_limit",
]
OLD_BACKUP_SHA256 = (
    "f3f76c6bbe06305c7ae82e2772c5daca7f76619444f7eca892d7aa253986b70b"
)
CORRECTED_BACKUP_SHA256 = (
    "07b5660e08640ea2eac11216e41f4696d01be52627cf3e1dd15d46f99c20286a"
)
COLLECTION_PAGE_SHA256 = (
    "cdc0d7355ac0ec3ccc9ec9b88def8d88898bd1c2b1e9c0cfbd46da6308604fc9"
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


class CorrectedAccountV2AcceptanceTests(unittest.TestCase):
    """Protect dataset, model, deployment, and repository contracts."""

    def test_01_exactly_25_corrected_account_samples_exist(self):
        files = sorted(ACTIVE.glob("P02_PHONE_account_R*.json"))
        self.assertEqual(len(files), 25)
        self.assertEqual({_json(path)["label"] for path in files}, {"account"})

    def test_02_old_account_samples_are_absent_from_active_dataset(self):
        active_hashes = {_sha256(path) for path in ACTIVE.glob("*account_R*.json")}
        invalid_hashes = {_sha256(path) for path in INVALID_ACCOUNT.glob("*.json")}
        self.assertTrue(invalid_hashes)
        self.assertTrue(active_hashes.isdisjoint(invalid_hashes))

    def test_03_old_account_archive_contains_25_samples(self):
        self.assertEqual(len(list(INVALID_ACCOUNT.glob("*.json"))), 25)
        self.assertTrue((INVALID_ACCOUNT / "README.md").is_file())
        self.assertTrue((INVALID_ACCOUNT / "SHA256SUMS.txt").is_file())

    def test_04_exactly_25_savings_samples_are_unchanged(self):
        previous = _csv(
            PHONE / "sprint_2_17_40class" / "checksums" / "phone_source_json_sha256.csv"
        )
        rows = [row for row in previous if row["label"] == "savings"]
        self.assertEqual(len(rows), 25)
        self.assertTrue(all(_sha256(ROOT / row["source_path"]) == row["file_sha256"] for row in rows))

    def test_05_account_and_savings_have_no_exact_sequence_duplicates(self):
        rows = _csv(CORRECTION / "corrected_phone_source_json_sha256.csv")
        account = {row["sequence_sha256"] for row in rows if row["label"] == "account"}
        savings = {row["sequence_sha256"] for row in rows if row["label"] == "savings"}
        self.assertTrue(account.isdisjoint(savings))

    def test_06_exactly_975_non_account_hashes_are_unchanged(self):
        rows = _csv(CORRECTION / "non_account_975_integrity_comparison.csv")
        self.assertEqual(len(rows), 975)
        self.assertTrue(all(row["unchanged"] == "True" for row in rows))

    def test_07_corrected_dataset_count_is_1000(self):
        self.assertEqual(len(list(ACTIVE.glob("*.json"))), 1000)

    def test_08_every_label_has_25_samples(self):
        counts = Counter(_json(path)["label"] for path in ACTIVE.glob("*.json"))
        self.assertEqual(counts, Counter({label: 25 for label in FINAL_LABELS}))

    def test_09_corrected_split_is_600_200_200(self):
        counts = {
            name: len(_csv(CANDIDATE / "manifests" / f"phone_{name}_manifest.csv"))
            for name in ("train", "validation", "test")
        }
        self.assertEqual(counts, {"train": 600, "validation": 200, "test": 200})

    def test_10_account_split_is_15_5_5(self):
        counts = {}
        for name in ("train", "validation", "test"):
            rows = _csv(CANDIDATE / "manifests" / f"phone_{name}_manifest.csv")
            counts[name] = sum(row["label"] == "account" for row in rows)
        self.assertEqual(counts, {"train": 15, "validation": 5, "test": 5})

    def test_11_no_old_account_file_appears_in_any_split(self):
        old_hashes = {_sha256(path) for path in INVALID_ACCOUNT.glob("*.json")}
        split_hashes = set()
        for name in ("train", "validation", "test"):
            split_hashes.update(
                row["source_file_hash"]
                for row in _csv(CANDIDATE / "manifests" / f"phone_{name}_manifest.csv")
            )
        self.assertTrue(old_hashes.isdisjoint(split_hashes))

    def test_12_model_output_remains_40(self):
        verification = _json(CANDIDATE / "metadata" / "tflite_verification.json")
        self.assertEqual(verification["float32_contract"]["output_shape"], [1, 40])
        self.assertEqual(verification["dynamic_range_contract"]["output_shape"], [1, 40])

    def test_13_account_index_remains_4(self):
        self.assertEqual(FINAL_LABELS.index("account"), 4)

    def test_14_savings_index_remains_13(self):
        self.assertEqual(FINAL_LABELS.index("savings"), 13)

    def test_15_exact_frozen_label_order_remains(self):
        self.assertEqual(_json(CANDIDATE / "metadata" / "labels_40.json"), FINAL_LABELS)
        self.assertEqual(_json(FLUTTER_MODELS / "labels_40.json"), FINAL_LABELS)

    def test_16_query_mapping_remains_exact(self):
        query = _json(FLUTTER / "assets" / "content" / "banking_queries.json")
        self.assertEqual([item["id"] for item in query["intents"]], FINAL_LABELS)
        self.assertEqual(sum(len(item["queries"]) for item in query["intents"]), 160)

    def test_17_corrected_source_and_flutter_model_hashes_match(self):
        pairs = [
            (
                CANDIDATE / "models" / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
                FLUTTER_MODELS / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
            ),
            (
                CANDIDATE / "models" / "signsync_40class_account_corrected_v2_float32.tflite",
                FLUTTER_MODELS / "signsync_40class_account_corrected_v2_float32.tflite",
            ),
        ]
        self.assertTrue(all(_sha256(source) == _sha256(deployed) for source, deployed in pairs))

    def test_18_corrected_backup_validates_after_extraction(self):
        backup = PHONE / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
        self.assertEqual(_sha256(backup), CORRECTED_BACKUP_SHA256)
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(backup) as archive:
                archive.extractall(temp)
            files = list(Path(temp).rglob("*.json"))
            self.assertEqual(len(files), 1000)

    def test_19_old_invalid_backup_is_archived(self):
        backup = (
            PHONE / "invalidated_backups" /
            "sprint_2_16B_banking_phone_samples_1000_backup_incorrect_account_20260719.zip"
        )
        self.assertEqual(_sha256(backup), OLD_BACKUP_SHA256)

    def test_20_old_model_package_is_marked_superseded(self):
        record = _json(ROOT / "ml" / "models" / "sprint_2_17_final_40class_SUPERSEDED.json")
        self.assertEqual(record["old_package_path"], "ml/models/sprint_2_17_final_40class")
        self.assertIn("INCORRECT ACCOUNT", record["status"])
        self.assertTrue(OLD_CANDIDATE.is_dir())

    def test_21_corrected_keras_tflite_parity_passes(self):
        parity = _json(CANDIDATE / "metadata" / "tflite_verification.json")
        self.assertEqual(parity["status"], "PASS")
        self.assertEqual(parity["keras_float32_top1_agreement"], 1.0)

    def test_22_account_savings_evaluation_files_exist(self):
        required = [
            CANDIDATE / "metrics" / "account_savings_test_predictions.csv",
            CANDIDATE / "metrics" / "account_savings_validation_predictions.csv",
            CANDIDATE / "metrics" / "account_savings_analysis.json",
            CANDIDATE / "reports" / "account_vs_savings_analysis.md",
        ]
        self.assertTrue(all(path.is_file() for path in required))

    def test_23_flutter_workflow_tests_remain_present(self):
        required = [
            "banking_interaction_workflow_test.dart",
            "manual_details_step_test.dart",
            "banking_workflow_privacy_test.dart",
            "phone_dataset_collection_page_test.dart",
            "theme_preference_test.dart",
        ]
        self.assertTrue(all((FLUTTER / "test" / name).is_file() for name in required))

    def test_24_dataset_collection_code_remains_unchanged(self):
        page = FLUTTER / "lib" / "ui" / "phone_dataset_collection_page.dart"
        self.assertEqual(_sha256(page), COLLECTION_PAGE_SHA256)

    def test_25_package_identifiers_remain_unchanged(self):
        gradle = (FLUTTER / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
        ios = (FLUTTER / "ios" / "Runner.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
        self.assertIn('namespace = "com.example.flutter_app"', gradle)
        self.assertIn('applicationId = "com.example.flutter_app"', gradle)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;", ios)


if __name__ == "__main__":
    unittest.main()

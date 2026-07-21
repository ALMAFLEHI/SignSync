"""Automated integrity tests for the completed Sprint 2.17 candidate pipeline."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from labels import ALPHABET_LABELS, DIGIT_LABELS  # noqa: E402
from sprint_2_16A_experiment_utils import (  # noqa: E402
    augment_sequence,
    load_augmentation_config,
    stable_rng,
    statistical_features,
)
from sprint_2_17_config import (  # noqa: E402
    CANDIDATE_ROOT,
    EXPECTED_FLUTTER_DYNAMIC_SHA256,
    EXPECTED_FLUTTER_FLOAT32_SHA256,
    EXPECTED_PHONE_BACKUP_SHA256,
    FINAL_LABELS,
    FLUTTER_DYNAMIC_MODEL,
    FLUTTER_FLOAT32_MODEL,
    HISTORICAL_TRAIN_FEATURES,
    MANIFEST_DIR,
    METADATA_DIR,
    MODEL_DIR,
    PHONE_AUGMENTED_FEATURES,
    PHONE_BACKUP_PATH,
    PHONE_SAMPLE_DIR,
    PHONE_TEST_FEATURES,
    PHONE_TRAIN_FEATURES,
    PHONE_VALIDATION_FEATURES,
    PILOT_LABELS,
    PILOT_MANIFEST_PATH,
    QUERY_CONFIG_PATH,
    REMOVED_LABELS,
)
from sprint_2_17_utils import read_csv, sha256_file  # noqa: E402


EXPECTED_LABELS = [
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


class Sprint217PipelineTests(unittest.TestCase):
    """Protect every acceptance-critical label, data, split, and model contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_report = _read_json(
            ROOT
            / "ml"
            / "data_phone"
            / "sprint_2_17_40class"
            / "reports"
            / "raw_dataset_validation.json"
        )
        cls.train_rows = read_csv(MANIFEST_DIR / "phone_train_manifest.csv")
        cls.validation_rows = read_csv(
            MANIFEST_DIR / "phone_validation_manifest.csv"
        )
        cls.test_rows = read_csv(MANIFEST_DIR / "phone_test_manifest.csv")
        cls.all_rows = cls.train_rows + cls.validation_rows + cls.test_rows
        cls.tflite = _read_json(METADATA_DIR / "tflite_verification.json")
        cls.model_metadata = _read_json(METADATA_DIR / "model_metadata.json")

    def test_01_frozen_label_count_is_40(self) -> None:
        self.assertEqual(len(FINAL_LABELS), 40)
        self.assertEqual(len(set(FINAL_LABELS)), 40)

    def test_02_frozen_label_order_is_exact(self) -> None:
        self.assertEqual(FINAL_LABELS, EXPECTED_LABELS)

    def test_03_no_alphabet_labels_exist(self) -> None:
        self.assertFalse(set(FINAL_LABELS).intersection(ALPHABET_LABELS))

    def test_04_no_digit_labels_exist(self) -> None:
        self.assertFalse(set(FINAL_LABELS).intersection(DIGIT_LABELS))

    def test_05_no_removed_labels_exist(self) -> None:
        self.assertFalse(set(FINAL_LABELS).intersection(REMOVED_LABELS))

    def test_06_dataset_count_is_1000(self) -> None:
        self.assertEqual(self.raw_report["status"], "PASS")
        self.assertEqual(self.raw_report["valid_samples"], 1000)

    def test_07_every_label_has_25_phone_samples(self) -> None:
        self.assertEqual(
            self.raw_report["per_label_counts"], {label: 25 for label in FINAL_LABELS}
        )

    def test_08_every_source_sequence_is_60_by_126(self) -> None:
        paths = sorted(PHONE_SAMPLE_DIR.rglob("*.json"))
        self.assertEqual(len(paths), 1000)
        for path in paths:
            payload = _read_json(path)
            frames = payload["frames"]
            self.assertEqual(len(frames), 60, path.name)
            self.assertTrue(all(len(frame) == 126 for frame in frames), path.name)

    def test_09_feature_matrices_have_width_756(self) -> None:
        expectations = {
            PHONE_TRAIN_FEATURES: 600,
            PHONE_VALIDATION_FEATURES: 200,
            PHONE_TEST_FEATURES: 200,
            PHONE_AUGMENTED_FEATURES: 600,
            HISTORICAL_TRAIN_FEATURES: 260,
        }
        for path, rows in expectations.items():
            with np.load(path, allow_pickle=False) as data:
                self.assertEqual(data["X"].shape, (rows, 756), path.name)

    def test_10_feature_order_matches_canonical_contract(self) -> None:
        sequence = np.arange(60 * 126, dtype=np.float32).reshape(60, 126) / 1000
        expected = np.concatenate(
            [
                np.mean(sequence, axis=0),
                np.std(sequence, axis=0, ddof=0),
                np.min(sequence, axis=0),
                np.max(sequence, axis=0),
                sequence[0],
                sequence[-1],
            ]
        ).astype(np.float32)
        actual = statistical_features(sequence)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-6)

    def test_11_population_standard_deviation_is_used(self) -> None:
        sequence = np.tile(np.arange(60, dtype=np.float32)[:, None], (1, 126))
        features = statistical_features(sequence)
        population = np.std(sequence, axis=0, ddof=0)
        sample = np.std(sequence, axis=0, ddof=1)
        np.testing.assert_allclose(features[126:252], population, rtol=0, atol=1e-6)
        self.assertFalse(np.allclose(features[126:252], sample))

    def test_12_augmentation_preserves_missing_hand_zero_blocks(self) -> None:
        sequence = np.zeros((60, 126), dtype=np.float32)
        sequence[:, 63:] = np.linspace(0.1, 0.9, 63, dtype=np.float32)
        augmented, _ = augment_sequence(
            sequence,
            stable_rng(42, "zero-slot-test"),
            load_augmentation_config(),
        )
        np.testing.assert_array_equal(augmented[:, :63], np.zeros((60, 63)))

    def test_13_raw_source_hashes_remain_unchanged(self) -> None:
        rows = read_csv(
            ROOT
            / "ml"
            / "data_phone"
            / "sprint_2_17_40class"
            / "checksums"
            / "phone_source_json_sha256.csv"
        )
        self.assertEqual(len(rows), 1000)
        for row in rows:
            self.assertEqual(sha256_file(ROOT / row["source_path"]), row["file_sha256"])

    def test_14_split_counts_are_600_200_200(self) -> None:
        self.assertEqual(
            (len(self.train_rows), len(self.validation_rows), len(self.test_rows)),
            (600, 200, 200),
        )

    def test_15_every_label_has_15_5_5_split(self) -> None:
        for rows, expected in (
            (self.train_rows, 15),
            (self.validation_rows, 5),
            (self.test_rows, 5),
        ):
            self.assertEqual(Counter(row["label"] for row in rows), Counter({label: expected for label in FINAL_LABELS}))

    def test_16_no_source_sample_appears_in_multiple_splits(self) -> None:
        sample_ids = [row["sample_id"] for row in self.all_rows]
        self.assertEqual(len(sample_ids), 1000)
        self.assertEqual(len(set(sample_ids)), 1000)

    def test_17_augmented_samples_exist_only_in_training(self) -> None:
        rows = read_csv(
            ROOT
            / "ml"
            / "data_phone"
            / "sprint_2_17_40class"
            / "augmentation"
            / "phone_train_augmentation_manifest.csv"
        )
        self.assertEqual(len(rows), 600)
        self.assertEqual({row["split"] for row in rows}, {"train"})
        self.assertTrue(all(row["sample_id"].endswith("__aug01") for row in rows))

    def test_18_pilot_split_assignments_are_preserved(self) -> None:
        prior = {
            row["sample_id"]: (
                "validation" if row["split"] == "val" else row["split"]
            )
            for row in read_csv(PILOT_MANIFEST_PATH)
            if row["label"] in PILOT_LABELS and row["augmentation_status"] == "original"
        }
        current = {
            row["sample_id"]: row["split"]
            for row in self.all_rows
            if row["label"] in PILOT_LABELS
        }
        self.assertEqual(len(prior), 100)
        self.assertEqual(current, prior)

    def test_19_historical_excluded_labels_are_not_in_training_features(self) -> None:
        with np.load(HISTORICAL_TRAIN_FEATURES, allow_pickle=False) as data:
            labels = set(data["labels"].astype(str))
        self.assertTrue(labels.issubset(FINAL_LABELS))
        self.assertFalse(labels.intersection(ALPHABET_LABELS + DIGIT_LABELS + REMOVED_LABELS))
        report = _read_json(
            ROOT
            / "ml"
            / "data_phone"
            / "sprint_2_17_40class"
            / "reports"
            / "historical_dataset_inspection.json"
        )
        self.assertEqual(report["alphabet_samples"], 245)
        self.assertEqual(report["digit_samples"], 85)
        self.assertEqual(report["removed_label_samples"], 100)

    def test_20_validation_and_test_are_never_augmented(self) -> None:
        for path in (PHONE_VALIDATION_FEATURES, PHONE_TEST_FEATURES):
            with np.load(path, allow_pickle=False) as data:
                self.assertNotIn("source_sample_ids", data.files)
                self.assertTrue(
                    all("__aug" not in value for value in data["sample_ids"].astype(str))
                )

    def test_21_keras_model_output_is_40(self) -> None:
        import tensorflow as tf

        model = tf.keras.models.load_model(MODEL_DIR / "signsync_40class_final.keras")
        self.assertEqual(model.input_shape, (None, 756))
        self.assertEqual(model.output_shape, (None, 40))

    def test_22_label_metadata_count_and_order_are_exact(self) -> None:
        labels = _read_json(METADATA_DIR / "labels_40.json")
        self.assertEqual(labels, FINAL_LABELS)

    def test_23_model_labels_match_query_intent_ids(self) -> None:
        query = _read_json(QUERY_CONFIG_PATH)
        query_ids = [intent["id"] for intent in query["intents"]]
        self.assertEqual(query_ids, FINAL_LABELS)
        self.assertEqual(sum(len(intent["queries"]) for intent in query["intents"]), 160)

    def test_24_float32_tflite_contract_is_exact(self) -> None:
        contract = self.tflite["float32_contract"]
        self.assertEqual(contract["input_shape"], [1, 756])
        self.assertEqual(contract["output_shape"], [1, 40])
        self.assertEqual(contract["input_dtype"], "float32")
        self.assertEqual(contract["output_dtype"], "float32")

    def test_25_dynamic_tflite_contract_is_exact(self) -> None:
        contract = self.tflite["dynamic_range_contract"]
        self.assertEqual(contract["input_shape"], [1, 756])
        self.assertEqual(contract["output_shape"], [1, 40])
        self.assertEqual(contract["input_dtype"], "float32")
        self.assertEqual(contract["output_dtype"], "float32")

    def test_26_keras_tflite_top1_parity_passed(self) -> None:
        self.assertEqual(self.tflite["parity_samples"], 40)
        self.assertEqual(self.tflite["keras_float32_top1_agreement"], 1.0)
        self.assertEqual(self.tflite["keras_dynamic_top1_agreement"], 1.0)

    def test_27_model_artifact_hashes_are_recorded_and_current(self) -> None:
        paths = {
            "keras": MODEL_DIR / "signsync_40class_final.keras",
            "float32_tflite": MODEL_DIR / "signsync_40class_float32.tflite",
            "dynamic_range_tflite": MODEL_DIR / "signsync_40class_dynamic_range.tflite",
        }
        for key, path in paths.items():
            self.assertEqual(sha256_file(path), self.model_metadata["model_sha256"][key])
        checksum_lines = (METADATA_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertIn("models/signsync_40class_final.keras", checksum_lines)

    def test_28_current_flutter_models_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(FLUTTER_DYNAMIC_MODEL), EXPECTED_FLUTTER_DYNAMIC_SHA256.lower()
        )
        self.assertEqual(
            sha256_file(FLUTTER_FLOAT32_MODEL), EXPECTED_FLUTTER_FLOAT32_SHA256.lower()
        )

    def test_29_dataset_backup_hash_remains_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(PHONE_BACKUP_PATH), EXPECTED_PHONE_BACKUP_SHA256.lower()
        )

    def test_30_raw_phone_sample_count_remains_1000(self) -> None:
        self.assertEqual(len(list(PHONE_SAMPLE_DIR.rglob("*.json"))), 1000)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

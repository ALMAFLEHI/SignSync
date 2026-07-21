"""Acceptance tests for the revised Sprint 2.19 offline consolidation."""

from __future__ import annotations

import csv
import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from finalize_sprint_2_19_offline_evaluation import (  # noqa: E402
    A55_SCREENSHOTS,
    A55_SCREENSHOT_DIR,
    CONFIDENCE_THRESHOLD,
    CONFUSION_DIR,
    EVIDENCE_DIR,
    EXPECTED_HASHES,
    FIGURES_DIR,
    FINAL_LABELS,
    METADATA_DIR,
    METRICS_DIR,
    MODEL_PATHS,
    PREDICTIONS_PATH,
    REPORT_ROOT,
    SOURCE_DIR,
    account_savings_metrics,
    classification_metrics,
    confidence_metrics,
    confusion_matrix,
    load_predictions,
    sha256_file,
    validate_predictions,
    verify_integrity,
)


class Sprint219OfflineConsolidationTests(unittest.TestCase):
    """Protect the revised evidence design and final corrected results."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_predictions()
        cls.validation = validate_predictions(cls.rows)
        cls.matrix = confusion_matrix(cls.rows)
        cls.overall, cls.per_class = classification_metrics(cls.rows, cls.matrix)
        cls.confidence, cls.rejection = confidence_metrics(cls.rows)
        cls.account_savings = account_savings_metrics(cls.rows, cls.per_class)
        cls.integrity = verify_integrity()

    def test_01_prediction_file_contains_200_rows(self) -> None:
        self.assertEqual(len(self.rows), 200)

    def test_02_exactly_40_classes_exist(self) -> None:
        self.assertEqual(set(row["actual_label"] for row in self.rows), set(FINAL_LABELS))
        self.assertEqual(len(FINAL_LABELS), 40)

    def test_03_each_class_has_five_samples(self) -> None:
        self.assertEqual(
            Counter(row["actual_label"] for row in self.rows),
            Counter({label: 5 for label in FINAL_LABELS}),
        )

    def test_04_frozen_label_order_is_exact(self) -> None:
        labels = json.loads(
            (ROOT / "flutter_app" / "assets" / "models" / "labels_40.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(labels, FINAL_LABELS)
        self.assertEqual(list(Counter(row["actual_label"] for row in self.rows)), FINAL_LABELS)

    def test_05_accuracy_recalculates_to_09550(self) -> None:
        self.assertAlmostEqual(self.overall["accuracy"], 0.9550, places=12)

    def test_06_macro_precision_recalculates_to_09625(self) -> None:
        self.assertAlmostEqual(self.overall["macro_precision"], 0.9625, places=12)

    def test_07_macro_recall_recalculates_to_09550(self) -> None:
        self.assertAlmostEqual(self.overall["macro_recall"], 0.9550, places=12)

    def test_08_macro_f1_recalculates_to_09542(self) -> None:
        self.assertAlmostEqual(self.overall["macro_f1"], 0.9541666666666666, places=12)

    def test_09_weighted_f1_recalculates_to_09542(self) -> None:
        self.assertAlmostEqual(self.overall["weighted_f1"], 0.9541666666666666, places=12)

    def test_10_account_metrics_equal_one(self) -> None:
        account = self.account_savings["account"]
        self.assertEqual((account["precision"], account["recall"], account["f1"], account["support"]), (1.0, 1.0, 1.0, 5))

    def test_11_savings_metrics_equal_one(self) -> None:
        savings = self.account_savings["savings"]
        self.assertEqual((savings["precision"], savings["recall"], savings["f1"], savings["support"]), (1.0, 1.0, 1.0, 5))

    def test_12_account_to_savings_confusion_is_zero(self) -> None:
        self.assertEqual(self.account_savings["account_to_savings"], 0)

    def test_13_savings_to_account_confusion_is_zero(self) -> None:
        self.assertEqual(self.account_savings["savings_to_account"], 0)

    def test_14_threshold_remains_frozen(self) -> None:
        self.assertEqual(CONFIDENCE_THRESHOLD, 0.80)
        self.assertEqual(self.rejection["threshold"], 0.80)

    def test_15_rejection_metrics_are_consistent(self) -> None:
        self.assertEqual(self.rejection["accepted"] + self.rejection["rejected"], 200)
        self.assertEqual(
            self.rejection["correct_and_accepted"]
            + self.rejection["incorrect_and_accepted"]
            + self.rejection["correct_but_rejected"]
            + self.rejection["incorrect_and_rejected"],
            200,
        )

    def test_16_confidence_values_are_finite(self) -> None:
        self.assertTrue(all(math.isfinite(row["confidence"]) for row in self.rows))
        self.assertTrue(all(0.0 <= row["confidence"] <= 1.0 for row in self.rows))

    def test_17_confusion_matrix_shape_is_40_by_40(self) -> None:
        self.assertEqual(len(self.matrix), 40)
        self.assertTrue(all(len(row) == 40 for row in self.matrix))

    def test_18_all_figure_and_source_files_exist(self) -> None:
        figures = {
            "confusion_matrix.png",
            "confusion_matrix_normalized.png",
            "per_class_recall.png",
            "per_class_f1.png",
            "confidence_distribution.png",
            "rejection_summary.png",
            "account_vs_savings.png",
            "weak_class_comparison.png",
            "offline_metric_summary.png",
        }
        self.assertTrue(all((FIGURES_DIR / name).is_file() for name in figures))
        self.assertTrue((SOURCE_DIR / "corrected_test_predictions.csv").is_file())

    def test_19_corrected_model_hashes_match(self) -> None:
        for role in ("keras", "float32_tflite", "dynamic_range_tflite", "deployment_manifest"):
            self.assertEqual(sha256_file(MODEL_PATHS[role]), EXPECTED_HASHES[role])

    def test_20_corrected_dataset_count_remains_1000(self) -> None:
        self.assertEqual(self.integrity["active_dataset_samples"], 1000)

    def test_21_corrected_backup_hash_matches(self) -> None:
        self.assertEqual(sha256_file(MODEL_PATHS["corrected_backup"]), EXPECTED_HASHES["corrected_backup"])

    def test_22_previous_incorrect_results_are_superseded(self) -> None:
        record = json.loads(
            (ROOT / "ml" / "models" / "sprint_2_17_final_40class_SUPERSEDED.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(record["status"].startswith("SUPERSEDED"))

    def test_23_no_fabricated_400_trial_data_exists(self) -> None:
        for directory_name in ("raw_exports", "validated"):
            directory = REPORT_ROOT / directory_name
            result_files = [] if not directory.exists() else [
                path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in {".csv", ".json"}
            ]
            self.assertEqual(result_files, [])
        design = json.loads((METADATA_DIR / "evaluation_design.json").read_text(encoding="utf-8"))
        self.assertEqual(design["optional_400_trial_protocol"], "PREPARED BUT NOT EXECUTED - OPTIONAL FUTURE WORK")

    def test_24_a55_evidence_is_labelled_smoke_test_only(self) -> None:
        report = (EVIDENCE_DIR / "sprint_2_19_a55_smoke_test_summary.md").read_text(encoding="utf-8").lower()
        self.assertIn("smoke", report)
        self.assertIn("not a formal live-device", report)
        self.assertTrue(all((A55_SCREENSHOT_DIR / name).is_file() for name in A55_SCREENSHOTS))

    def test_25_no_customer_banking_data_is_included(self) -> None:
        design = json.loads((METADATA_DIR / "evaluation_design.json").read_text(encoding="utf-8"))
        self.assertFalse(design["privacy"]["customer_banking_data_in_evaluation"])
        with PREDICTIONS_PATH.open(newline="", encoding="utf-8") as source:
            columns = set(csv.DictReader(source).fieldnames or [])
        forbidden = {"customer_name", "account_value", "banking_detail", "raw_landmarks", "video"}
        self.assertFalse(columns.intersection(forbidden))


if __name__ == "__main__":
    unittest.main()

"""Automated preparation tests for Sprint 2.19 technical evaluation."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_sprint_2_19_live_evaluation import (  # noqa: E402
    account_savings_metrics,
    weak_class_metrics,
)
from generate_sprint_2_19_schedule import generate_schedule, write_schedule  # noqa: E402
from package_sprint_2_19_evaluation import (  # noqa: E402
    build_artifact_inventory,
    package_evaluation,
)
from sprint_2_19_config import (  # noqa: E402
    ANDROID_PACKAGE_ID,
    CONFIDENCE_THRESHOLD,
    DEPLOYMENT_MANIFEST_SHA256,
    DOC_SCHEDULE,
    DYNAMIC_MODEL_SHA256,
    FINAL_LABELS,
    LABELS_SHA256,
    MODEL_VERSION,
    PROTOCOL_VERSION,
    SCHEDULE_SHA256,
    TRIAL_COLUMNS,
    WEAK_CLASSES,
)
from sprint_2_19_evaluation import (  # noqa: E402
    EvaluationValidationError,
    classification_metrics,
    confusion_matrix,
    latency_summary,
    load_schedule,
    sha256_file,
    validate_rows,
    wilson_interval,
)
from validate_sprint_2_19_live_export import validate_export  # noqa: E402


class Sprint219EvaluationTests(unittest.TestCase):
    """Protect the formal design, validator, metrics, and packaging gates."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schedule = load_schedule(DOC_SCHEDULE)
        cls.raw_rows = _valid_raw_rows(cls.schedule)
        cls.metadata = _valid_metadata()

    def test_01_schedule_is_deterministic_and_hash_stable(self) -> None:
        self.assertEqual(generate_schedule(), generate_schedule())
        self.assertEqual(sha256_file(DOC_SCHEDULE), SCHEDULE_SHA256)

    def test_02_schedule_is_balanced(self) -> None:
        self.assertEqual(len(self.schedule), 400)
        blocks = Counter(row["block_number"] for row in self.schedule)
        self.assertEqual(blocks, Counter({block: 40 for block in range(1, 11)}))
        labels = Counter(row["intended_label"] for row in self.schedule)
        self.assertEqual(labels, Counter({label: 10 for label in FINAL_LABELS}))
        for label in FINAL_LABELS:
            conditions = Counter(
                row["condition"]
                for row in self.schedule
                if row["intended_label"] == label
            )
            self.assertEqual(conditions, Counter({"standard": 5, "mild_variation": 5}))

    def test_03_valid_export_rows_pass(self) -> None:
        rows = validate_rows(
            TRIAL_COLUMNS,
            deepcopy(self.raw_rows),
            self.schedule,
            deepcopy(self.metadata),
        )
        self.assertEqual(len(rows), 400)

    def test_04_duplicate_trial_is_rejected(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[1]["trial_number"] = "1"
        with self.assertRaisesRegex(EvaluationValidationError, "Duplicate trial"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_05_missing_trial_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvaluationValidationError, "exactly 400"):
            validate_rows(
                TRIAL_COLUMNS,
                self.raw_rows[:-1],
                self.schedule,
                self.metadata,
            )

    def test_06_incorrect_schedule_order_is_rejected(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[0]["intended_label"] = rows[1]["intended_label"]
        rows[0]["intended_label_index"] = rows[1]["intended_label_index"]
        with self.assertRaisesRegex(EvaluationValidationError, "frozen schedule"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_07_invalid_label_is_rejected(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[0]["predicted_label"] = "A"
        with self.assertRaisesRegex(EvaluationValidationError, "outside the frozen"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_08_invalid_confidence_is_rejected(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[0]["confidence"] = "1.1"
        rows[0]["confidence_margin"] = "1.05"
        with self.assertRaisesRegex(EvaluationValidationError, "between 0 and 1"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_09_threshold_logic_is_rejected_when_edited(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[0]["accepted"] = "false"
        rows[0]["rejected"] = "true"
        rows[0]["correct_and_accepted"] = "false"
        rows[0]["correct_but_rejected"] = "true"
        with self.assertRaisesRegex(EvaluationValidationError, "frozen threshold"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_10_metrics_are_exact_for_perfect_predictions(self) -> None:
        rows = validate_rows(
            TRIAL_COLUMNS, self.raw_rows, self.schedule, self.metadata
        )
        overall, per_class = classification_metrics(rows)
        self.assertEqual(overall["accuracy"], 1.0)
        self.assertEqual(overall["macro_f1"], 1.0)
        self.assertTrue(all(row["support"] == 10 for row in per_class))
        matrix = confusion_matrix(rows)
        self.assertEqual(sum(sum(row) for row in matrix), 400)
        self.assertEqual(sum(matrix[index][index] for index in range(40)), 400)

    def test_11_confusion_matrix_records_directional_error(self) -> None:
        rows = validate_rows(
            TRIAL_COLUMNS, self.raw_rows, self.schedule, self.metadata
        )
        rows = deepcopy(rows)
        account = next(row for row in rows if row["intended_label"] == "account")
        account["predicted_label"] = "savings"
        account["predicted_label_index"] = FINAL_LABELS.index("savings")
        account["correct_top1"] = False
        account["correct_and_accepted"] = False
        account["incorrect_and_accepted"] = True
        result = account_savings_metrics(rows)
        self.assertEqual(result["account_to_savings_count"], 1)
        self.assertEqual(result["savings_to_account_count"], 0)

    def test_12_wilson_interval_matches_known_result(self) -> None:
        lower, upper = wilson_interval(5, 10)
        self.assertAlmostEqual(lower, 0.2366, places=4)
        self.assertAlmostEqual(upper, 0.7634, places=4)

    def test_13_latency_percentiles_are_correct(self) -> None:
        result = latency_summary([1, 2, 3, 4, 5])
        self.assertEqual(result["mean"], 3.0)
        self.assertEqual(result["median"], 3.0)
        self.assertAlmostEqual(float(result["p95"]), 4.8)

    def test_14_weak_class_report_keeps_frozen_scope(self) -> None:
        rows = validate_rows(
            TRIAL_COLUMNS, self.raw_rows, self.schedule, self.metadata
        )
        _, per_class = classification_metrics(rows)
        weak = weak_class_metrics(rows, per_class)
        self.assertEqual([row["label"] for row in weak], WEAK_CLASSES)
        self.assertTrue(all(row["support"] == 10 for row in weak))

    def test_15_privacy_column_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvaluationValidationError, "schema changed"):
            validate_rows(
                [*TRIAL_COLUMNS, "raw_landmarks"],
                self.raw_rows,
                self.schedule,
                self.metadata,
            )

    def test_16_model_hash_is_verified(self) -> None:
        rows = deepcopy(self.raw_rows)
        rows[0]["active_model_sha256"] = "0" * 64
        with self.assertRaisesRegex(EvaluationValidationError, "model hash"):
            validate_rows(TRIAL_COLUMNS, rows, self.schedule, self.metadata)

    def test_17_file_validator_checks_export_hash_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trials = root / "live_trials.csv"
            _write_rows(trials, self.raw_rows)
            metadata = deepcopy(self.metadata)
            metadata["export_file_sha256"] = {trials.name: sha256_file(trials)}
            metadata_path = root / "session_metadata.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            output = root / "validated"
            rows = validate_export(trials, metadata_path, DOC_SCHEDULE, output)
            self.assertEqual(len(rows), 400)
            self.assertTrue((output / "validation_report.json").is_file())

    def test_18_packaging_refuses_incomplete_physical_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("prepared", encoding="utf-8")
            inventory = build_artifact_inventory(root)
            self.assertEqual(inventory[0]["path"], "README.md")
            with self.assertRaises(FileNotFoundError):
                package_evaluation(root)


def _valid_metadata() -> dict[str, object]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "session_id": "a55_formal_test",
        "trial_schedule_sha256": SCHEDULE_SHA256,
        "model_version": MODEL_VERSION,
        "model_sha256": DYNAMIC_MODEL_SHA256,
        "label_file_sha256": LABELS_SHA256,
        "deployment_manifest_sha256": DEPLOYMENT_MANIFEST_SHA256,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "device_model": "SM-A556E",
        "android_version": "16",
        "android_api_level": 36,
        "app_package_id": ANDROID_PACKAGE_ID,
        "app_version": "1.0.0",
        "build_number": "1",
        "evaluation_started_at": "2026-07-19T10:00:00Z",
        "evaluation_completed_at": "2026-07-19T12:00:00Z",
        "expected_trial_count": 400,
        "actual_valid_trial_count": 400,
        "technical_event_count": 0,
        "warm_up_trials_excluded": 5,
        "export_file_sha256": {"placeholder.csv": "0" * 64},
    }


def _valid_raw_rows(schedule: list[dict[str, object]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for scheduled in schedule:
        intended = str(scheduled["intended_label"])
        intended_index = int(scheduled["intended_label_index"])
        second_index = (intended_index + 1) % len(FINAL_LABELS)
        rows.append(
            {
                "protocol_version": PROTOCOL_VERSION,
                "session_id": "a55_formal_test",
                "trial_number": str(scheduled["trial_number"]),
                "block_number": str(scheduled["block_number"]),
                "condition": str(scheduled["condition"]),
                "intended_label": intended,
                "intended_label_index": str(intended_index),
                "predicted_label": intended,
                "predicted_label_index": str(intended_index),
                "confidence": "0.90",
                "second_label": FINAL_LABELS[second_index],
                "second_confidence": "0.05",
                "confidence_margin": "0.85",
                "accepted": "true",
                "rejected": "false",
                "correct_top1": "true",
                "correct_and_accepted": "true",
                "incorrect_and_accepted": "false",
                "correct_but_rejected": "false",
                "capture_duration_ms": "2000",
                "average_capture_fps": "30.0",
                "feature_computation_ms": "1.5",
                "tflite_inference_ms": "1.8",
                "prediction_processing_ms": "3.6",
                "model_load_ms": "12.0",
                "technical_status": "valid_inference",
                "device_model": "SM-A556E",
                "android_version": "16",
                "active_model_version": MODEL_VERSION,
                "active_model_sha256": DYNAMIC_MODEL_SHA256,
                "confidence_threshold": "0.80",
                "timestamp": "2026-07-19T10:00:00Z",
                "notes": "",
            }
        )
    return rows


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=TRIAL_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

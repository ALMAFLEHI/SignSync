"""Authoritative release checks for SignSync Sprint 2.21."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import validate_sprint_2_21_release_candidate as release  # noqa: E402


class Sprint221ReleaseCandidateTests(unittest.TestCase):
    def test_01_frozen_label_order_is_exact(self) -> None:
        self.assertEqual(len(release.FINAL_LABELS), 40)
        self.assertEqual(len(set(release.FINAL_LABELS)), 40)
        self.assertEqual(release.FINAL_LABELS[4], "account")
        self.assertEqual(release.FINAL_LABELS[13], "savings")
        self.assertEqual(release.FINAL_LABELS[-1], "daily_limit")

    def test_02_all_protected_hashes_pass(self) -> None:
        actual = release.validate_protected_artifacts()
        self.assertEqual(set(actual), set(release.PROTECTED_ARTIFACTS))

    def test_03_dataset_is_exactly_40_by_25(self) -> None:
        counts = release.validate_dataset()
        self.assertEqual(sum(counts.values()), 1000)
        self.assertTrue(all(count == 25 for count in counts.values()))

    def test_04_query_configuration_is_40_by_4(self) -> None:
        self.assertEqual(release.validate_query_configuration(), (40, 160))

    def test_05_model_contract_and_locked_metrics_pass(self) -> None:
        metrics = release.validate_model_and_metrics()
        self.assertEqual(metrics["correct_predictions"], 191)
        self.assertAlmostEqual(float(metrics["accuracy"]), 0.9550)
        self.assertAlmostEqual(float(metrics["macro_f1"]), 0.9541666666666666)

    def test_06_release_source_configuration_is_safe(self) -> None:
        release.validate_release_source_configuration()

    def test_07_hash_mismatch_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "changed.bin"
            changed.write_bytes(b"not a protected artifact")
            protected = dict(release.PROTECTED_ARTIFACTS)
            protected["keras"] = (changed, "0" * 64)
            with patch.object(release, "PROTECTED_ARTIFACTS", protected):
                with self.assertRaises(release.ReleaseValidationError):
                    release.validate_protected_artifacts()

    def test_08_release_package_is_complete(self) -> None:
        result = release.validate_release_package()
        self.assertGreater(result["source_archive_entries"], 0)
        self.assertGreater(result["evidence_archive_entries"], 0)
        self.assertGreater(result["checksum_entries"], 0)


if __name__ == "__main__":
    unittest.main()

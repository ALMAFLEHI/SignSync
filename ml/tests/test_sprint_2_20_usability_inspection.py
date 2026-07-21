"""Validation tests for the Sprint 2.20 usability inspection package."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from generate_sprint_2_20_usability_inspection import (  # noqa: E402
    ACCESSIBILITY_ROWS,
    EVIDENCE_DIR,
    FINDINGS,
    HEURISTIC_ROWS,
    MANDATORY_LIMITATION,
    METADATA_DIR,
    PRIVACY_ROWS,
    PROTECTED_HASHES,
    REPORT_ROOT,
    SCENARIOS,
    SCREENSHOT_DIR,
    SPRINT_DOC,
    TARGETS,
    WALKTHROUGH_QUESTIONS,
    WALKTHROUGH_STEPS,
    accessibility_rows,
    automated_expectations,
    cognitive_rows,
    heuristic_rows,
    integrity_report,
    privacy_rows,
    sha256_file,
    target_rows,
)


class Sprint220UsabilityInspectionTests(unittest.TestCase):
    """Protect the honest method, structured results, and evidence package."""

    def test_01_cognitive_walkthrough_answers_all_questions(self) -> None:
        rows = cognitive_rows()
        self.assertEqual(len(WALKTHROUGH_STEPS), 8)
        self.assertEqual(len(WALKTHROUGH_QUESTIONS), 8)
        self.assertEqual(len(rows), 64)
        self.assertEqual(Counter(row["status"] for row in rows), {"PASS": 64})
        for step in WALKTHROUGH_STEPS:
            self.assertEqual(
                sum(row["workflow_step"] == step["step"] for row in rows), 8
            )

    def test_02_heuristic_inspection_has_exact_principles(self) -> None:
        rows = heuristic_rows()
        self.assertEqual(len(HEURISTIC_ROWS), 12)
        self.assertEqual(len(rows), 12)
        self.assertEqual(Counter(row["status"] for row in rows), {"PASS": 10, "PARTIAL": 2})
        self.assertFalse(any(row["status"] == "FAIL" for row in rows))

    def test_03_accessibility_is_honest_about_screen_reader_limit(self) -> None:
        rows = accessibility_rows()
        self.assertEqual(len(ACCESSIBILITY_ROWS), 17)
        self.assertEqual(Counter(row["status"] for row in rows), {"PASS": 16, "PARTIAL": 1})
        screen_reader = next(row for row in rows if row["criterion"] == "Screen-reader semantics")
        self.assertIn("TalkBack", screen_reader["researcher_observation"])
        self.assertFalse(screen_reader["formal_wcag_certification"])

    def test_04_privacy_checks_all_pass(self) -> None:
        rows = privacy_rows()
        self.assertEqual(len(PRIVACY_ROWS), 7)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))
        self.assertTrue(any(row["privacy_check"] == "No video upload" for row in rows))

    def test_05_four_scenarios_use_only_declared_fake_values(self) -> None:
        self.assertEqual(len(SCENARIOS), 4)
        self.assertEqual(
            Counter(item["result"] for item in SCENARIOS),
            {"PASS": 3, "PARTIAL": 1},
        )
        account = next(item for item in SCENARIOS if item["scenario_id"] == 1)
        transfer = next(item for item in SCENARIOS if item["scenario_id"] == 2)
        self.assertEqual(account["fake_test_values"]["account_number"], "1234561864")
        self.assertEqual(transfer["fake_test_values"]["amount"], "1500")
        self.assertEqual(
            transfer["fake_test_values"]["beneficiary_account"], "1234563321"
        )

    def test_06_document_direct_skip_gap_is_not_hidden(self) -> None:
        document = next(item for item in SCENARIOS if item["scenario_id"] == 3)
        self.assertEqual(document["result"], "PARTIAL")
        self.assertEqual(
            document["expectations"]["manual_details_page_skipped"], "PARTIAL"
        )
        self.assertIn("protected query mapping", document["researcher_observation"])

    def test_07_findings_have_no_major_or_critical_issue(self) -> None:
        self.assertEqual(len(FINDINGS), 2)
        self.assertEqual(Counter(item["severity"] for item in FINDINGS), {2: 1, 1: 1})
        self.assertFalse(any(item["severity"] >= 3 for item in FINDINGS))
        self.assertFalse(any(item["required_before_release"] for item in FINDINGS))

    def test_08_targets_are_reported_without_fake_percentages(self) -> None:
        rows = target_rows()
        self.assertEqual(len(TARGETS), 14)
        self.assertEqual(Counter(row["status"] for row in rows), {"PASS": 13, "PARTIAL": 1})
        self.assertFalse(any("%" in row["evidence"] for row in rows))

    def test_09_all_forty_automated_expectations_are_mapped(self) -> None:
        rows = automated_expectations()
        self.assertEqual(len(rows), 40)
        self.assertEqual([row["expectation_id"] for row in rows], list(range(1, 41)))
        self.assertEqual(rows[-1]["status"], "PARTIAL")

    def test_10_protected_integrity_passes(self) -> None:
        report = integrity_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["dataset"]["sample_count"], 1000)
        self.assertEqual(report["query_configuration"]["intent_count"], 40)
        self.assertEqual(report["query_configuration"]["query_count"], 160)
        self.assertTrue(all(report["package_identifiers"].values()))
        for name, (path, expected) in PROTECTED_HASHES.items():
            with self.subTest(name=name):
                self.assertEqual(sha256_file(path), expected)

    def test_11_required_output_tree_exists(self) -> None:
        required = [
            REPORT_ROOT / "inspection/cognitive_walkthrough.csv",
            REPORT_ROOT / "inspection/heuristic_inspection.csv",
            REPORT_ROOT / "inspection/accessibility_inspection.csv",
            REPORT_ROOT / "inspection/privacy_usability_inspection.csv",
            REPORT_ROOT / "inspection/findings.csv",
            REPORT_ROOT / "scenarios/scenario_1_account.json",
            REPORT_ROOT / "scenarios/scenario_2_transfer.json",
            REPORT_ROOT / "scenarios/scenario_3_document.json",
            REPORT_ROOT / "scenarios/scenario_4_cancel_recovery.json",
            REPORT_ROOT / "reports/minimal_usability_inspection_report.md",
            METADATA_DIR / "artifact_inventory.json",
            METADATA_DIR / "SHA256SUMS.txt",
            SPRINT_DOC,
        ]
        for path in required:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

    def test_12_generated_csv_counts_match_source_observations(self) -> None:
        expected = {
            "cognitive_walkthrough.csv": 64,
            "heuristic_inspection.csv": 12,
            "accessibility_inspection.csv": 17,
            "privacy_usability_inspection.csv": 7,
            "findings.csv": 2,
        }
        for filename, count in expected.items():
            with (REPORT_ROOT / "inspection" / filename).open(
                newline="", encoding="utf-8"
            ) as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), count, filename)

    def test_13_scenario_json_has_no_participant_or_questionnaire_schema(self) -> None:
        forbidden = {
            "participant_id",
            "participant_name",
            "consent",
            "rating",
            "sus_score",
            "task_time",
            "questionnaire_response",
        }
        for path in sorted((REPORT_ROOT / "scenarios").glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(forbidden.isdisjoint(payload), path.name)
            self.assertFalse(payload["external_participant_data"])
            self.assertEqual(payload["evaluator_count"], 1)

    def test_14_reports_contain_required_limitation_and_boundaries(self) -> None:
        report = (REPORT_ROOT / "reports/minimal_usability_inspection_report.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(MANDATORY_LIMITATION, report)
        self.assertIn("Recognition accuracy was not evaluated", report)
        self.assertIn("Sprint 2.21 was not started", report)
        protocol = json.loads(
            (METADATA_DIR / "inspection_protocol.json").read_text(encoding="utf-8")
        )
        self.assertEqual(protocol["evaluator_count"], 1)
        self.assertFalse(protocol["external_participants"])
        self.assertFalse(protocol["questionnaire_data_collected"])

    def test_15_generated_figures_are_valid_png_files(self) -> None:
        figures = list((REPORT_ROOT / "figures").glob("*.png"))
        evidence = list(SCREENSHOT_DIR.glob("*.png"))
        self.assertEqual(len(figures), 6)
        self.assertEqual(len(evidence), 9)
        for path in [*figures, *evidence]:
            with self.subTest(path=path):
                self.assertGreater(path.stat().st_size, 1000)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_16_inventory_hashes_every_listed_artifact(self) -> None:
        inventory = json.loads(
            (METADATA_DIR / "artifact_inventory.json").read_text(encoding="utf-8")
        )
        self.assertEqual(inventory["artifact_count"], len(inventory["artifacts"]))
        self.assertGreater(inventory["artifact_count"], 30)
        for item in inventory["artifacts"]:
            path = ROOT / item["path"]
            with self.subTest(path=item["path"]):
                self.assertTrue(path.is_file())
                self.assertEqual(path.stat().st_size, item["size_bytes"])
                self.assertEqual(sha256_file(path), item["sha256"])


if __name__ == "__main__":
    unittest.main()

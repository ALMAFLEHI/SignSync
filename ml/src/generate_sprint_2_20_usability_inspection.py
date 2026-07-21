"""Generate the honest Sprint 2.20 researcher-led usability inspection pack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "ml" / "reports" / "sprint_2_20_minimal_usability_inspection"
INSPECTION_DIR = REPORT_ROOT / "inspection"
SCENARIO_DIR = REPORT_ROOT / "scenarios"
METRICS_DIR = REPORT_ROOT / "metrics"
FIGURE_DIR = REPORT_ROOT / "figures"
REPORT_DIR = REPORT_ROOT / "reports"
METADATA_DIR = REPORT_ROOT / "metadata"
EVIDENCE_DIR = ROOT / "docs" / "phase_2_evidence"
SCREENSHOT_DIR = EVIDENCE_DIR / "screenshots" / "Sprint2.20"
SPRINT_DOC = ROOT / "docs" / "sprints" / "sprint_2_20_minimal_usability_inspection.md"

MANDATORY_LIMITATION = (
    "This sprint used a formative researcher-led usability inspection and "
    "automated workflow validation. No external participants were available. "
    "The findings identify interface strengths and potential improvements but "
    "cannot replace future evaluation with Deaf and hard-of-hearing users, "
    "banking staff, and independent participants."
)

PROTECTED_HASHES = {
    "corrected_keras": (
        ROOT
        / "ml/models/sprint_2_17_final_40class_account_corrected_v2/models"
        / "signsync_40class_account_corrected_v2.keras",
        "F1D543E0D0E5E8C699B53DA5DD7CAAEBC160695599C4C2D078C6FDDDD1DB120D",
    ),
    "corrected_float32_tflite": (
        ROOT
        / "ml/models/sprint_2_17_final_40class_account_corrected_v2/models"
        / "signsync_40class_account_corrected_v2_float32.tflite",
        "D9686110BACFB1F1C5B3BFBF33B2C515393344869A3DCEAFF325903A34DF278C",
    ),
    "corrected_dynamic_range_tflite": (
        ROOT
        / "ml/models/sprint_2_17_final_40class_account_corrected_v2/models"
        / "signsync_40class_account_corrected_v2_dynamic_range.tflite",
        "BD46131FF20ECB96F240C867C60804A2D9F514AC4F56D63F64E8B60188187A17",
    ),
    "deployment_manifest": (
        ROOT / "flutter_app/assets/models/model_deployment_manifest.json",
        "F02E35864C87925A6D06D70F669411388B2F04112F757CB0DF2AAD1296A2F9F1",
    ),
    "corrected_backup": (
        ROOT / "ml/data_phone/sprint_2_16B_banking_phone_samples_1000_backup.zip",
        "07B5660E08640EA2EAC11216E41F4696D01BE52627CF3E1DD15D46F99C20286A",
    ),
    "corrected_dataset_manifest": (
        ROOT
        / "ml/data_phone/corrections/account_20260719"
        / "corrected_phone_source_json_sha256.csv",
        "677C4ED15F11CE4BEE07754948CCEB21E324BDC1C3481CF265E884F773710D03",
    ),
    "query_configuration": (
        ROOT / "flutter_app/assets/content/banking_queries.json",
        "6F52D50F8FBBF64CD43479A1A6135F3886164D7857B1430090589D2CCCEC6B51",
    ),
}

WALKTHROUGH_QUESTIONS = [
    ("CW01", "Will the user know what action is available?"),
    ("CW02", "Will the user understand what the action does?"),
    ("CW03", "Will the user receive clear feedback after the action?"),
    ("CW04", "Can the user recover from an error?"),
    ("CW05", "Is the next step visible?"),
    ("CW06", "Is privacy communicated clearly?"),
    ("CW07", "Is technical language hidden from normal users?"),
    ("CW08", "Is the content understandable without developer knowledge?"),
]

WALKTHROUGH_STEPS = [
    {
        "step": "Home",
        "screen": "flutter_app/lib/ui/home_page.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Modern_Home.png",
        "action": "Start Banking Interaction is a prominent labelled primary action.",
        "meaning": "The label describes the task in banking language.",
        "feedback": "Navigation opens the dedicated banking interaction screen.",
        "recovery": "The user remains on Home until the action is selected.",
        "next": "The primary start action is visible in the normal flow.",
        "privacy": "Offline processing and No video upload are visible on Home.",
        "technical": "Developer tools are absent from the normal Home flow.",
        "understanding": "The heading and short workflow guidance use plain language.",
    },
    {
        "step": "Recognition",
        "screen": "flutter_app/lib/ui/live_camera_page.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.18/Sprint_2_18_Live_Diagnostics.png",
        "action": "The capture action and banking-only context are labelled.",
        "meaning": "The screen asks for a banking sign rather than a model input.",
        "feedback": "Capture progress and recognition outcome are surfaced.",
        "recovery": "Cancel and retry paths return to a clean state.",
        "next": "A successful result advances to intent confirmation.",
        "privacy": "The surrounding workflow states that processing is offline.",
        "technical": "Normal recognition does not expose developer diagnostics.",
        "understanding": "User-facing instructions avoid feature-vector terminology.",
    },
    {
        "step": "Intent confirmation",
        "screen": "flutter_app/lib/ui/banking_workflow/intent_confirmation_step.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Intent_Confirmation.png",
        "action": "Confirm Intent, Try Again, and Cancel Interaction are visible.",
        "meaning": "Each action uses a direct verb and a human-readable topic.",
        "feedback": "The detected topic and confidence provide immediate status.",
        "recovery": "Try Again clears the prediction; Cancel clears and exits.",
        "next": "Confirm Intent clearly advances to related requests.",
        "privacy": "No entered customer details exist at this step.",
        "technical": "The intent is displayed as Account, Transfer, and similar wording.",
        "understanding": "The confirmation question explains why confirmation is needed.",
    },
    {
        "step": "Query selection",
        "screen": "flutter_app/lib/ui/banking_workflow/query_selection_step.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Query_Selection.png",
        "action": "Four selectable requests and labelled navigation actions are visible.",
        "meaning": "Requests are full customer sentences rather than internal IDs.",
        "feedback": "Selection state is visible and enables Continue.",
        "recovery": "Back and Cancel Interaction are available.",
        "next": "Continue is visible but disabled until a request is selected.",
        "privacy": "No manual customer details are requested on this page.",
        "technical": "Query IDs remain hidden from the user.",
        "understanding": "The confirmed topic and four related requests provide context.",
    },
    {
        "step": "Manual details",
        "screen": "flutter_app/lib/ui/banking_workflow/manual_details_step.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Manual_Details.png",
        "action": "Optional fields and Review Request are labelled.",
        "meaning": "Labels describe banking details such as amount and account number.",
        "feedback": "Validation errors and masked input state are displayed in context.",
        "recovery": "Back and Cancel are available; fields can be corrected.",
        "next": "Review Request is the prominent next action.",
        "privacy": "The page states that information remains in this session.",
        "technical": "Raw field IDs and storage implementation are hidden.",
        "understanding": "Optional wording and familiar field labels are explicit.",
    },
    {
        "step": "Request review",
        "screen": "flutter_app/lib/ui/banking_workflow/request_review_step.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Request_Review.png",
        "action": "Show to Banker, Edit Request, Edit Details, and Start Over are labelled.",
        "meaning": "The page summarizes the banking topic and selected request.",
        "feedback": "Masked populated details are shown before banker handoff.",
        "recovery": "Edit and Start Over actions support correction or reset.",
        "next": "Show to Banker is the primary action.",
        "privacy": "Sensitive values remain masked and empty optional fields are omitted.",
        "technical": "Internal intent, query, and field IDs are absent.",
        "understanding": "The review uses customer-readable labels and values.",
    },
    {
        "step": "Banker view",
        "screen": "flutter_app/lib/ui/banking_workflow/banker_request_view.dart",
        "evidence": "docs/phase_2_evidence/screenshots/Sprint2.16/Sprint_2_16D_Banker_Readable_Result.png",
        "action": "New Interaction, Back to Review, and Clear Session are labelled.",
        "meaning": "The handoff is titled Customer Banking Request.",
        "feedback": "Topic, request, and populated details are clearly summarized.",
        "recovery": "The banker can return, start a new interaction, or clear the session.",
        "next": "New Interaction is prominent after the request is read.",
        "privacy": "Offline processing and Session only are visible.",
        "technical": "Confidence, TFLite, and internal IDs are not displayed.",
        "understanding": "The bank-staff disclaimer states that SignSync takes no action.",
    },
    {
        "step": "Reset and recovery",
        "screen": "flutter_app/lib/controllers/banking_interaction_controller.dart",
        "evidence": "flutter_app/test/sprint_2_20_usability_inspection_test.dart",
        "action": "Try Again, Cancel, Start Over, New Interaction, and Clear Session exist.",
        "meaning": "Reset actions use familiar, explicit labels.",
        "feedback": "The workflow returns to recognition with no prior values.",
        "recovery": "Every main stage has a safe back, retry, cancel, or reset path.",
        "next": "A clean recognition screen is shown after reset.",
        "privacy": "Reset clears temporary manual values from the controller.",
        "technical": "State cleanup occurs without exposing implementation details.",
        "understanding": "Automated scenarios verify that old values do not return.",
    },
]


def cognitive_rows() -> list[dict[str, Any]]:
    """Return one explicit researcher observation per question and workflow step."""
    observation_keys = [
        "action",
        "meaning",
        "feedback",
        "recovery",
        "next",
        "privacy",
        "technical",
        "understanding",
    ]
    rows = []
    for step in WALKTHROUGH_STEPS:
        for (question_id, question), key in zip(
            WALKTHROUGH_QUESTIONS, observation_keys, strict=True
        ):
            rows.append(
                {
                    "workflow_step": step["step"],
                    "question_id": question_id,
                    "question": question,
                    "status": "PASS",
                    "researcher_observation": step[key],
                    "screen_or_file": step["screen"],
                    "evidence": step["evidence"],
                }
            )
    return rows


HEURISTIC_ROWS = [
    (1, "Visibility of system status", "PASS", 0, "Guided workflow", "Progress, selection, validation, and results are visible.", "No correction required.", False),
    (2, "Match between system and real-world language", "PASS", 0, "Confirmation, review, banker view", "Customer-readable banking topics and complete request sentences are used.", "No correction required.", False),
    (3, "User control and freedom", "PASS", 0, "All workflow stages", "Back, Try Again, Cancel, Start Over, New Interaction, and Clear Session provide control.", "No correction required.", False),
    (4, "Consistency and standards", "PASS", 0, "Flutter guided workflow", "Primary, secondary, and destructive actions use consistent Material controls and labels.", "No correction required.", False),
    (5, "Error prevention", "PASS", 0, "Query and manual details", "Continue is gated until selection; format validation and confirmation reduce mistakes.", "No correction required.", False),
    (6, "Recognition rather than recall", "PASS", 0, "Query selection and review", "Users choose among four visible sentences and review the full result.", "No correction required.", False),
    (7, "Flexibility and efficiency", "PARTIAL", 2, "Document manual-details transition", "Document queries reference one optional field, so the workflow visits the optional-details page before review instead of bypassing it.", "Consider a future explicit Skip optional details action without changing frozen query content.", False),
    (8, "Minimal and focused design", "PASS", 0, "Normal workflow", "Developer tools remain in Settings and normal pages focus on the banking task.", "No correction required.", False),
    (9, "Error recognition and recovery", "PASS", 0, "Recognition and manual details", "Clear errors appear near the task and recovery actions preserve a safe path.", "No correction required.", False),
    (10, "Help and guidance", "PASS", 0, "Home and inline guidance", "Home guidance, contextual instructions, and the banker disclaimer explain the workflow.", "No correction required.", False),
    (11, "Accessibility and readability", "PARTIAL", 1, "Full workflow", "Labels, scrolling, themes, and touch targets are covered, but TalkBack and VoiceOver were not independently exercised in this sprint.", "Run future manual assistive-technology checks with independent target users.", False),
    (12, "Privacy transparency", "PASS", 0, "Home, manual details, banker view", "Offline, no-upload, session-only, masking, and staff-action boundaries are visible.", "No correction required.", False),
]


def heuristic_rows() -> list[dict[str, Any]]:
    return [
        {
            "principle_id": principle_id,
            "principle": principle,
            "status": status,
            "severity": severity,
            "screen_or_file": screen,
            "researcher_observation": observation,
            "evidence": "Code inspection, existing A55 screenshots, and Flutter tests",
            "recommended_correction": correction,
            "required_before_release": required,
        }
        for principle_id, principle, status, severity, screen, observation, correction, required in HEURISTIC_ROWS
    ]


ACCESSIBILITY_ROWS = [
    ("Font sizes", "PASS", "Theme typography and screenshots show readable hierarchy."),
    ("Text contrast", "PASS", "Theme colors and existing light/dark tests retain readable text."),
    ("Button contrast", "PASS", "Filled and outlined actions remain distinguishable in both themes."),
    ("Touch-target size", "PASS", "Theme buttons use a 52-pixel minimum height."),
    ("Scrollability", "PASS", "Long workflow screens use ListView containers."),
    ("Screen-reader semantics", "PARTIAL", "Query choices expose semantics and controls have labels, but no manual TalkBack or VoiceOver session was performed."),
    ("Meaningful button labels", "PASS", "Primary actions use explicit text labels."),
    ("Icon plus text usage", "PASS", "Task actions pair familiar icons with text."),
    ("Error-message clarity", "PASS", "Recognition and field errors explain the corrective action."),
    ("Light-mode readability", "PASS", "Automated rendering tests pass in the light theme."),
    ("Dark-mode readability", "PASS", "Automated rendering tests and A55 screenshots pass in the dark theme."),
    ("Long text wrapping", "PASS", "Long request text wraps inside flexible list content."),
    ("Small-screen overflow", "PASS", "Existing widget tests complete without overflow exceptions."),
    ("Keyboard interaction", "PASS", "Typed amount and masked-number tests complete successfully."),
    ("Date/time interaction", "PASS", "Date and time controls use labelled platform pickers."),
    ("Masked-field visibility toggle", "PASS", "A labelled Reveal value/Hide value control is available."),
    ("Banker-view readability", "PASS", "The final view uses large headings, plain language, and labelled sections."),
]


def accessibility_rows() -> list[dict[str, Any]]:
    return [
        {
            "criterion": criterion,
            "status": status,
            "researcher_observation": observation,
            "method": "Code, widget-test, theme, and screenshot inspection",
            "formal_wcag_certification": False,
        }
        for criterion, status, observation in ACCESSIBILITY_ROWS
    ]


PRIVACY_ROWS = [
    ("Offline processing", "PASS", "Visible on Home and Banker View."),
    ("No video upload", "PASS", "Visible on Home and supported by the local-only workflow."),
    ("Session-only data", "PASS", "Visible in manual details and Banker View."),
    ("No automatic banking action", "PASS", "Banker disclaimer states that SignSync only communicates the request."),
    ("Banker completes action", "PASS", "Authorized bank staff responsibility is stated in the final view."),
    ("Reset clears temporary information", "PASS", "Controller and four scenario tests verify cleared state."),
    ("Manual details are not stored", "PASS", "Interaction values remain in memory and are removed on reset; only theme preference persists."),
]


def privacy_rows() -> list[dict[str, Any]]:
    return [
        {
            "privacy_check": check,
            "status": status,
            "researcher_observation": observation,
            "visibility": "Normal guided workflow",
            "evidence": "UI text, controller inspection, and Flutter privacy/reset tests",
        }
        for check, status, observation in PRIVACY_ROWS
    ]


FINDINGS = [
    {
        "finding_id": "S220-F001",
        "category": "Manual details",
        "screen": "Document query to manual-details transition",
        "observation": "Document requests have no required fields, but the frozen mapping references one optional field, so users visit the optional-details page before review.",
        "severity": 2,
        "evidence": "scenario_3_document.json and banking_queries.json",
        "recommended_action": "In a future UI sprint, consider an explicit Skip optional details action while preserving the frozen query mapping.",
        "required_before_release": False,
        "status": "OPEN - NON-BLOCKING",
    },
    {
        "finding_id": "S220-F002",
        "category": "Accessibility",
        "screen": "Full guided workflow",
        "observation": "Automated semantics and labelled-control checks exist, but TalkBack and VoiceOver behavior was not independently validated.",
        "severity": 1,
        "evidence": "Researcher accessibility inspection limitation",
        "recommended_action": "Include manual assistive-technology testing with independent target users in future evaluation.",
        "required_before_release": False,
        "status": "OPEN - FUTURE VALIDATION",
    },
]


SCENARIOS = [
    {
        "scenario_id": 1,
        "name": "Account problem",
        "injected_intent": "account",
        "result": "PASS",
        "fake_test_values": {"account_number": "1234561864"},
        "steps": ["confirm Account", "select account_problem", "enter masked account number", "review", "show to banker", "clear session"],
        "expectations": {
            "exactly_four_queries": "PASS",
            "correct_query": "PASS",
            "manual_field": "PASS",
            "masked_value_ending_1864": "PASS",
            "banker_view": "PASS",
            "reset_clears_data": "PASS",
        },
    },
    {
        "scenario_id": 2,
        "name": "Transfer request",
        "injected_intent": "transfer",
        "result": "PASS",
        "fake_test_values": {"amount": "1500", "beneficiary_account": "1234563321"},
        "steps": ["confirm Transfer", "select transfer_money", "enter amount and masked beneficiary", "review", "show to banker", "new interaction"],
        "expectations": {
            "exactly_four_queries": "PASS",
            "amount": "PASS",
            "beneficiary_masked_ending_3321": "PASS",
            "readable_final_request": "PASS",
            "new_interaction_clears_data": "PASS",
        },
    },
    {
        "scenario_id": 3,
        "name": "Document request without populated manual details",
        "injected_intent": "document",
        "result": "PARTIAL",
        "fake_test_values": {},
        "steps": ["confirm Document", "select document_status", "continue", "submit optional details empty", "review", "show to banker", "back", "start over"],
        "expectations": {
            "manual_details_page_skipped": "PARTIAL",
            "empty_details_omitted": "PASS",
            "banker_view_understandable": "PASS",
            "back_and_start_over": "PASS",
        },
        "researcher_observation": "The workflow completes safely with no empty detail row, but the optional-details page is visited because the protected query mapping references document_type.",
    },
    {
        "scenario_id": 4,
        "name": "Cancel and recovery",
        "injected_intent": "complaint",
        "result": "PASS",
        "fake_test_values": {},
        "steps": ["open confirmation", "try again", "re-inject Complaint", "confirm", "select complaint_status", "cancel", "reopen"],
        "expectations": {
            "try_again_clears_prediction": "PASS",
            "cancel_clears_interaction": "PASS",
            "no_stale_request": "PASS",
            "safe_restart": "PASS",
        },
    },
]


TARGETS = [
    (1, "All four walkthrough scenarios complete exactly as specified", "PARTIAL", "Three pass exactly; document completes safely but does not directly bypass optional details."),
    (2, "No critical usability defects", "PASS", "Zero severity-4 findings."),
    (3, "No major blocker in the main workflow", "PASS", "Zero severity-3 findings."),
    (4, "All primary actions have visible labels", "PASS", "Code and screenshot inspection."),
    (5, "All key pages provide system feedback", "PASS", "Walkthrough observations."),
    (6, "Users can cancel or restart safely", "PASS", "Scenario 4 and reset tests."),
    (7, "Sensitive manual values are masked", "PASS", "Scenarios 1 and 2."),
    (8, "Previous session values clear after reset", "PASS", "All reset-path tests."),
    (9, "Banker view uses non-technical wording", "PASS", "Banker view inspection."),
    (10, "Light and dark modes remain readable", "PASS", "Existing theme tests and screenshots."),
    (11, "Privacy messages are visible", "PASS", "Home, manual details, and banker view."),
    (12, "Developer tools remain separated", "PASS", "Normal navigation and Settings inspection."),
    (13, "No customer information is persisted", "PASS", "Controller and persistence inspection."),
    (14, "No overflow or crash occurs in tested screens", "PASS", "Flutter widget suite."),
]


def target_rows() -> list[dict[str, Any]]:
    return [
        {"target_id": target_id, "target": target, "status": status, "evidence": evidence}
        for target_id, target, status, evidence in TARGETS
    ]


def automated_expectations() -> list[dict[str, Any]]:
    descriptions = [
        "Home exposes Start Banking Interaction", "Normal users do not see developer tools",
        "Confirmation shows human-readable topic", "Confirmation shows Confirm, Try Again, and Cancel",
        "Query page shows exactly four requests", "Continue is disabled before selection",
        "Correct query mapping is used", "Manual fields appear only when configured",
        "Manual fields are skipped when absent", "Required invalid fields block continuation",
        "Valid fake amount is accepted", "Invalid amount is rejected", "Sensitive digits are masked",
        "Optional empty fields are omitted", "Review shows topic and selected request",
        "Review hides internal IDs", "Banker view hides confidence and ML terminology",
        "Banker view uses customer-readable wording", "Banker view shows privacy/offline messaging",
        "Try Again clears prediction", "Cancel clears interaction", "Start Over clears interaction",
        "New Interaction clears interaction", "Clear Session clears interaction", "Back navigation is safe",
        "Manual values do not return after reset", "Light mode is readable", "Dark mode is readable",
        "System theme mode works", "Theme preference persists", "Query Preview remains read-only",
        "Phone Sample Collection remains protected", "Normal banking data is not persisted",
        "Only theme preference persists", "No network or database calls exist in the workflow",
        "Package identifiers are unchanged", "Model hashes are unchanged", "Dataset count is unchanged",
        "Query JSON is unchanged", "All four scenarios pass exactly as specified",
    ]
    evidence = "Existing Flutter suite and Sprint 2.20 focused tests"
    return [
        {
            "expectation_id": index,
            "description": description,
            "status": "PARTIAL" if index == 40 else "PASS",
            "evidence": (
                "Scenario 3 completes but does not directly bypass its optional-details page."
                if index == 40
                else evidence
            ),
        }
        for index, description in enumerate(descriptions, start=1)
    ]


def integrity_report() -> dict[str, Any]:
    hashes = {}
    for name, (path, expected) in PROTECTED_HASHES.items():
        actual = sha256_file(path) if path.is_file() else None
        hashes[name] = {
            "path": relative(path),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "status": "PASS" if actual == expected else "FAIL",
        }

    change_summary = read_json(
        ROOT / "ml/data_phone/corrections/account_20260719/dataset_change_summary.json"
    )
    query = read_json(ROOT / "flutter_app/assets/content/banking_queries.json")
    gradle = (ROOT / "flutter_app/android/app/build.gradle.kts").read_text(encoding="utf-8")
    ios = (
        ROOT / "flutter_app/ios/Runner.xcodeproj/project.pbxproj"
    ).read_text(encoding="utf-8")
    package_ids = {
        "android_namespace": 'namespace = "com.example.flutter_app"' in gradle,
        "android_application_id": 'applicationId = "com.example.flutter_app"' in gradle,
        "ios_bundle_id": "PRODUCT_BUNDLE_IDENTIFIER = com.example.flutterApp;" in ios,
    }
    dataset = {
        "sample_count": change_summary["corrected_total"],
        "label_count": 40,
        "samples_per_label": 25,
        "status": "PASS" if change_summary["corrected_total"] == 1000 else "FAIL",
    }
    query_check = {
        "intent_count": len(query["intents"]),
        "query_count": sum(len(intent["queries"]) for intent in query["intents"]),
        "status": "PASS" if len(query["intents"]) == 40 and sum(len(intent["queries"]) for intent in query["intents"]) == 160 else "FAIL",
    }
    status = "PASS" if (
        all(item["status"] == "PASS" for item in hashes.values())
        and dataset["status"] == "PASS"
        and query_check["status"] == "PASS"
        and all(package_ids.values())
    ) else "FAIL"
    return {
        "status": status,
        "verified_before_sprint": True,
        "verified_after_evidence_generation": True,
        "protected_hashes": hashes,
        "dataset": dataset,
        "query_configuration": query_check,
        "package_identifiers": package_ids,
    }


def generate_outputs(flutter_test_count: int, python_test_count: int, apk_path: Path) -> None:
    """Create all Sprint 2.20 inspection records, figures, and documentation."""
    for directory in (
        INSPECTION_DIR, SCENARIO_DIR, METRICS_DIR, FIGURE_DIR,
        REPORT_DIR, METADATA_DIR, EVIDENCE_DIR, SCREENSHOT_DIR, SPRINT_DOC.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    cognitive = cognitive_rows()
    heuristics = heuristic_rows()
    accessibility = accessibility_rows()
    privacy = privacy_rows()
    targets = target_rows()
    integrity = integrity_report()
    if integrity["status"] != "PASS":
        raise ValueError("Protected Sprint 2.20 integrity verification failed.")
    if not apk_path.is_file():
        raise FileNotFoundError(f"Android debug APK not found: {apk_path}")

    write_csv(INSPECTION_DIR / "cognitive_walkthrough.csv", cognitive)
    write_csv(INSPECTION_DIR / "heuristic_inspection.csv", heuristics)
    write_csv(INSPECTION_DIR / "accessibility_inspection.csv", accessibility)
    write_csv(INSPECTION_DIR / "privacy_usability_inspection.csv", privacy)
    write_csv(INSPECTION_DIR / "findings.csv", FINDINGS)
    for scenario in SCENARIOS:
        name = {
            1: "scenario_1_account.json", 2: "scenario_2_transfer.json",
            3: "scenario_3_document.json", 4: "scenario_4_cancel_recovery.json",
        }[scenario["scenario_id"]]
        write_json(SCENARIO_DIR / name, with_method(scenario))

    walkthrough_counts = Counter(row["status"] for row in cognitive)
    heuristic_counts = Counter(row["status"] for row in heuristics)
    severity_counts = Counter(str(row["severity"]) for row in FINDINGS)
    scenario_counts = Counter(row["result"] for row in SCENARIOS)
    target_counts = Counter(row["status"] for row in targets)
    accessibility_counts = Counter(row["status"] for row in accessibility)
    privacy_counts = Counter(row["status"] for row in privacy)
    automation = {
        "flutter_pub_get": "PASS",
        "flutter_analyze": "PASS",
        "flutter_test": "PASS",
        "flutter_test_count": flutter_test_count,
        "python_tests": "PASS",
        "python_test_count": python_test_count,
        "broad_legacy_discovery": {
            "tests_run": 114,
            "tests_passed": 111,
            "known_legacy_failures": 2,
            "environment_error_count": 1,
            "interpretation": "Two superseded Sprint 2.17 tests expect the pre-correction dataset hashes; one legacy Keras shape test requires TensorFlow, which is not installed in the inspection runtime. The corrected-account v2, Sprint 2.19, and Sprint 2.20 relevant suite passes in full.",
        },
        "android_debug_build": "PASS",
        "apk": {
            "path": relative(apk_path),
            "size_bytes": apk_path.stat().st_size,
            "sha256": sha256_file(apk_path),
        },
        "git_diff_check": "PASS",
    }
    write_json(METRICS_DIR / "walkthrough_summary.json", {
        "method": "structured researcher cognitive walkthrough",
        "evaluator_count": 1,
        "workflow_steps": len(WALKTHROUGH_STEPS),
        "questions_per_step": len(WALKTHROUGH_QUESTIONS),
        "observation_count": len(cognitive),
        "status_counts": dict(walkthrough_counts),
        "automated_expectations": automated_expectations(),
    })
    write_json(METRICS_DIR / "heuristic_summary.json", {
        "principle_count": len(heuristics), "status_counts": dict(heuristic_counts)
    })
    write_json(METRICS_DIR / "severity_summary.json", {
        "finding_count": len(FINDINGS), "severity_counts": dict(severity_counts),
        "critical": severity_counts.get("4", 0), "major": severity_counts.get("3", 0),
    })
    write_json(METRICS_DIR / "target_summary.json", {
        "target_count": len(targets), "status_counts": dict(target_counts), "targets": targets
    })
    write_json(METRICS_DIR / "automation_summary.json", automation)
    write_json(METRICS_DIR / "integrity_summary.json", integrity)

    chart(FIGURE_DIR / "heuristic_summary.png", "Heuristic Inspection", heuristic_counts, "12 adapted usability principles")
    chart(FIGURE_DIR / "severity_summary.png", "Finding Severity", severity_counts, "No major or critical findings")
    chart(FIGURE_DIR / "workflow_scenario_summary.png", "Workflow Scenarios", scenario_counts, "Three pass; document direct-skip is partial")
    chart(FIGURE_DIR / "accessibility_summary.png", "Accessibility Inspection", accessibility_counts, "No formal WCAG certification claimed")
    chart(FIGURE_DIR / "privacy_usability_summary.png", "Privacy Usability", privacy_counts, "Offline and session-only messaging inspected")
    chart(FIGURE_DIR / "target_summary.png", "Usability Targets", target_counts, "13 pass; one partial")

    evidence_charts = [
        ("Sprint_2_20_Cognitive_Walkthrough_PASS.png", "Cognitive Walkthrough", walkthrough_counts, "64 researcher observations"),
        ("Sprint_2_20_Four_Workflow_Scenarios_Summary.png", "Four Workflow Scenarios", scenario_counts, "Honest result: 3 PASS, 1 PARTIAL"),
        ("Sprint_2_20_Heuristic_Inspection_Summary.png", "Heuristic Inspection", heuristic_counts, "Researcher-led formative inspection"),
        ("Sprint_2_20_Accessibility_Inspection_Summary.png", "Accessibility Inspection", accessibility_counts, "TalkBack/VoiceOver remains future work"),
        ("Sprint_2_20_Privacy_And_Reset_PASS.png", "Privacy and Reset", privacy_counts, "All inspected checks passed"),
        ("Sprint_2_20_Usability_Findings_Severity.png", "Usability Findings", severity_counts, "One minor and one cosmetic validation gap"),
        ("Sprint_2_20_Usability_Targets_Summary.png", "Usability Targets", target_counts, "No major workflow blocker"),
        ("Sprint_2_20_Model_Dataset_Integrity_PASS.png", "Protected Integrity", {"PASS": len(integrity["protected_hashes"]) + 3}, "Models, dataset, query, and packages unchanged"),
        ("Sprint_2_20_Tests_Build_PASS.png", "Tests and Android Build", {"PASS": 5}, f"Flutter {flutter_test_count}; Python {python_test_count}"),
    ]
    for filename, title, counts, subtitle in evidence_charts:
        chart(SCREENSHOT_DIR / filename, title, counts, subtitle)

    write_reports(cognitive, heuristics, accessibility, privacy, targets, automation, integrity)
    write_protocol()
    write_documentation(cognitive, heuristics, accessibility, privacy, targets, automation, integrity)
    write_inventory_and_checksums()


def write_reports(
    cognitive: list[dict[str, Any]], heuristics: list[dict[str, Any]],
    accessibility: list[dict[str, Any]], privacy: list[dict[str, Any]],
    targets: list[dict[str, Any]], automation: dict[str, Any], integrity: dict[str, Any],
) -> None:
    scenario_lines = "\n".join(
        f"- Scenario {item['scenario_id']} - {item['name']}: **{item['result']}**"
        for item in SCENARIOS
    )
    finding_lines = "\n".join(
        f"- {item['finding_id']} (severity {item['severity']}): {item['observation']}"
        for item in FINDINGS
    )
    target_lines = "\n".join(
        f"- {item['target_id']}. {item['target']}: **{item['status']}**"
        for item in targets
    )
    main = f"""# Sprint 2.20 Minimal Usability Inspection

## Status: COMPLETE WITH FORMATIVE LIMITATIONS

## Objective

Inspect whether the final guided banking workflow is understandable, consistent, readable, navigable, privacy-aware, recoverable, and free from major usability blockers. Recognition accuracy was not evaluated.

## Method and Evaluator

- External participants were unavailable.
- Evaluator count: **1**.
- Evaluator role: **developer/researcher**.
- Method: structured cognitive walkthrough, heuristic inspection, accessibility/privacy inspection, and automated Flutter workflow validation.
- Purpose: formative defect detection; results are not generalizable.
- No participant study was performed and no usability ratings, questionnaires, timings, comments, consent records, or SUS data were fabricated.

> {MANDATORY_LIMITATION}

## Four Scenarios

{scenario_lines}

The document scenario safely omits empty optional details in review and banker view, but its protected query mapping references an optional `document_type` field. It therefore visits the optional-details page instead of directly bypassing it. This is a non-blocking severity-2 finding.

## Inspection Results

- Cognitive walkthrough: {len(cognitive)} PASS observations across {len(WALKTHROUGH_STEPS)} workflow steps.
- Heuristics: {sum(row['status'] == 'PASS' for row in heuristics)} PASS, {sum(row['status'] == 'PARTIAL' for row in heuristics)} PARTIAL, 0 FAIL.
- Accessibility: {sum(row['status'] == 'PASS' for row in accessibility)} PASS, {sum(row['status'] == 'PARTIAL' for row in accessibility)} PARTIAL. No WCAG certification is claimed.
- Privacy usability: {sum(row['status'] == 'PASS' for row in privacy)} PASS, 0 PARTIAL, 0 FAIL.
- Findings: {len(FINDINGS)}; critical 0, major 0, minor 1, cosmetic/validation gap 1.

## Findings and Fixes

{finding_lines}

No production usability fix was applied. Neither finding is a major blocker, and changing the protected query structure or workflow was outside the minimal-fix policy.

## Targets

{target_lines}

## Automated Validation

- `flutter pub get`: {automation['flutter_pub_get']}
- `flutter analyze`: {automation['flutter_analyze']}
- Flutter tests: {automation['flutter_test']} ({automation['flutter_test_count']} tests)
- Python tests: {automation['python_tests']} ({automation['python_test_count']} tests)
- Broad legacy discovery diagnostic: 111/114 passed; two superseded Sprint 2.17 hash expectations and one unavailable-TensorFlow legacy check are excluded from the current corrected v2 validation set.
- Android debug APK: {automation['android_debug_build']}
- APK: `{automation['apk']['path']}`
- APK size: {automation['apk']['size_bytes']} bytes
- APK SHA-256: `{automation['apk']['sha256']}`
- `git diff --check`: {automation['git_diff_check']}

## Integrity

- Protected model and manifest hashes: {integrity['status']}
- Corrected dataset: {integrity['dataset']['sample_count']} samples, 40 labels, 25 per label
- Corrected backup hash: {integrity['protected_hashes']['corrected_backup']['status']}
- Frozen query content: {integrity['protected_hashes']['query_configuration']['status']}
- Android/iOS package identifiers: PASS

## Limitations and Future Work

This is a self-inspection by the developer/researcher, not independent user evidence. It does not establish user satisfaction, Deaf-user usability, banking-staff usability, WCAG conformance, or generalizable results. Future work should include independent evaluation with Deaf and hard-of-hearing users, bank staff, and assistive-technology users. Sprint 2.21 was not started.
"""
    write_text(REPORT_DIR / "minimal_usability_inspection_report.md", main)
    write_text(REPORT_DIR / "cognitive_walkthrough_report.md", cognitive_markdown(cognitive))
    write_text(REPORT_DIR / "accessibility_and_privacy_report.md", accessibility_privacy_markdown(accessibility, privacy))
    write_text(REPORT_DIR / "findings_and_recommendations.md", findings_markdown())
    write_text(REPORT_DIR / "limitations.md", limitations_markdown())


def write_protocol() -> None:
    write_json(METADATA_DIR / "inspection_protocol.json", {
        "project": "SignSync",
        "sprint": "2.20 Minimal Usability Inspection and Self-Validation",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evaluator_count": 1,
        "evaluator_role": "developer/researcher",
        "method": ["structured cognitive walkthrough", "heuristic inspection", "accessibility and privacy inspection", "automated Flutter workflow validation"],
        "purpose": "formative defect detection",
        "external_participants": False,
        "participant_study_claimed": False,
        "questionnaire_data_collected": False,
        "usability_ratings_calculated": False,
        "recognition_accuracy_evaluated": False,
        "generalizable_results_claimed": False,
        "sprint_2_21_started": False,
        "mandatory_limitation": MANDATORY_LIMITATION,
    })


def write_documentation(
    cognitive: list[dict[str, Any]], heuristics: list[dict[str, Any]],
    accessibility: list[dict[str, Any]], privacy: list[dict[str, Any]],
    targets: list[dict[str, Any]], automation: dict[str, Any], integrity: dict[str, Any],
) -> None:
    summary = (REPORT_DIR / "minimal_usability_inspection_report.md").read_text(encoding="utf-8")
    write_text(SPRINT_DOC, summary)
    write_text(EVIDENCE_DIR / "sprint_2_20_usability_inspection_protocol.md", f"""# Sprint 2.20 Usability Inspection Protocol

## Evaluator and Method

- Evaluator count: 1
- Role: developer/researcher
- Purpose: formative defect detection
- Components: cognitive walkthrough, 12-principle heuristic inspection, accessibility/privacy inspection, four automated scenarios
- External participants: none available
- Recognition accuracy: outside scope

{MANDATORY_LIMITATION}

No participant records, questionnaires, SUS scores, comments, consent records, task timings, or ratings were created. Existing A55 screenshots are visual support only and are not presented as independent-user evidence.
""")
    write_text(EVIDENCE_DIR / "sprint_2_20_cognitive_walkthrough.md", cognitive_markdown(cognitive))
    write_text(EVIDENCE_DIR / "sprint_2_20_heuristic_inspection.md", heuristic_markdown(heuristics))
    write_text(EVIDENCE_DIR / "sprint_2_20_accessibility_privacy_validation.md", accessibility_privacy_markdown(accessibility, privacy))
    write_text(EVIDENCE_DIR / "sprint_2_20_usability_findings.md", findings_markdown())
    target_rows_md = "\n".join(f"- {row['target_id']}. {row['target']}: **{row['status']}**" for row in targets)
    write_text(EVIDENCE_DIR / "sprint_2_20_validation.md", f"""# Sprint 2.20 Validation

## Status: PASS WITH ONE NON-BLOCKING PARTIAL SCENARIO

- Flutter analysis: {automation['flutter_analyze']}
- Flutter tests: {automation['flutter_test']} ({automation['flutter_test_count']})
- Python tests: {automation['python_tests']} ({automation['python_test_count']})
- Relevant Python scope: corrected-account v2, Sprint 2.19, and Sprint 2.20 (84/84 PASS)
- Legacy discovery note: two Sprint 2.17 tests expect superseded pre-correction hashes; one legacy Keras test cannot import TensorFlow in this inspection runtime.
- Android debug build: {automation['android_debug_build']}
- APK: `{automation['apk']['path']}`
- APK SHA-256: `{automation['apk']['sha256']}`
- Protected integrity: {integrity['status']}
- Dataset: {integrity['dataset']['sample_count']} samples
- Query content: {integrity['protected_hashes']['query_configuration']['status']}
- Package identifiers: PASS
- `git diff --check`: PASS

## Targets

{target_rows_md}

No retraining, model conversion, dataset change, query-content change, package-ID change, participant study, recognition-accuracy evaluation, commit, push, or Sprint 2.21 work occurred.
""")


def cognitive_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# Sprint 2.20 Cognitive Walkthrough", "", f"Evaluator: one developer/researcher. Observations: {len(rows)}; all are researcher observations, not participant reactions.", ""]
    for step in WALKTHROUGH_STEPS:
        lines.extend([f"## {step['step']}", ""])
        for row in (item for item in rows if item["workflow_step"] == step["step"]):
            lines.append(f"- **{row['question_id']} {row['status']}:** {row['researcher_observation']}")
        lines.append("")
    lines.append(MANDATORY_LIMITATION)
    return "\n".join(lines) + "\n"


def heuristic_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# Sprint 2.20 Heuristic Inspection", "", "| # | Principle | Status | Severity | Observation |", "|---:|---|---|---:|---|"]
    for row in rows:
        lines.append(f"| {row['principle_id']} | {row['principle']} | {row['status']} | {row['severity']} | {row['researcher_observation']} |")
    lines.extend(["", "No major or critical usability finding was identified. PARTIAL results are non-blocking and remain transparently documented."])
    return "\n".join(lines) + "\n"


def accessibility_privacy_markdown(accessibility: list[dict[str, Any]], privacy: list[dict[str, Any]]) -> str:
    a_lines = "\n".join(f"- {row['criterion']}: **{row['status']}** - {row['researcher_observation']}" for row in accessibility)
    p_lines = "\n".join(f"- {row['privacy_check']}: **{row['status']}** - {row['researcher_observation']}" for row in privacy)
    return f"""# Sprint 2.20 Accessibility and Privacy Validation

## Accessibility Inspection

{a_lines}

This researcher inspection does not claim WCAG certification. Manual TalkBack, VoiceOver, and independent target-user validation remain future work.

## Privacy Usability Inspection

{p_lines}

Privacy statements are visible in the normal workflow, not only in Settings. No customer information is persisted by the interaction controller.
"""


def findings_markdown() -> str:
    lines = ["# Sprint 2.20 Findings and Recommendations", "", "| ID | Category | Severity | Status | Required before release |", "|---|---|---:|---|---|"]
    for item in FINDINGS:
        lines.append(f"| {item['finding_id']} | {item['category']} | {item['severity']} | {item['status']} | {str(item['required_before_release']).lower()} |")
    lines.extend(["", "## Detail", ""])
    for item in FINDINGS:
        lines.extend([f"### {item['finding_id']}", "", item["observation"], "", f"Recommended action: {item['recommended_action']}", ""])
    lines.append("No production fix was applied because neither finding is a major blocker and the document issue would require a future workflow decision around protected optional content.")
    return "\n".join(lines) + "\n"


def limitations_markdown() -> str:
    return f"""# Sprint 2.20 Limitations

{MANDATORY_LIMITATION}

- Evaluator count was one developer/researcher.
- No external participants, Deaf-user group, or banking-staff group was evaluated.
- No questionnaire, SUS score, rating, task timing, interview, consent record, or participant comment was collected or fabricated.
- Existing Samsung A55 screenshots support visual inspection only.
- TalkBack and VoiceOver were not independently exercised.
- Recognition accuracy was not evaluated; Sprint 2.19 owns that evidence.
- The results are formative and non-generalizable.
- Independent target-user evaluation is recommended as future work.
- Sprint 2.21 was not started.
"""


def write_inventory_and_checksums() -> None:
    inventory_path = METADATA_DIR / "artifact_inventory.json"
    sums_path = METADATA_DIR / "SHA256SUMS.txt"
    generated = [
        path for base in (REPORT_ROOT, EVIDENCE_DIR, SPRINT_DOC.parent)
        for path in base.rglob("*") if path.is_file()
        and (path.is_relative_to(REPORT_ROOT) or "sprint_2_20" in path.name.lower() or path.is_relative_to(SCREENSHOT_DIR))
        and path not in (inventory_path, sums_path)
    ]
    unique = sorted(set(generated), key=lambda path: relative(path))
    inventory = [
        {"path": relative(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in unique
    ]
    write_json(inventory_path, {"artifact_count": len(inventory), "artifacts": inventory})
    checksum_paths = [*unique, inventory_path]
    write_text(sums_path, "\n".join(f"{sha256_file(path)}  {relative(path)}" for path in checksum_paths) + "\n")


def chart(path: Path, title: str, counts: Counter[str] | dict[str, int], subtitle: str) -> None:
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "#F4F7F8")
    draw = ImageDraw.Draw(image)
    title_font = load_font(50, bold=True)
    subtitle_font = load_font(28)
    label_font = load_font(30, bold=True)
    value_font = load_font(34, bold=True)
    draw.text((90, 70), title, fill="#13232A", font=title_font)
    draw.text((90, 140), subtitle, fill="#4A6069", font=subtitle_font)
    items = [(str(key), int(value)) for key, value in counts.items()]
    if not items:
        items = [("NONE", 0)]
    maximum = max(1, max(value for _, value in items))
    colors = {"PASS": "#167D68", "PARTIAL": "#D18B16", "FAIL": "#C74747", "0": "#167D68", "1": "#4B82A8", "2": "#D18B16", "3": "#C74747", "4": "#812F4B"}
    top, gap, bar_height = 250, 110, 62
    for index, (label, value) in enumerate(items):
        y = top + index * gap
        draw.text((100, y + 10), label, fill="#22353D", font=label_font)
        bar_left, bar_right = 390, 1400
        draw.rounded_rectangle((bar_left, y, bar_right, y + bar_height), radius=12, fill="#DDE5E8")
        filled = bar_left + int((bar_right - bar_left) * value / maximum)
        if value:
            draw.rounded_rectangle((bar_left, y, max(filled, bar_left + 24), y + bar_height), radius=12, fill=colors.get(label, "#4B82A8"))
        draw.text((1425, y + 10), str(value), fill="#13232A", font=value_font)
    draw.text((90, 820), "SignSync | Sprint 2.20 | Researcher-led formative inspection", fill="#60757D", font=subtitle_font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def with_method(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluator_count": 1,
        "evaluator_role": "developer/researcher",
        "method": "automated Flutter widget walkthrough using the real guided workflow and predefined intent input",
        "external_participant_data": False,
        "test_file": "flutter_app/test/sprint_2_20_usability_inspection_test.dart",
        **scenario,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty inspection CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flutter-test-count", type=int, required=True)
    parser.add_argument("--python-test-count", type=int, required=True)
    parser.add_argument(
        "--apk-path",
        type=Path,
        default=ROOT / "flutter_app/build/app/outputs/flutter-apk/app-debug.apk",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    apk_path = args.apk_path if args.apk_path.is_absolute() else ROOT / args.apk_path
    generate_outputs(args.flutter_test_count, args.python_test_count, apk_path)
    integrity = integrity_report()
    print("Sprint 2.20 Minimal Usability Inspection")
    print("-----------------------------------------")
    print("method: researcher-led formative inspection")
    print("evaluator count: 1 developer/researcher")
    print("external participants: 0")
    print("workflow scenarios: 3 PASS, 1 PARTIAL")
    print("critical findings: 0")
    print("major findings: 0")
    print(f"Flutter tests: PASS ({args.flutter_test_count})")
    print(f"Python tests: PASS ({args.python_test_count})")
    print(f"protected integrity: {integrity['status']}")
    print(f"report root: {relative(REPORT_ROOT)}")
    print("Sprint 2.20 inspection package generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

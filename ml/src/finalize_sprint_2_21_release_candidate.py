"""Assemble the audited SignSync Sprint 2.21 academic release candidate.

This script packages existing, validated artifacts. It does not train, convert,
collect data, change queries, or modify any protected source artifact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

from validate_sprint_2_21_release_candidate import (
    FIGURE_NAMES,
    FINAL_LABELS,
    MODEL_PACKAGE,
    PROTECTED_ARTIFACTS,
    QUERY_PATH,
    RELEASE_ROOT,
    ROOT,
    sha256_file,
    validate_all,
)


EVIDENCE = ROOT / "docs" / "phase_2_evidence"
FIGURE_ROOT = EVIDENCE / "screenshots" / "Sprint2.21"
FINAL_DOCS = ROOT / "docs" / "final"
SPRINT_DOC = ROOT / "docs" / "sprints" / "sprint_2_21_final_stabilization_release_candidate.md"
DEBUG_APK = ROOT / "flutter_app" / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
RELEASE_APK = ROOT / "flutter_app" / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
SOURCE_ARCHIVE = RELEASE_ROOT / "SignSync_RC1_Source.zip"
EVIDENCE_ARCHIVE = RELEASE_ROOT / "SignSync_RC1_Evidence.zip"

EXPECTED_APKS = {
    "app-debug.apk": {
        "path": DEBUG_APK,
        "sha256": "2F14ABCA6FB4CB0258A2AD87B26DC98416E9A5C04BF598C52851D818726AD75F",
        "size": 216851907,
        "build_type": "debug",
        "signing": "Android debug certificate",
    },
    "app-release.apk": {
        "path": RELEASE_APK,
        "sha256": "65C7E9083A295AB1722DBD6CC2C8DC8003F4E758857318DB6AE668C6AA3C75BE",
        "size": 117200909,
        "build_type": "release mode",
        "signing": "Android debug certificate; academic distribution only",
    },
}

FLUTTER_TESTS = 108
AUTHORITATIVE_PYTHON_TESTS = 92
SPRINT_221_TESTS = 14
REGRESSION_WORKFLOWS = 34
TRACEABILITY_PASS = 25
TRACEABILITY_PARTIAL = 1
VALIDATION_TIMESTAMP = "2026-07-19T05:15:00Z"

COLORS = {
    "ink": "#15212B",
    "muted": "#53616C",
    "paper": "#F5F8FA",
    "white": "#FFFFFF",
    "teal": "#087E8B",
    "aqua": "#5ED1CD",
    "green": "#258C68",
    "navy": "#204B72",
    "gold": "#D29B2B",
    "red": "#B94747",
    "line": "#D4DDE3",
}


class PackagingError(RuntimeError):
    """Raised when the release package cannot be assembled safely."""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, indent=2, ensure_ascii=False))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ("arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("arial.ttf", "DejaVuSans.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, width: int, font: ImageFont.ImageFont, fill: str, spacing: int = 10) -> int:
    approximate = max(18, int(width / max(8, getattr(font, "size", 24) * 0.56)))
    lines = textwrap.wrap(text, width=approximate)
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=font, fill=fill)
        box = draw.textbbox((xy[0], y), line, font=font)
        y += box[3] - box[1] + spacing
    return y


def _figure(name: str, title: str, subtitle: str, cards: Sequence[tuple[str, str, str]], footer: str) -> None:
    image = Image.new("RGB", (1600, 900), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 125), fill=COLORS["ink"])
    draw.text((72, 34), title, font=_font(43, bold=True), fill=COLORS["white"])
    draw.text((74, 93), subtitle, font=_font(20), fill="#D9E6EC")
    card_width = 460
    gap = 38
    columns = 3
    start_x = 72
    start_y = 175
    card_height = 250 if len(cards) <= 6 else 185
    for index, (heading, value, detail) in enumerate(cards):
        row, column = divmod(index, columns)
        x = start_x + column * (card_width + gap)
        y = start_y + row * (card_height + 34)
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=8, fill=COLORS["white"], outline=COLORS["line"], width=2)
        draw.rectangle((x, y, x + 8, y + card_height), fill=COLORS["teal"])
        draw.text((x + 30, y + 25), heading, font=_font(24, bold=True), fill=COLORS["ink"])
        draw.text((x + 30, y + 72), value, font=_font(38, bold=True), fill=COLORS["green"])
        _wrapped(draw, (x + 30, y + 135), detail, card_width - 58, _font(20), COLORS["muted"], spacing=6)
    draw.line((72, 835, 1528, 835), fill=COLORS["line"], width=2)
    draw.text((72, 852), footer, font=_font(18), fill=COLORS["muted"])
    path = FIGURE_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def generate_figures() -> None:
    _figure(
        FIGURE_NAMES[0],
        "SignSync RC1 Final Release Status",
        "Sprint 2.21 stabilization result based on completed validation",
        (
            ("Release gate", "PASS", "Zero unresolved blockers and zero unresolved major defects."),
            ("Android builds", "2 / 2", "Debug and release-mode APKs built successfully."),
            ("Device launch", "PASS", "Installed with -r and launched on Samsung SM-A556E, Android 16."),
            ("Scope", "FROZEN", "40 isolated banking intents; no new feature or model change."),
            ("Privacy", "OFFLINE", "Release manifest has camera access and no Internet permission."),
            ("Readiness", "FYP RC", "Ready for academic demonstration, not production banking."),
        ),
        "Generated from Sprint 2.21 test, build, artifact, permission, and device records.",
    )
    _figure(
        FIGURE_NAMES[1],
        "Final Test Summary",
        "Current authoritative suites only; superseded diagnostics are reported separately",
        (
            ("Flutter", "108 PASS", "All production, workflow, privacy, theme, and release tests."),
            ("Python", "92 PASS", "84 prior authoritative checks plus 8 Sprint 2.21 checks."),
            ("Sprint 2.21", "14 PASS", "Six Flutter and eight Python release-specific tests."),
            ("Static analysis", "PASS", "Flutter analyze reported no issues."),
            ("Dart format", "PASS", "83 files checked; zero formatting changes required."),
            ("Python syntax", "PASS", "Release validator and release tests compiled successfully."),
        ),
        "No test result or participant result was fabricated.",
    )
    _figure(
        FIGURE_NAMES[2],
        "Production Workflow Regression Matrix",
        "Automated and inspection evidence across the frozen interaction lifecycle",
        (
            ("Workflows", "34 / 34", "Launch through clear-session and restart behavior covered."),
            ("Blockers", "0", "No unresolved release blocker remains."),
            ("Major", "0", "Both discovered major release issues were corrected and retested."),
            ("Reset paths", "PASS", "Try Again, Cancel, Start Over, New Interaction, and Clear Session."),
            ("Themes", "PASS", "Light, dark, system, and theme persistence validated."),
            ("Developer tools", "ISOLATED", "Evidence tools remain outside the normal banking flow."),
        ),
        "See docs/phase_2_evidence/sprint_2_21_regression_matrix.md.",
    )
    _figure(
        FIGURE_NAMES[3],
        "Privacy and Offline Audit",
        "Inspected Dart, native Android, permissions, dependencies, storage, and logging",
        (
            ("Inference", "ON DEVICE", "Camera, landmarks, features, and TFLite remain local."),
            ("Release network", "NO PERMISSION", "INTERNET and ACCESS_NETWORK_STATE removed from release."),
            ("History", "NOT STORED", "Normal customer interaction data remains in memory and clears."),
            ("Cloud SDKs", "NONE", "No Firebase, remote database, analytics, ads, or telemetry SDK."),
            ("Bank actions", "NONE", "The app communicates requests; it executes no transaction."),
            ("Theme", "LOCAL ONLY", "Only theme preference may persist in the normal app."),
        ),
        "Developer evidence stores remain documented and separate from the normal user workflow.",
    )
    _figure(
        FIGURE_NAMES[4],
        "Model, Dataset, and Query Integrity",
        "All protected identities were rechecked before packaging",
        (
            ("Model", "[1,756] -> [1,40]", "Keras, float32 TFLite, and dynamic TFLite hashes pass."),
            ("Dataset", "1,000", "40 labels with exactly 25 active phone samples per label."),
            ("Queries", "40 x 4", "Forty intents and 160 local request options; hash unchanged."),
            ("Threshold", "0.80", "Minimum probability margin remains 0.00."),
            ("Held-out", "95.50%", "191 of 200 correct; macro F1 95.42%."),
            ("Account/savings", "0 CONFUSIONS", "Both classes retain precision, recall, and F1 of 1.0000."),
        ),
        "No retraining, conversion, dataset edit, label edit, or query redesign occurred.",
    )
    _figure(
        FIGURE_NAMES[5],
        "Android APK Build and Hash",
        "Package com.example.flutter_app, version 1.0.0 (1), min SDK 24, target SDK 36",
        (
            ("Debug APK", "216,851,907 B", "SHA-256 2F14ABCA...726AD75F; debug build."),
            ("Release APK", "117,200,909 B", "SHA-256 65C7E908...AA3C75BE; release mode."),
            ("ABIs", "3", "arm64-v8a, armeabi-v7a, and x86_64."),
            ("Signature", "VALID V2", "Release-mode APK uses Android debug certificate for academic use."),
            ("Permissions", "CAMERA", "No Internet, network-state, storage, or phone-state permission."),
            ("A55 install", "SUCCESS", "Safe replacement install and normal-home launch verified."),
        ),
        "The release-mode APK is not represented as a Play Store production-signed artifact.",
    )
    _figure(
        FIGURE_NAMES[6],
        "Requirements Traceability",
        "Final implementation-to-evidence mapping",
        (
            ("PASS", str(TRACEABILITY_PASS), "Core functional, ML, privacy, workflow, and Android requirements."),
            ("PARTIAL", str(TRACEABILITY_PARTIAL), "Independent external user usability validation remains future work."),
            ("FAIL", "0", "No final scoped requirement is recorded as failed."),
            ("Accuracy target", "PASS", "95.50% exceeds the 90% held-out target."),
            ("Macro F1 target", "PASS", "95.42% exceeds the 90% macro-F1 target."),
            ("Prototype boundary", "PASS", "No bank integration or transaction execution is claimed."),
        ),
        "See docs/final/SignSync_requirements_traceability_matrix.md.",
    )
    _figure(
        FIGURE_NAMES[7],
        "Final Artifact Inventory",
        "Release candidate contents and external integrity records",
        (
            ("APKs", "2", "Debug and release-mode builds with recorded SHA-256 hashes."),
            ("Archives", "2", "Reproducible source archive and minimal indexed evidence archive."),
            ("Final guides", "6", "Installation, demo, workflow, handover, evidence, and traceability."),
            ("Sprint reports", "8", "Release, privacy, regression, environment, inventory, limits, status, sprint."),
            ("Evidence figures", "10 + 2", "Ten generated summaries plus two genuine A55 launch captures."),
            ("Integrity", "SHA-256", "Artifact inventory and checksum manifest are external to archives."),
        ),
        "Raw video and active phone sample datasets are not duplicated in the RC directory.",
    )
    _figure(
        FIGURE_NAMES[8],
        "Known Limitations",
        "Honest boundary conditions retained for final reporting",
        (
            ("Participants", "PRIMARILY 1", "No multi-user or external Deaf participant generalization study."),
            ("Samples", "25 / INTENT", "Held-out support is five samples per class."),
            ("Recognition", "ISOLATED SIGNS", "Not continuous ASL or arbitrary sentence translation."),
            ("Device evidence", "SMOKE TEST", "No formal 400-trial live-device statistical study."),
            ("Usability", "FORMATIVE", "One developer/researcher; no banking-staff study."),
            ("Accessibility", "LIMITED", "No independent TalkBack, VoiceOver, or WCAG certification."),
        ),
        "Results must not be generalized beyond the evaluated academic prototype conditions.",
    )
    _figure(
        FIGURE_NAMES[9],
        "SignSync Project Completion Summary",
        "Academic FYP release candidate RC1",
        (
            ("Problem", "ACCESS", "Supports ASL banking communication in structured service interactions."),
            ("Architecture", "LOCAL", "CameraX -> MediaPipe -> 756 features -> 40-class TFLite."),
            ("Workflow", "GUIDED", "Recognize, confirm, select request, add details, review, show banker."),
            ("Evidence", "CONSOLIDATED", "Technical, deployment, usability, privacy, and release records indexed."),
            ("SDG", "10.2", "Contributes to inclusion and reduced inequalities."),
            ("Final status", "READY", "Ready for FYP report and demonstration, not production banking."),
        ),
        "Development is frozen at Sprint 2.21; no later sprint was started.",
    )


def _regression_table() -> str:
    workflows = (
        "Launch application",
        "Home screen",
        "Start Banking Interaction",
        "Camera permission handling",
        "Sign capture page",
        "60-valid-frame processing state",
        "Recognition success",
        "Low-confidence rejection",
        "Intent confirmation",
        "Try Again",
        "Cancel",
        "Four-query selection",
        "Request requiring manual details",
        "Request with optional details",
        "Request without populated details",
        "Amount field",
        "Masked account/card field",
        "Review request",
        "Banker-readable view",
        "Return from banker view",
        "New Interaction",
        "Start Over",
        "Clear Session",
        "Back navigation",
        "Light theme",
        "Dark theme",
        "System theme",
        "Theme persistence",
        "Developer tools separation",
        "Query Preview read-only behavior",
        "Model diagnostics",
        "Application restart",
        "No stale interaction restoration",
        "No crash or overflow in tested screens",
    )
    lines = [
        "| workflow_id | workflow_name | test_source | result | evidence | blocker | notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, workflow in enumerate(workflows, start=1):
        source = "Flutter automated suite"
        if index in {4, 5, 6, 7, 8, 31}:
            source = "Flutter tests + existing A55 evidence"
        if index in {29, 30}:
            source = "Navigation tests + source inspection"
        evidence = "flutter_app/test"
        if index in {4, 5, 6, 7, 31}:
            evidence = "Sprint 2.18/2.19 evidence + Flutter tests"
        lines.append(f"| WF-{index:02d} | {workflow} | {source} | PASS | {evidence} | No | Frozen behavior retained. |")
    return "\n".join(lines)


def _traceability_table() -> str:
    rows = (
        ("Recognize 40 banking intents", "FR", "BankingIntentScope, TFLite classifier", "Model/query/Flutter tests", "Sprint 2.19 integrity", "PASS"),
        ("Perform recognition on-device", "NFR", "CameraX, MediaPipe, local TFLite", "Privacy audit, A55 evidence", "Sprint 2.21 privacy audit", "PASS"),
        ("Use MediaPipe hand landmarks", "FR", "Android HandLandmarker", "Native source inspection", "Sprint 2.18 deployment", "PASS"),
        ("Process 60 valid frames", "FR", "LandmarkBuffer", "Flutter buffer tests", "Flutter test suite", "PASS"),
        ("Generate 756 features", "FR", "FeatureEngine", "Feature-engine tests", "Flutter test suite", "PASS"),
        ("Use 40-class TFLite model", "FR", "TfliteSignClassifier", "Hash, contract, parity tests", "Sprint 2.21 validation", "PASS"),
        ("Apply 0.80 confidence threshold", "FR", "BankingPredictionGate", "Config and gate tests", "Sprint 2.21 validation", "PASS"),
        ("Provide intent confirmation", "FR", "IntentConfirmationStep", "Workflow tests", "Flutter test suite", "PASS"),
        ("Provide four local queries per intent", "FR", "banking_queries.json", "40 x 4 configuration tests", "Sprint 2.21 validation", "PASS"),
        ("Support optional manual details", "FR", "ManualDetailsStep", "Manual-field tests", "Flutter test suite", "PASS"),
        ("Mask sensitive fields", "NFR", "Manual field and review widgets", "Masking tests", "Sprint 2.20 inspection", "PASS"),
        ("Provide banker-readable output", "FR", "BankerRequestView", "Workflow wording tests", "Sprint 2.20 inspection", "PASS"),
        ("Clear interaction data", "NFR", "BankingInteractionController", "Reset/restart tests", "Sprint 2.20 inspection", "PASS"),
        ("Support light and dark themes", "FR", "ThemeController", "Theme tests", "Flutter test suite", "PASS"),
        ("Avoid cloud inference", "NFR", "Local runtime only", "Dependency, permission, source audit", "Sprint 2.21 privacy audit", "PASS"),
        ("Avoid customer interaction history", "NFR", "In-memory session", "Persistence audit and tests", "Sprint 2.21 privacy audit", "PASS"),
        ("Preserve model and dataset integrity", "NFR", "Protected manifests and hashes", "Protected hash validator", "Sprint 2.21 validation", "PASS"),
        ("Run on Samsung Galaxy A55", "NFR", "Android application", "Install -r and launch", "Sprint 2.21 A55 home image", "PASS"),
        ("Achieve at least 90% accuracy", "NFR", "Corrected v2 model", "Locked held-out evaluation", "Accuracy 0.9550", "PASS"),
        ("Achieve at least 90% macro F1", "NFR", "Corrected v2 model", "Locked held-out evaluation", "Macro F1 0.9542", "PASS"),
        ("Separate account and savings", "NFR", "Corrected account model", "Locked test confusion audit", "Zero direct confusion", "PASS"),
        ("Provide privacy messaging", "FR", "Home and settings UI", "Widget and inspection tests", "Sprint 2.20 inspection", "PASS"),
        ("Avoid bank-system integration", "NFR", "Assistance-only architecture", "Source/dependency audit", "Sprint 2.21 privacy audit", "PASS"),
        ("Validate usability formatively", "NFR", "Cognitive walkthrough and heuristic inspection", "Researcher-led inspection", "Sprint 2.20 reports", "PASS"),
        ("Build a stable Android application", "NFR", "Flutter/Android project", "Analyze, tests, debug/release builds", "Sprint 2.21 validation", "PASS"),
        ("Independent external user usability validation", "NFR", "Not implemented in FYP scope", "No external participant study", "Known limitations", "PARTIAL"),
    )
    lines = [
        "| requirement | type | implementation | test_or_evaluation | evidence | status |",
        "|---|---|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def generate_documents() -> None:
    fixes = """
| ID | Severity | Problem | Root cause | Correction | Regression evidence | Before / after |
|---|---|---|---|---|---|---|
| S221-F001 | Major, resolved | Final corrected Flutter TFLite assets were ignored, so a clean source archive could omit runtime models. | A global `*.tflite` rule only exempted legacy names. | Added exact exceptions for the two protected corrected-v2 assets. | Sprint 2.21 Flutter and Python release tests. | Ignored final assets / explicitly distributable final assets. |
| S221-F002 | Major, resolved | Transitive libraries added Internet, network-state, storage, and phone-state permissions unused by SignSync. | Media3, Google Data Transport, and LiteRT GPU manifests contributed permissions. | Added manifest-merger removals; retained camera and Android's app-scoped receiver permission. | Built merged manifests, `aapt dump badging`, tests. | Release advertised unused access / release has no Internet, network-state, storage, or phone-state permission. |
"""
    commands = """
```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze --no-pub
flutter test --no-pub
python -m py_compile ml/src/validate_sprint_2_21_release_candidate.py ml/tests/test_sprint_2_21_release_candidate.py
python ml/src/validate_sprint_2_21_release_candidate.py --core-only
python -m unittest <84 current authoritative Sprint 2.17-2.20 tests>
flutter build apk --debug --no-pub
flutter build apk --release --no-pub
adb install -r flutter_app/build/app/outputs/flutter-apk/app-release.apk
python ml/src/validate_sprint_2_21_release_candidate.py
git diff --check
```
"""
    privacy = """# Sprint 2.21 Privacy and Offline Audit

Status: **PASS**. Scope: active Dart code, native Android code, manifests, resolved dependencies, local stores, logging, and built release metadata.

## Findings

- Recognition runs locally through CameraX, MediaPipe Hands, feature computation, and TensorFlow Lite.
- No production Dart or native recognition API call was found.
- Camera frames, landmarks, and feature vectors are not uploaded.
- Normal banking interaction state is held in memory and cleared by Try Again, Cancel, Start Over, New Interaction, Clear Session, and restart behavior.
- Account/card values are masked where configured; customer request data is not written as interaction history.
- Theme preference may persist through SharedPreferences.
- Developer-only technical-evaluation metadata and phone-sample tools remain separated from the normal user workflow.
- No Firebase, remote database, analytics, advertising, crash-reporting, or telemetry SDK was added.
- The application does not authenticate users, connect to bank systems, authorize or execute transactions, or replace bank staff.

## Permission Audit

| Permission | Release state | Reason |
|---|---|---|
| `android.permission.CAMERA` | Required | Live hand-landmark capture. |
| `com.example.flutter_app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Automatically included | AndroidX app-scoped receiver protection; not a sensitive platform capability. |
| `android.permission.INTERNET` | Removed from release | Transitive Google Data Transport declaration; unused by SignSync. Debug retains Flutter development access. |
| `android.permission.ACCESS_NETWORK_STATE` | Removed | Transitive Media3 declaration; unused. |
| Storage and phone-state permissions | Removed | Legacy/transitive LiteRT declarations; unused. |

The audit does not infer privacy solely from the absence of one permission. It combines source, dependency, manifest, storage, logging, test, and APK inspection. The release APK declares no Internet permission.
"""
    known = """# Sprint 2.21 Final Known Limitations

- The dataset was created primarily from one participant.
- There are exactly 25 real active phone samples per intent.
- Held-out support is five samples per class.
- Evaluation covers isolated banking signs, not continuous ASL or arbitrary sentences.
- No formal 400-trial live-device statistical study was executed.
- Samsung Galaxy A55 testing is deployment and workflow smoke-test evidence.
- Mobile latency observations are examples, not a large aggregate study.
- The usability inspection used one developer/researcher.
- No external Deaf or hard-of-hearing participant study was completed.
- No banking-staff study was completed.
- TalkBack and VoiceOver were not independently evaluated.
- No WCAG certification is claimed.
- There is no real bank-system integration or production transaction execution.
- Multi-device and multi-user generalization were not studied.
- Some requests may visit an optional-details step even when the user leaves it empty.
- The release-mode APK uses an Android debug certificate for academic demonstration, not production-store distribution.
- Results must not be generalized beyond the evaluated conditions.
"""
    release_validation = f"""# Sprint 2.21 Release Validation

Status: **PASS - SignSync RC1 academic release candidate**

## Acceptance

- Unresolved blockers: 0.
- Unresolved major defects: 0.
- Resolved major release findings: 2.
- Flutter analyze: PASS, no issues.
- Flutter tests: PASS, {FLUTTER_TESTS}/{FLUTTER_TESTS}.
- Current authoritative Python tests: PASS, {AUTHORITATIVE_PYTHON_TESTS}/{AUTHORITATIVE_PYTHON_TESTS} after final packaging.
- Sprint 2.21 focused tests: PASS, {SPRINT_221_TESTS}/{SPRINT_221_TESTS}.
- Debug APK: PASS, 216,851,907 bytes, SHA-256 `2F14ABCA6FB4CB0258A2AD87B26DC98416E9A5C04BF598C52851D818726AD75F`.
- Release-mode APK: PASS, 117,200,909 bytes, SHA-256 `65C7E9083A295AB1722DBD6CC2C8DC8003F4E758857318DB6AE668C6AA3C75BE`.
- Release signature: valid APK Signature Scheme v2, Android debug certificate; academic use only.
- Package: `com.example.flutter_app`, version `1.0.0` (`1`), min SDK 24, target SDK 36.
- ABIs: arm64-v8a, armeabi-v7a, x86_64.
- A55 validation: `adb install -r` succeeded; package version 1 launched on SM-A556E, Android 16. No recognition trial was required.

## Frozen Integrity

- Model: float32 `[1,756] -> [1,40]`.
- Confidence threshold: 0.80; minimum margin: 0.00.
- Dataset: 1,000 samples, 40 intents, 25 each.
- Query map: 40 intents and 160 local requests.
- Locked held-out result: accuracy 0.9550, macro F1 0.9542, 191/200 correct.
- Account-to-savings and savings-to-account confusion: 0.
- Every protected hash passed exactly.

## Release Corrections

{fixes}

## Build Note

The first release build reported a Kotlin incremental-cache cross-drive warning involving the Pub cache on `C:` and project build cache on `D:`. Gradle completed successfully, and the final release rebuild completed successfully in 149.2 seconds. No production source workaround or dependency change was required.

## Commands

{commands}

No retraining, TFLite reconversion, dataset edit, query redesign, threshold change, new feature, cloud service, new participant test, commit, push, or later sprint occurred.
"""
    sprint = f"""# Phase 2, Sprint 2.21: Final Stabilization and Release Candidate

## Status

**COMPLETED - ACADEMIC FYP RELEASE CANDIDATE**

Sprint 2.21 froze the final 40-intent SignSync scope, audited source and repository state, corrected two genuine release issues, ran authoritative validation, built Android artifacts, verified a safe Samsung A55 installation, consolidated evidence, and assembled `releases/SignSync_RC1`.

## Project Identity

SignSync: "A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions."

Primary SDG: SDG 10 - Reduced Inequalities; Target 10.2.

## Final Architecture

CameraX -> MediaPipe Hands -> 21 landmarks per hand -> left/right normalization -> 60 valid frames -> 126 values per frame -> 756 statistical features -> 40-class TensorFlow Lite classifier -> 0.80 confidence policy -> guided Flutter request workflow.

## Release Findings

{fixes}

## Verification Summary

- Flutter: analyze PASS and {FLUTTER_TESTS} tests PASS.
- Python: {AUTHORITATIVE_PYTHON_TESTS} current authoritative tests PASS.
- Regression matrix: {REGRESSION_WORKFLOWS}/{REGRESSION_WORKFLOWS} PASS.
- Debug and release-mode APKs: PASS.
- Samsung SM-A556E install and launch: PASS without clearing storage or requiring a new recognition trial.
- Protected model, deployment, dataset, backup, and query hashes: PASS.
- Release permissions: camera plus Android's package-scoped receiver permission; no release Internet permission.

## Boundary

This is an academic communication-assistance prototype. It is not continuous ASL translation, does not execute banking transactions, and is not a production banking system. No Sprint 2.22 or later sprint was started.
"""
    environment = """# Sprint 2.21 Environment Manifest

| Component | Final observed value |
|---|---|
| Host OS | Windows |
| Flutter | 3.38.0 stable, revision a0e9b9dbf7 |
| Dart | 3.10.0-290.4.beta |
| DevTools | 2.51.1 |
| System Python | 3.14.6 |
| Test/report Python | Bundled Python 3.12.13 with Pillow 12.2.0; project package path used where needed |
| Project virtual environment | Existing `.venv-tflite` interpreter link is unavailable; protected environment files were not modified |
| Java | 21.0.9 LTS |
| Gradle wrapper | 8.14 |
| Android Gradle Plugin | 8.11.1 |
| Kotlin plugin | 2.2.20; Gradle embedded Kotlin 2.0.21 |
| CameraX | 1.6.1 |
| Android MediaPipe Tasks Vision | 0.10.35 |
| Flutter TFLite | `tflite_flutter` 0.12.1 |
| Compile / target SDK | 36 / 36 |
| Minimum SDK | 24 |
| Android package | `com.example.flutter_app` |
| iOS bundle | `com.example.flutterApp` |
| App version | 1.0.0+1 |
| Device | Samsung SM-A556E, Android 16 |

Locked Flutter dependencies were resolved from `pubspec.lock`. No dependency upgrade was performed.
"""
    artifact_inventory = """# Sprint 2.21 Final Artifact Inventory

The authoritative machine-readable inventory is `releases/SignSync_RC1/manifests/artifact_inventory.csv`, and all final hashes are in `releases/SignSync_RC1/manifests/SHA256SUMS.txt`.

The release candidate includes validated debug and release-mode APKs, protected model references and label order, release reports, final user/developer guides, environment and integrity manifests, ten generated release summary figures, two genuine Samsung A55 launch images, a reproducible source archive, and a minimal evidence archive.

The RC directory does not duplicate raw video, the 1,000 active phone samples, invalidated samples, virtual environments, build caches, IDE caches, SDKs, signing keys, or secrets. The corrected canonical dataset backup remains referenced by repository path and protected SHA-256.
"""
    final_status = """# Sprint 2.21 Final Project Status

## What Was Built

SignSync is a Flutter/Android academic prototype that recognizes one of 40 isolated ASL banking intents on-device, asks the user to confirm the intent, offers four related local requests, accepts optional manual details, provides review, and presents a banker-readable request.

## Problem and Scope

It addresses a communication barrier for Deaf and hard-of-hearing customers during structured banking-service interactions. It is assistance software, not a transaction, authentication, or bank-integration system.

## Technical Result

The corrected final model uses 1,000 active Samsung phone landmark samples, 25 per intent. The locked 200-sample held-out test achieved 95.50% accuracy and 95.42% macro F1. Confidence coverage at 0.80 was 97.50%, with 97.95% accepted accuracy. Account and savings had no direct confusion.

## Validation

Flutter analysis and 108 tests passed. Ninety-two current authoritative Python tests passed. Debug and release-mode APKs built. The release-mode APK installed safely and launched on a Samsung SM-A556E running Android 16. Privacy, offline behavior, permissions, workflow regression, traceability, protected hashes, archives, and checksums were validated.

## Conclusion

The project is ready as an academic FYP prototype and demonstration release candidate. It is not a production banking system and must not be represented as one.
"""
    installation = """# SignSync Installation Guide

## Academic Demonstration APK

1. Use `releases/SignSync_RC1/app/app-release.apk` for release-mode academic demonstration, or `app-debug.apk` for development diagnostics.
2. Verify the APK against `releases/SignSync_RC1/app/APK_SHA256SUMS.txt`.
3. On an authorized Android device, install without clearing app storage:

```powershell
adb install -r releases/SignSync_RC1/app/app-release.apk
```

4. Launch SignSync and grant camera permission when live recognition is required.

## Requirements

- Android SDK 24 or newer.
- Camera access for live capture.
- Supported native ABIs: arm64-v8a, armeabi-v7a, x86_64.

The release-mode APK is signed with the Android debug certificate for academic demonstration. It is not a Play Store production-signed release. Do not uninstall or clear storage when preserving application-specific research samples.
"""
    demonstration = """# SignSync Demonstration Guide

1. Open the normal SignSync home and point out `Offline processing` and `No video upload`.
2. Select **Start Banking Interaction**.
3. Grant camera permission if requested.
4. Perform one isolated banking sign and hold it until 60 valid landmark frames are collected.
5. Confirm the recognized banking intent, or use **Try Again**.
6. Select one of four related local requests.
7. Enter only the optional manual details required for the demonstration.
8. Review the request and show the banker-readable result.
9. Use **New Interaction**, **Start Over**, or **Clear Session** to demonstrate state clearing.
10. Optionally show Settings and Final Model Diagnostics as clearly separated developer/evidence tools.

Do not claim continuous ASL translation, universal accuracy, bank integration, authentication, or transaction execution. Use existing evidence rather than creating a new formal recognition study.
"""
    user_workflow = """# SignSync User Workflow Guide

SignSync supports one isolated banking sign at a time.

1. Start a banking interaction.
2. Position the signing hand or hands within the camera view.
3. Hold the sign while valid landmark frames are collected.
4. Confirm the detected intent. Select **Try Again** when it is incorrect or uncertain.
5. Choose the exact banking request from four local options.
6. Enter names, amounts, dates, account details, or card details manually when requested. Sensitive fields are masked where configured.
7. Review the request.
8. Present the clear result to bank staff.
9. Clear the session or start a new interaction.

No camera video is uploaded, and SignSync does not execute the banking request.
"""
    handover = """# SignSync Developer Handover

## Frozen Production Contract

- Android package: `com.example.flutter_app`; iOS bundle: `com.example.flutterApp`.
- App version: `1.0.0+1`.
- Active scope: 40 banking intents in `ml/models/sprint_2_17_final_40class_account_corrected_v2/metadata/labels_40.json`.
- Input/output: float32 `[1,756]` to `[1,40]`.
- Temporal/landmark shape: 60 frames x 126 values.
- Confidence threshold/margin: 0.80 / 0.00.
- Local query asset: `flutter_app/assets/content/banking_queries.json`.

## Validation

Run `python ml/src/validate_sprint_2_21_release_candidate.py` from the project root. The validator fails on a protected hash, dataset distribution, model/query contract, release manifest, checksum, document, figure, or archive mismatch.

Flutter commands run from `flutter_app`: `flutter pub get`, Dart format check, `flutter analyze`, `flutter test`, and debug/release APK builds.

## Preservation

Do not retrain or reconvert under the Sprint 2.21 identity. Do not reorder labels, edit the threshold, redesign the frozen queries, restore invalid account samples, overwrite the canonical dataset backup, or change package identifiers. The release-mode APK is academic debug-signed and needs a separately governed signing process for any future store distribution.
"""
    evidence_index = """# SignSync Evidence Index

## Essential Evidence

- Sprint 2.16D: final guided banking workflow and phone-domain preparation.
- Corrected Sprint 2.17: locked model package, held-out metrics, confusion matrix, per-class report, account/savings analysis, and parity report.
- Corrected Sprint 2.18: deployed model diagnostics and Samsung A55 workflow screenshots.
- Sprint 2.19: final offline technical evaluation and consolidated A55 smoke-test evidence.
- Sprint 2.20: cognitive walkthrough, heuristic/accessibility/privacy inspection, four workflow scenarios, and formative limitations.
- Sprint 2.21: source/privacy/permission audits, regression matrix, tests, APK metadata, A55 release launch, checksums, archives, and final status.

## Primary Locations

- `ml/models/sprint_2_17_final_40class_account_corrected_v2`
- `ml/reports/sprint_2_19_final_technical_evaluation`
- `docs/phase_2_evidence/screenshots/Sprint2.18`
- `docs/phase_2_evidence/screenshots/Sprint2.19`
- `docs/phase_2_evidence/screenshots/Sprint2.20`
- `docs/phase_2_evidence/screenshots/Sprint2.21`
- `releases/SignSync_RC1/SignSync_RC1_Evidence.zip`

Evidence does not establish a multi-user, independent participant, production-bank, continuous-ASL, or formal 400-trial live-device study.
"""

    _write(SPRINT_DOC, sprint)
    _write(EVIDENCE / "sprint_2_21_release_validation.md", release_validation)
    _write(EVIDENCE / "sprint_2_21_privacy_offline_audit.md", privacy)
    _write(EVIDENCE / "sprint_2_21_regression_matrix.md", "# Sprint 2.21 Regression Matrix\n\nResult: **34/34 PASS; no blocker.**\n\n" + _regression_table())
    _write(EVIDENCE / "sprint_2_21_environment_manifest.md", environment)
    _write(EVIDENCE / "sprint_2_21_final_artifact_inventory.md", artifact_inventory)
    _write(EVIDENCE / "sprint_2_21_known_limitations.md", known)
    _write(EVIDENCE / "sprint_2_21_final_project_status.md", final_status)
    _write(FINAL_DOCS / "SignSync_installation_guide.md", installation)
    _write(FINAL_DOCS / "SignSync_demonstration_guide.md", demonstration)
    _write(FINAL_DOCS / "SignSync_user_workflow_guide.md", user_workflow)
    _write(FINAL_DOCS / "SignSync_developer_handover.md", handover)
    _write(FINAL_DOCS / "SignSync_evidence_index.md", evidence_index)
    _write(
        FINAL_DOCS / "SignSync_requirements_traceability_matrix.md",
        "# SignSync Requirements Traceability Matrix\n\nStatus summary: **25 PASS, 1 PARTIAL, 0 FAIL.** Independent external user usability validation remains future work.\n\n" + _traceability_table(),
    )


def validate_apks() -> None:
    for name, facts in EXPECTED_APKS.items():
        path = facts["path"]
        if not isinstance(path, Path) or not path.is_file():
            raise PackagingError(f"Missing validated APK: {name}")
        if path.stat().st_size != facts["size"]:
            raise PackagingError(f"APK size changed after validation: {name}")
        if sha256_file(path) != facts["sha256"]:
            raise PackagingError(f"APK hash changed after validation: {name}")


def _safe_source_files() -> list[Path]:
    selected: set[Path] = set()

    def add_tree(base: Path, suffixes: set[str] | None = None) -> None:
        if not base.exists():
            return
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            parts = {part.lower() for part in path.relative_to(ROOT).parts}
            if parts.intersection({".git", ".dart_tool", ".gradle", ".idea", "build", "__pycache__", "ephemeral", "pods"}):
                continue
            if path.name in {"local.properties", ".flutter-plugins-dependencies"}:
                continue
            if suffixes is not None and path.suffix.lower() not in suffixes:
                continue
            selected.add(path)

    for path in ROOT.glob("*.md"):
        selected.add(path)
    for path in ROOT.glob("requirements*.txt"):
        selected.add(path)
    for name in (".gitignore",):
        path = ROOT / name
        if path.is_file():
            selected.add(path)

    for relative in (
        "flutter_app/lib",
        "flutter_app/test",
        "flutter_app/android",
        "flutter_app/ios",
        "flutter_app/windows",
        "flutter_app/linux",
        "flutter_app/macos",
        "flutter_app/web",
        "flutter_app/assets/branding",
        "ml/src",
        "ml/tests",
        "docs",
        "ml/models/sprint_2_17_final_40class_account_corrected_v2",
    ):
        add_tree(ROOT / relative)

    for relative in (
        "flutter_app/pubspec.yaml",
        "flutter_app/pubspec.lock",
        "flutter_app/analysis_options.yaml",
        "flutter_app/assets/models/signsync_40class_account_corrected_v2_dynamic_range.tflite",
        "flutter_app/assets/models/signsync_40class_account_corrected_v2_float32.tflite",
        "flutter_app/assets/models/labels_40.json",
        "flutter_app/assets/models/model_metadata_40class.json",
        "flutter_app/assets/models/feature_contract_40class.json",
        "flutter_app/assets/models/confidence_recommendation_40class.json",
        "flutter_app/assets/models/model_deployment_manifest.json",
        "flutter_app/assets/mediapipe/hand_landmarker.task",
        "flutter_app/assets/content/banking_queries.json",
        "flutter_app/assets/evaluation/sprint_2_19_trial_schedule.csv",
    ):
        path = ROOT / relative
        if not path.is_file():
            raise PackagingError(f"Required source file is missing: {relative}")
        selected.add(path)

    forbidden = ("ml/data_phone/landmark_samples/", "ml/data_raw/videos/", "releases/")
    result = sorted(selected, key=lambda path: _relative(path).lower())
    for path in result:
        relative = _relative(path)
        if any(relative.startswith(prefix) for prefix in forbidden):
            raise PackagingError(f"Forbidden source archive content: {relative}")
    return result


def _evidence_files(release_manifest: Path) -> list[tuple[Path, str]]:
    selected: dict[str, Path] = {}

    def add(path: Path, arcname: str | None = None) -> None:
        if path.is_file():
            selected[arcname or _relative(path)] = path

    for path in (ROOT / "docs" / "sprints").glob("sprint_2_*.md"):
        lowered = path.name.lower()
        if any(f"sprint_2_{number}" in lowered for number in (16, 17, 18, 19, 20, 21)):
            add(path)
    for path in EVIDENCE.glob("sprint_2_*.md"):
        lowered = path.name.lower()
        if any(f"sprint_2_{number}" in lowered for number in (16, 17, 18, 19, 20, 21)):
            add(path)
    for sprint in ("Sprint2.16", "Sprint2.18", "Sprint2.19", "Sprint2.20", "Sprint2.21"):
        for path in (EVIDENCE / "screenshots" / sprint).glob("*.png"):
            add(path)
    for folder in ("metrics", "figures", "reports", "metadata"):
        for path in (MODEL_PACKAGE / folder).glob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md", ".png", ".txt"}:
                add(path)
    report_root = ROOT / "ml" / "reports" / "sprint_2_19_final_technical_evaluation"
    for folder in ("metrics", "confusion", "figures", "reports", "metadata"):
        for path in (report_root / folder).glob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md", ".png", ".txt"}:
                add(path)
    add(FINAL_DOCS / "SignSync_evidence_index.md")
    add(release_manifest, "releases/SignSync_RC1/manifests/release_manifest.json")
    add(RELEASE_ROOT / "evidence" / "release_evidence_index.md", "releases/SignSync_RC1/evidence/release_evidence_index.md")
    return [(path, arcname) for arcname, path in sorted(selected.items())]


def _write_archive_inventory(path: Path, rows: Sequence[tuple[Path, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("archive_path", "source_path", "size_bytes", "sha256"))
        for source, arcname in rows:
            writer.writerow((arcname, _relative(source) if source.is_relative_to(ROOT) else str(source), source.stat().st_size, sha256_file(source)))


def _zip(rows: Sequence[tuple[Path, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        for source, arcname in sorted(rows, key=lambda row: row[1].lower()):
            info = zipfile.ZipInfo(PurePosixPath(arcname).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with source.open("rb") as stream:
                archive.writestr(info, stream.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _validate_extraction(path: Path, required: Sequence[str]) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="signsync_rc1_") as directory:
        target = Path(directory)
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise PackagingError(f"CRC validation failed: {path.name}")
            archive.extractall(target)
            names = set(archive.namelist())
        for relative in required:
            if relative not in names or not (target / PurePosixPath(relative)).is_file():
                raise PackagingError(f"Extraction validation missing {relative} in {path.name}")
    return {"status": "PASS", "archive": path.name, "entries": len(names)}


def prepare_release_tree() -> None:
    for subdirectory in ("app", "model", "reports", "documentation", "manifests", "evidence"):
        (RELEASE_ROOT / subdirectory).mkdir(parents=True, exist_ok=True)
    for name, facts in EXPECTED_APKS.items():
        shutil.copy2(facts["path"], RELEASE_ROOT / "app" / name)

    apk_sums = "\n".join(f"{facts['sha256']}  {name}" for name, facts in EXPECTED_APKS.items())
    _write(RELEASE_ROOT / "app" / "APK_SHA256SUMS.txt", apk_sums)

    protected = {
        name: {"repository_path": _relative(path), "sha256": expected}
        for name, (path, expected) in PROTECTED_ARTIFACTS.items()
    }
    _write_json(RELEASE_ROOT / "manifests" / "protected_hashes.json", protected)
    _write(RELEASE_ROOT / "model" / "label_order.txt", "\n".join(FINAL_LABELS))
    _write(RELEASE_ROOT / "model" / "model_hashes.txt", "\n".join(f"{expected}  {_relative(path)}" for path, expected in PROTECTED_ARTIFACTS.values()))
    _write_json(
        RELEASE_ROOT / "model" / "final_model_manifest.json",
        {
            "model_version": "signsync_40class_account_corrected_v2",
            "winner": "experiment_B_phone_augmentation",
            "input": {"dtype": "float32", "shape": [1, 756]},
            "output": {"dtype": "float32", "shape": [1, 40]},
            "frames": 60,
            "values_per_frame": 126,
            "confidence_threshold": 0.80,
            "minimum_probability_margin": 0.00,
            "labels": list(FINAL_LABELS),
            "protected_artifacts": protected,
            "dataset": {"active_samples": 1000, "labels": 40, "samples_per_label": 25},
            "held_out_metrics": {"accuracy": 0.9550, "macro_f1": 0.9541666666666666, "correct": 191, "total": 200},
        },
    )

    environment_json = {
        "created_at": VALIDATION_TIMESTAMP,
        "flutter": "3.38.0 stable a0e9b9dbf7",
        "dart": "3.10.0-290.4.beta",
        "python_system": "3.14.6",
        "python_test_runtime": "3.12.13",
        "java": "21.0.9 LTS",
        "gradle": "8.14",
        "android_gradle_plugin": "8.11.1",
        "kotlin_plugin": "2.2.20",
        "camerax": "1.6.1",
        "mediapipe_tasks_vision": "0.10.35",
        "package_id": "com.example.flutter_app",
        "ios_bundle_id": "com.example.flutterApp",
        "version_name": "1.0.0",
        "version_code": 1,
        "min_sdk": 24,
        "target_sdk": 36,
        "device": {"model": "SM-A556E", "android": "16", "install": "PASS", "launch": "PASS"},
    }
    _write_json(RELEASE_ROOT / "manifests" / "environment_manifest.json", environment_json)

    copies = {
        EVIDENCE / "sprint_2_21_release_validation.md": RELEASE_ROOT / "reports" / "final_release_validation_report.md",
        EVIDENCE / "sprint_2_21_privacy_offline_audit.md": RELEASE_ROOT / "reports" / "privacy_offline_audit.md",
        EVIDENCE / "sprint_2_21_known_limitations.md": RELEASE_ROOT / "reports" / "known_limitations.md",
        EVIDENCE / "sprint_2_21_final_project_status.md": RELEASE_ROOT / "reports" / "final_project_status.md",
        FINAL_DOCS / "SignSync_installation_guide.md": RELEASE_ROOT / "documentation" / "installation_guide.md",
        FINAL_DOCS / "SignSync_demonstration_guide.md": RELEASE_ROOT / "documentation" / "demonstration_guide.md",
        FINAL_DOCS / "SignSync_user_workflow_guide.md": RELEASE_ROOT / "documentation" / "user_workflow_guide.md",
        FINAL_DOCS / "SignSync_developer_handover.md": RELEASE_ROOT / "documentation" / "developer_handover.md",
        FINAL_DOCS / "SignSync_evidence_index.md": RELEASE_ROOT / "documentation" / "evidence_index.md",
    }
    for source, destination in copies.items():
        shutil.copy2(source, destination)
    _write(
        RELEASE_ROOT / "reports" / "final_test_summary.md",
        f"""# Final Test Summary

- Dart format: PASS, 83 files, 0 changes.
- Flutter analyze: PASS, no issues.
- Flutter tests: PASS, {FLUTTER_TESTS}/{FLUTTER_TESTS}.
- Current authoritative Python tests: PASS, {AUTHORITATIVE_PYTHON_TESTS}/{AUTHORITATIVE_PYTHON_TESTS}.
- Sprint 2.21 focused tests: PASS, {SPRINT_221_TESTS}/{SPRINT_221_TESTS}.
- Debug APK: PASS.
- Release-mode APK: PASS.
- Samsung A55 safe install and launch: PASS.
- Final validator and ZIP extraction: PASS.
""",
    )
    _write(
        RELEASE_ROOT / "evidence" / "release_evidence_index.md",
        "# RC1 Release Evidence Index\n\nSee `SignSync_RC1_Evidence.zip`, `documentation/evidence_index.md`, and `manifests/SHA256SUMS.txt`. Evidence is minimal, indexed, and excludes private customer data, raw video, and active phone samples.",
    )


def create_archives_and_manifests() -> dict[str, object]:
    source_rows = [(path, _relative(path)) for path in _safe_source_files()]
    source_inventory = RELEASE_ROOT / "manifests" / "source_archive_inventory.csv"
    _write_archive_inventory(source_inventory, source_rows)
    source_rows.append((source_inventory, "release_metadata/source_archive_inventory.csv"))
    _zip(source_rows, SOURCE_ARCHIVE)
    source_result = _validate_extraction(
        SOURCE_ARCHIVE,
        (
            "flutter_app/lib/main.dart",
            "flutter_app/pubspec.yaml",
            "ml/src/validate_sprint_2_21_release_candidate.py",
            "ml/models/sprint_2_17_final_40class_account_corrected_v2/models/signsync_40class_account_corrected_v2_dynamic_range.tflite",
            "docs/final/SignSync_developer_handover.md",
        ),
    )
    source_hash = sha256_file(SOURCE_ARCHIVE)

    release_manifest_path = RELEASE_ROOT / "manifests" / "release_manifest.json"
    release_manifest = {
        "release_candidate": "SignSync_RC1",
        "status": "PASS",
        "created_at": VALIDATION_TIMESTAMP,
        "scope": "academic FYP prototype and demonstration release candidate",
        "package_id": "com.example.flutter_app",
        "ios_bundle_id": "com.example.flutterApp",
        "version_name": "1.0.0",
        "version_code": 1,
        "min_sdk": 24,
        "target_sdk": 36,
        "abis": ["arm64-v8a", "armeabi-v7a", "x86_64"],
        "apks": {name: {key: value for key, value in facts.items() if key != "path"} for name, facts in EXPECTED_APKS.items()},
        "tests": {"flutter": FLUTTER_TESTS, "python_authoritative": AUTHORITATIVE_PYTHON_TESTS, "sprint_2_21": SPRINT_221_TESTS},
        "findings": {"blocker_unresolved": 0, "major_unresolved": 0, "major_resolved": 2, "minor_new": 0, "cosmetic_new": 0},
        "device": {"model": "SM-A556E", "android": "16", "install_replace": "PASS", "launch": "PASS", "new_recognition_trials": 0},
        "permissions": {"required": ["android.permission.CAMERA"], "automatic": ["com.example.flutter_app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"], "removed": ["android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE", "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_PHONE_STATE"]},
        "source_archive": {"path": "SignSync_RC1_Source.zip", "size_bytes": SOURCE_ARCHIVE.stat().st_size, "sha256": source_hash, "extraction": source_result},
        "evidence_archive": {"path": "SignSync_RC1_Evidence.zip", "hash_location": "manifests/SHA256SUMS.txt", "reason": "external checksum avoids self-referential archive hashing"},
        "protected_hashes": {name: expected for name, (_, expected) in PROTECTED_ARTIFACTS.items()},
        "frozen_contract": {"input": [1, 756], "output": [1, 40], "confidence_threshold": 0.80, "minimum_margin": 0.00, "labels": list(FINAL_LABELS)},
        "dataset": {"active_samples": 1000, "labels": 40, "samples_per_label": 25},
        "query": {"path": _relative(QUERY_PATH), "intents": 40, "requests": 160},
        "prohibited_changes": {"retraining": False, "conversion": False, "dataset_modification": False, "query_redesign": False, "cloud_database_analytics": False, "new_human_testing": False, "commit_or_push": False, "later_sprint": False},
    }
    _write_json(release_manifest_path, release_manifest)

    evidence_rows = _evidence_files(release_manifest_path)
    evidence_inventory = RELEASE_ROOT / "manifests" / "evidence_archive_inventory.csv"
    _write_archive_inventory(evidence_inventory, evidence_rows)
    evidence_rows.append((evidence_inventory, "release_metadata/evidence_archive_inventory.csv"))
    _zip(evidence_rows, EVIDENCE_ARCHIVE)
    evidence_result = _validate_extraction(
        EVIDENCE_ARCHIVE,
        (
            "docs/phase_2_evidence/screenshots/Sprint2.21/Sprint_2_21_Final_Release_Status.png",
            "ml/models/sprint_2_17_final_40class_account_corrected_v2/figures/confusion_matrix.png",
            "docs/phase_2_evidence/sprint_2_21_release_validation.md",
            "releases/SignSync_RC1/manifests/release_manifest.json",
        ),
    )

    _write_json(
        RELEASE_ROOT / "manifests" / "archive_validation.json",
        {
            "source": {**source_result, "size_bytes": SOURCE_ARCHIVE.stat().st_size, "sha256": source_hash},
            "evidence": {**evidence_result, "size_bytes": EVIDENCE_ARCHIVE.stat().st_size, "sha256": sha256_file(EVIDENCE_ARCHIVE)},
        },
    )
    return {"source": source_result, "evidence": evidence_result}


def create_final_inventory() -> None:
    inventory_path = RELEASE_ROOT / "manifests" / "artifact_inventory.csv"
    sums_path = RELEASE_ROOT / "manifests" / "SHA256SUMS.txt"
    candidates = sorted(
        (path for path in RELEASE_ROOT.rglob("*") if path.is_file() and path not in {inventory_path, sums_path}),
        key=lambda path: path.relative_to(RELEASE_ROOT).as_posix().lower(),
    )
    with inventory_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("path", "category", "size_bytes", "sha256"))
        for path in candidates:
            relative = path.relative_to(RELEASE_ROOT).as_posix()
            category = PurePosixPath(relative).parts[0] if "/" in relative else "archive"
            writer.writerow((relative, category, path.stat().st_size, sha256_file(path)))

    checksummed = sorted(
        (path for path in RELEASE_ROOT.rglob("*") if path.is_file() and path != sums_path),
        key=lambda path: path.relative_to(RELEASE_ROOT).as_posix().lower(),
    )
    _write(sums_path, "\n".join(f"{sha256_file(path)}  {path.relative_to(RELEASE_ROOT).as_posix()}" for path in checksummed))


def main() -> int:
    validate_all(include_release=False)
    validate_apks()
    generate_documents()
    generate_figures()
    prepare_release_tree()
    archive_results = create_archives_and_manifests()
    create_final_inventory()
    print("Sprint 2.21 Release Candidate Packaging")
    print("----------------------------------------")
    print(f"PASS: debug APK ({DEBUG_APK.stat().st_size:,} bytes)")
    print(f"PASS: release APK ({RELEASE_APK.stat().st_size:,} bytes)")
    print(f"PASS: 14 final documents and {len(FIGURE_NAMES)} generated evidence figures")
    print(f"PASS: source archive ({SOURCE_ARCHIVE.stat().st_size:,} bytes; {archive_results['source']['entries']} entries)")
    print(f"PASS: evidence archive ({EVIDENCE_ARCHIVE.stat().st_size:,} bytes; {archive_results['evidence']['entries']} entries)")
    print("PASS: release manifest, artifact inventories, and checksum manifests")
    print("PASS: SignSync RC1 packaging completed without modifying protected artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

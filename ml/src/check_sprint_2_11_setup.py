"""Verify Sprint 2.11 expansion setup without opening a camera or changing data."""

from __future__ import annotations

import py_compile
from pathlib import Path

import collect_video
import full_collection_config
import full_dataset_config
import full_landmark_extraction_config
from labels import (
    ALL_LABELS,
    ALL_LABELS_V1,
    ALL_LABELS_V2,
    BANKING_INTENTS_EXPANSION_V2,
    BANKING_INTENTS_V1,
    BANKING_INTENTS_V2,
    NORMAL_MODE_LABELS_V2,
    NUMBER_MODE_LABELS,
)
from sprint_2_11_intent_expansion_config import (
    EXPECTED_NEW_LABELS,
    EXPECTED_NEW_VIDEOS,
    METADATA_PATH,
    RAW_VIDEO_ROOT,
    SPRINT_2_11_REPETITIONS,
    iter_expected_samples,
)


REPORT_PATH = Path("docs") / "phase_2_evidence" / "sprint_2_11_setup_check_report.md"
LEGACY_CHECK_SCRIPTS = [
    Path("ml") / "src" / "check_full_collection_dataset.py",
    Path("ml") / "src" / "check_full_landmark_dataset.py",
    Path("ml") / "src" / "check_full_training_dataset.py",
]


def add_check(checks: list[tuple[str, bool, str]], name: str, passed: bool, detail: str) -> None:
    """Store one setup verification result for terminal and Markdown reporting."""
    checks.append((name, passed, detail))


def compile_legacy_checks() -> tuple[bool, str]:
    """Compile legacy verifiers to confirm V2 labels did not break their syntax."""
    try:
        for script_path in LEGACY_CHECK_SCRIPTS:
            py_compile.compile(script_path, doraise=True)
    except py_compile.PyCompileError as exc:
        return False, str(exc)
    return True, "all Sprint 2.8, 2.9, and 2.10 verification scripts compile"


def write_report(checks: list[tuple[str, bool, str]], passed: bool) -> None:
    """Write a concise FYP evidence report for the pre-recording setup check."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {name} | {'PASS' if result else 'FAIL'} | {detail} |"
        for name, result, detail in checks
    )
    failures = [f"- {name}: {detail}" for name, result, detail in checks if not result]
    content = f"""# Sprint 2.11 Intent Expansion Setup Check

## Result
{'PASS' if passed else 'FAIL'}

## Checks
| Check | Status | Detail |
| --- | --- | --- |
{rows}

## Failed Checks
{'\n'.join(failures) if failures else '- None'}

## Scope Confirmation
- New banking labels: {EXPECTED_NEW_LABELS}
- Repetitions per new label: {SPRINT_2_11_REPETITIONS}
- Expected new videos: {EXPECTED_NEW_VIDEOS}
- Raw videos were not recorded or changed by this check.
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    """Run safe pre-recording checks and return non-zero when any check fails."""
    checks: list[tuple[str, bool, str]] = []
    add_check(checks, "V1 total labels", len(ALL_LABELS_V1) == 56, str(len(ALL_LABELS_V1)))
    add_check(checks, "V2 total labels", len(ALL_LABELS_V2) == 86, str(len(ALL_LABELS_V2)))
    add_check(
        checks,
        "V2 banking intent count",
        len(BANKING_INTENTS_V2) == 50,
        str(len(BANKING_INTENTS_V2)),
    )
    add_check(
        checks,
        "new banking intent count",
        len(BANKING_INTENTS_EXPANSION_V2) == EXPECTED_NEW_LABELS,
        str(len(BANKING_INTENTS_EXPANSION_V2)),
    )
    add_check(
        checks,
        "new labels are active",
        all(label in ALL_LABELS for label in BANKING_INTENTS_EXPANSION_V2),
        "all expansion labels are in active ALL_LABELS",
    )
    add_check(
        checks,
        "new labels are unique",
        len(set(BANKING_INTENTS_EXPANSION_V2)) == len(BANKING_INTENTS_EXPANSION_V2),
        "no duplicates in the 30-label expansion",
    )
    add_check(
        checks,
        "new labels do not overlap V1",
        not set(BANKING_INTENTS_EXPANSION_V2).intersection(BANKING_INTENTS_V1),
        "no expansion label exists in V1 banking intents",
    )
    add_check(checks, "receipt excluded", "receipt" not in ALL_LABELS_V2, "receipt absent")
    add_check(checks, "payment included", "payment" in ALL_LABELS_V2, "payment present")
    add_check(
        checks,
        "V2 Normal Mode count",
        len(NORMAL_MODE_LABELS_V2) == 76,
        str(len(NORMAL_MODE_LABELS_V2)),
    )
    add_check(
        checks,
        "Number Mode count",
        len(NUMBER_MODE_LABELS) == 10,
        str(len(NUMBER_MODE_LABELS)),
    )
    add_check(
        checks,
        "Sprint 2.11 expected samples",
        len(iter_expected_samples()) == EXPECTED_NEW_VIDEOS,
        str(len(iter_expected_samples())),
    )

    try:
        accepted_label = collect_video.validate_label(BANKING_INTENTS_EXPANSION_V2[0])
        add_check(
            checks,
            "collect_video active label validation",
            accepted_label == BANKING_INTENTS_EXPANSION_V2[0],
            f"accepted {accepted_label}",
        )
    except ValueError as exc:
        add_check(checks, "collect_video active label validation", False, str(exc))

    add_check(checks, "metadata file exists", METADATA_PATH.exists(), METADATA_PATH.as_posix())
    add_check(checks, "raw video root exists", RAW_VIDEO_ROOT.exists(), RAW_VIDEO_ROOT.as_posix())
    add_check(
        checks,
        "Sprint 2.8 V1 configuration",
        len(full_collection_config.REMAINING_LABELS) == 45,
        f"{len(full_collection_config.REMAINING_LABELS)} remaining labels",
    )
    add_check(
        checks,
        "Sprint 2.9 V1 configuration",
        len(full_landmark_extraction_config.iter_expected_samples()) == 505,
        f"{len(full_landmark_extraction_config.iter_expected_samples())} expected samples",
    )
    add_check(
        checks,
        "Sprint 2.10 V1 configuration",
        len(full_dataset_config.iter_expected_samples()) == 505,
        f"{len(full_dataset_config.iter_expected_samples())} expected samples",
    )
    legacy_compiles, legacy_detail = compile_legacy_checks()
    add_check(checks, "legacy check scripts compile", legacy_compiles, legacy_detail)

    passed = all(result for _, result, _ in checks)
    write_report(checks, passed)
    if passed:
        print("PASS: Sprint 2.11 setup check passed.")
        return 0

    print("FAIL: Sprint 2.11 setup check failed.")
    for name, result, detail in checks:
        if not result:
            print(f"- {name}: {detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

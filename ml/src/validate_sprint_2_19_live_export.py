"""Validate a completed Sprint 2.19 Samsung A55 export before analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sprint_2_19_config import DOC_SCHEDULE, TRIAL_COLUMNS, VALIDATED_DIR
from sprint_2_19_evaluation import (
    EvaluationValidationError,
    load_schedule,
    read_csv_rows,
    read_json_object,
    sha256_file,
    validate_rows,
    validate_technical_events,
    write_csv,
    write_json,
)


def validate_export(
    live_trials_path: Path,
    metadata_path: Path,
    schedule_path: Path = DOC_SCHEDULE,
    output_dir: Path = VALIDATED_DIR,
    technical_events_path: Path | None = None,
) -> list[dict[str, object]]:
    """Validate a complete export and write only validation artifacts."""
    columns, raw_rows = read_csv_rows(live_trials_path)
    schedule = load_schedule(schedule_path)
    metadata = read_json_object(metadata_path)
    rows = validate_rows(columns, raw_rows, schedule, metadata)
    events = validate_technical_events(
        technical_events_path,
        metadata,
        str(rows[0]["session_id"]),
    )

    export_hashes = metadata.get("export_file_sha256")
    if not isinstance(export_hashes, dict):
        raise EvaluationValidationError("Export hashes are missing from metadata.")
    expected_hash = export_hashes.get(live_trials_path.name)
    if expected_hash != sha256_file(live_trials_path):
        raise EvaluationValidationError("Live-trial CSV hash does not match metadata.")
    if technical_events_path is not None:
        event_hash = export_hashes.get(technical_events_path.name)
        if event_hash != sha256_file(technical_events_path):
            raise EvaluationValidationError(
                "Technical-event CSV hash does not match metadata."
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "validated_trials.csv", TRIAL_COLUMNS, rows)
    report = {
        "status": "PASS",
        "critical_validation_passed": True,
        "trial_count": len(rows),
        "session_id": rows[0]["session_id"],
        "schedule_sha256": sha256_file(schedule_path),
        "live_trials_sha256": sha256_file(live_trials_path),
        "privacy_schema_passed": True,
        "technical_event_count": len(events),
        "physical_results_validated": True,
    }
    write_json(output_dir / "validation_report.json", report)
    (output_dir / "validation_report.md").write_text(
        "# Sprint 2.19 Export Validation\n\n"
        "**Status: PASS**\n\n"
        f"- Valid recognition trials: {len(rows)}\n"
        "- Frozen schedule: PASS\n"
        "- Frozen model and threshold: PASS\n"
        "- Trial consistency: PASS\n"
        "- Privacy-safe schema: PASS\n",
        encoding="utf-8",
    )
    return rows


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-trials", type=Path)
    parser.add_argument("--session-metadata", type=Path)
    parser.add_argument("--technical-events", type=Path)
    parser.add_argument("--schedule", type=Path, default=DOC_SCHEDULE)
    parser.add_argument("--output-dir", type=Path, default=VALIDATED_DIR)
    parser.add_argument(
        "--check-schedule-only",
        action="store_true",
        help="Validate preparation without claiming physical completion.",
    )
    return parser


def main() -> int:
    """Run schedule-only preparation validation or full export validation."""
    args = build_parser().parse_args()
    try:
        if args.check_schedule_only:
            schedule = load_schedule(args.schedule)
            print("Sprint 2.19 Preparation Validation")
            print("----------------------------------")
            print(f"frozen schedule rows: {len(schedule)}")
            print(f"schedule SHA-256: {sha256_file(args.schedule)}")
            print("PASS: automated preparation only; physical execution remains pending.")
            return 0
        if args.live_trials is None or args.session_metadata is None:
            raise EvaluationValidationError(
                "--live-trials and --session-metadata are required for physical validation."
            )
        rows = validate_export(
            args.live_trials,
            args.session_metadata,
            args.schedule,
            args.output_dir,
            args.technical_events,
        )
        print(f"PASS: validated {len(rows)} immutable live recognition trials.")
        return 0
    except (EvaluationValidationError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

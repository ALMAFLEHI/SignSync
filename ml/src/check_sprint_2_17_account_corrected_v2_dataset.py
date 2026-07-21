"""Validate the protected 1,000-sample Sprint 2.17 phone dataset read-only."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from sprint_2_17_account_corrected_v2_config import (
    DERIVED_CHECKSUM_DIR,
    DERIVED_REPORT_DIR,
    EXPECTED_FLUTTER_DYNAMIC_SHA256,
    EXPECTED_FLUTTER_FLOAT32_SHA256,
    EXPECTED_PHONE_BACKUP_SHA256,
    FINAL_LABELS,
    FLUTTER_DYNAMIC_MODEL,
    FLUTTER_FLOAT32_MODEL,
    PARTICIPANT_ID,
    PHONE_BACKUP_PATH,
    PHONE_SAMPLE_DIR,
    PILOT_LABELS,
    ensure_output_directories,
)
from sprint_2_17_utils import (
    PhoneSequence,
    load_phone_sequence,
    relative_path,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


REPORT_JSON = DERIVED_REPORT_DIR / "raw_dataset_validation.json"
REPORT_CSV = DERIVED_REPORT_DIR / "raw_dataset_per_label.csv"
REPORT_MD = DERIVED_REPORT_DIR / "raw_dataset_validation.md"
HASH_MANIFEST = DERIVED_CHECKSUM_DIR / "phone_source_json_sha256.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=PHONE_SAMPLE_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_directories()
    paths = sorted(path for path in args.sample_dir.rglob("*.json") if path.is_file())
    original_hashes = {path: sha256_file(path) for path in paths}
    samples: list[PhoneSequence] = []
    errors: list[str] = []
    for path in paths:
        try:
            samples.append(load_phone_sequence(path))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))

    label_counts = Counter(sample.label for sample in samples)
    sample_id_counts = Counter(sample.sample_id for sample in samples)
    filename_counts = Counter(sample.path.name for sample in samples)
    sequence_groups: dict[str, list[PhoneSequence]] = defaultdict(list)
    for sample in samples:
        sequence_groups[sample.sequence_sha256].append(sample)
    duplicate_sequence_groups = [
        group for group in sequence_groups.values() if len(group) > 1
    ]
    cross_label_duplicate_groups = [
        group for group in duplicate_sequence_groups if len({item.label for item in group}) > 1
    ]

    checks = {
        "json_file_count": len(paths) == 1000,
        "valid_sample_count": len(samples) == 1000,
        "label_count": set(label_counts) == set(FINAL_LABELS),
        "per_label_count": all(label_counts[label] == 25 for label in FINAL_LABELS),
        "repetition_coverage": all(
            {item.repetition for item in samples if item.label == label}
            == set(range(1, 26))
            for label in FINAL_LABELS
        ),
        "participant_metadata": all(item.participant_id == PARTICIPANT_ID for item in samples),
        "unique_sample_ids": all(count == 1 for count in sample_id_counts.values()),
        "unique_filenames": all(count == 1 for count in filename_counts.values()),
        "no_exact_duplicate_sequences": not duplicate_sequence_groups,
        "no_cross_label_identical_content": not cross_label_duplicate_groups,
        "pilot_counts": all(label_counts[label] == 25 for label in PILOT_LABELS),
        "no_parse_or_contract_errors": not errors,
    }

    post_hashes = {path: sha256_file(path) for path in paths}
    checks["raw_files_unchanged_during_validation"] = original_hashes == post_hashes
    protected_hashes = {
        "flutter_dynamic_range": sha256_file(FLUTTER_DYNAMIC_MODEL),
        "flutter_float32": sha256_file(FLUTTER_FLOAT32_MODEL),
        "phone_backup": sha256_file(PHONE_BACKUP_PATH),
    }
    checks["protected_flutter_dynamic_hash"] = (
        protected_hashes["flutter_dynamic_range"].upper()
        == EXPECTED_FLUTTER_DYNAMIC_SHA256
    )
    checks["protected_flutter_float32_hash"] = (
        protected_hashes["flutter_float32"].upper()
        == EXPECTED_FLUTTER_FLOAT32_SHA256
    )
    checks["protected_backup_hash"] = (
        protected_hashes["phone_backup"].upper() == EXPECTED_PHONE_BACKUP_SHA256
    )

    hash_rows = [
        {
            "sample_id": sample.sample_id,
            "label": sample.label,
            "repetition": sample.repetition,
            "source_path": relative_path(sample.path),
            "file_sha256": sample.sha256,
            "sequence_sha256": sample.sequence_sha256,
        }
        for sample in samples
    ]
    write_csv(
        HASH_MANIFEST,
        hash_rows,
        [
            "sample_id",
            "label",
            "repetition",
            "source_path",
            "file_sha256",
            "sequence_sha256",
        ],
    )

    per_label_rows = []
    for label_index, label in enumerate(FINAL_LABELS):
        group = [sample for sample in samples if sample.label == label]
        per_label_rows.append(
            {
                "label_index": label_index,
                "label": label,
                "sample_count": len(group),
                "minimum_repetition": min((item.repetition for item in group), default=""),
                "maximum_repetition": max((item.repetition for item in group), default=""),
                "missing_left_frames": sum(item.missing_left_frames for item in group),
                "missing_right_frames": sum(item.missing_right_frames for item in group),
                "status": "PASS" if len(group) == 25 else "FAIL",
            }
        )
    write_csv(
        REPORT_CSV,
        per_label_rows,
        [
            "label_index",
            "label",
            "sample_count",
            "minimum_repetition",
            "maximum_repetition",
            "missing_left_frames",
            "missing_right_frames",
            "status",
        ],
    )

    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "status": status,
        "generated_at": utc_now(),
        "sample_directory": relative_path(args.sample_dir),
        "json_files": len(paths),
        "valid_samples": len(samples),
        "participant_ids": sorted({sample.participant_id for sample in samples}),
        "labels": len(label_counts),
        "per_label_counts": {label: label_counts[label] for label in FINAL_LABELS},
        "sequence_shape": [60, 126],
        "duplicate_sample_ids": sorted(
            sample_id for sample_id, count in sample_id_counts.items() if count > 1
        ),
        "duplicate_filenames": sorted(
            name for name, count in filename_counts.items() if count > 1
        ),
        "exact_duplicate_sequence_groups": [
            [item.sample_id for item in group] for group in duplicate_sequence_groups
        ],
        "cross_label_duplicate_groups": [
            [item.sample_id for item in group] for group in cross_label_duplicate_groups
        ],
        "errors": errors,
        "checks": checks,
        "protected_hashes": protected_hashes,
        "source_hash_manifest": relative_path(HASH_MANIFEST),
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(_markdown_report(report), encoding="utf-8")

    print("Sprint 2.17 Final 40-Class Dataset Validation")
    print("------------------------------------------------")
    print(f"JSON files: {len(paths)}")
    print(f"Valid samples: {len(samples)}")
    print(f"Frozen labels: {len(label_counts)}")
    print(f"Exact duplicate sequences: {len(duplicate_sequence_groups)}")
    print(f"Cross-label identical sequences: {len(cross_label_duplicate_groups)}")
    print(f"Raw files unchanged: {checks['raw_files_unchanged_during_validation']}")
    print(f"Report: {relative_path(REPORT_MD)}")
    print(f"Status: {status}")
    return 0 if status == "PASS" else 1


def _markdown_report(report: dict[str, object]) -> str:
    checks = report["checks"]
    lines = [
        "# Sprint 2.17 Raw Phone Dataset Validation",
        "",
        f"## Status: {report['status']}",
        "",
        f"- Source JSON files: {report['json_files']}",
        f"- Valid samples: {report['valid_samples']}",
        f"- Frozen banking labels: {report['labels']}",
        "- Samples per label: 25",
        "- Sequence shape: 60 x 126",
        f"- Exact duplicate sequence groups: {len(report['exact_duplicate_sequence_groups'])}",
        f"- Cross-label duplicate groups: {len(report['cross_label_duplicate_groups'])}",
        "- Raw files repaired or rewritten: 0",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- [{'x' if passed else ' '}] {name.replace('_', ' ')}"
        for name, passed in checks.items()
    )
    lines.extend(
        [
            "",
            "## Protected Hashes",
            "",
            f"- Flutter dynamic model: `{report['protected_hashes']['flutter_dynamic_range']}`",
            f"- Flutter float32 model: `{report['protected_hashes']['flutter_float32']}`",
            f"- Dataset backup: `{report['protected_hashes']['phone_backup']}`",
            "",
            "The validator is read-only for all phone source JSON files.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

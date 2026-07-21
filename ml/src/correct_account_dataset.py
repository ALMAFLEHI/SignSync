"""Validate and apply the corrected Samsung A55 account dataset component."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_17_config import FINAL_LABELS, PHONE_SAMPLE_DIR, ROOT
from sprint_2_17_utils import (
    PhoneSequence,
    load_phone_sequence,
    relative_path,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


CORRECTION_DATE = "20260719"
CORRECTION_ROOT = (
    ROOT / "ml" / "data_phone" / "corrections" / f"account_{CORRECTION_DATE}"
)
STAGING_DIR = CORRECTION_ROOT / "staging_from_a55"
OLD_HASH_MANIFEST = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_17_40class"
    / "checksums"
    / "phone_source_json_sha256.csv"
)
INVALIDATED_ACCOUNT_DIR = (
    ROOT
    / "ml"
    / "data_phone"
    / "invalidated"
    / f"account_incorrect_gesture_{CORRECTION_DATE}"
)
OLD_CANONICAL_BACKUP = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_16B_banking_phone_samples_1000_backup.zip"
)
INVALIDATED_BACKUP_DIR = ROOT / "ml" / "data_phone" / "invalidated_backups"
INVALIDATED_BACKUP = (
    INVALIDATED_BACKUP_DIR
    / (
        "sprint_2_16B_banking_phone_samples_1000_backup_"
        f"incorrect_account_{CORRECTION_DATE}.zip"
    )
)
TIMESTAMPED_CORRECTED_BACKUP = (
    ROOT
    / "ml"
    / "data_phone"
    / (
        "sprint_2_16B_banking_phone_samples_1000_"
        f"account_corrected_{CORRECTION_DATE}.zip"
    )
)
CORRECTED_HASH_MANIFEST = CORRECTION_ROOT / "corrected_phone_source_json_sha256.csv"
CORRECTED_BACKUP_MANIFEST = (
    ROOT / "ml" / "data_phone" / "corrected_backup_manifest.json"
)
CORRECTED_BACKUP_SHA256SUMS = (
    ROOT / "ml" / "data_phone" / "CORRECTED_BACKUP_SHA256SUMS.txt"
)

EXPECTED_OLD_BACKUP_SHA256 = (
    "F3F76C6BBE06305C7AE82E2772C5DACA7F76619444F7ECA892D7AA253986B70B"
)
EXPECTED_ACCOUNT_IDS = {
    f"P02_PHONE_account_R{repetition:02d}" for repetition in range(1, 26)
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("validate-staging", "apply", "verify"),
        help="Run a read-only staged validation, apply the correction, or verify it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "validate-staging":
        report = validate_staging(write_reports=True)
        _print_staging_summary(report)
        return 0 if report["status"] == "PASS" else 1
    if args.command == "apply":
        report = apply_correction()
        _print_apply_summary(report)
        return 0

    report = verify_corrected_state()
    _print_apply_summary(report)
    return 0 if report["status"] == "PASS" else 1


def validate_staging(*, write_reports: bool) -> dict[str, Any]:
    """Validate all staged bytes before any canonical replacement."""
    old_rows = _read_old_hash_manifest()
    old_account_sequence_hashes = {
        row["sequence_sha256"] for row in old_rows.values() if row["label"] == "account"
    }
    savings_sequence_hashes = {
        row["sequence_sha256"] for row in old_rows.values() if row["label"] == "savings"
    }
    old_account_file_hashes = {
        row["file_sha256"] for row in old_rows.values() if row["label"] == "account"
    }

    paths = sorted(STAGING_DIR.glob("*.json")) if STAGING_DIR.is_dir() else []
    samples: list[PhoneSequence] = []
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payloads[path.name] = payload
            sample = load_phone_sequence(path)
            samples.append(sample)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")

    sequence_counts = Counter(sample.sequence_sha256 for sample in samples)
    id_counts = Counter(sample.sample_id for sample in samples)
    for sample in samples:
        payload = payloads[sample.path.name]
        created_at = payload.get("created_at")
        created_at_valid = _valid_iso_timestamp(created_at)
        overlap_old_account = sample.sequence_sha256 in old_account_sequence_hashes
        overlap_savings = sample.sequence_sha256 in savings_sequence_hashes
        row_valid = all(
            (
                sample.label == "account",
                sample.sample_id in EXPECTED_ACCOUNT_IDS,
                1 <= sample.repetition <= 25,
                sample.frames.shape == (60, 126),
                bool(np.isfinite(sample.frames).all()),
                sequence_counts[sample.sequence_sha256] == 1,
                id_counts[sample.sample_id] == 1,
                not overlap_old_account,
                not overlap_savings,
                sample.sha256 not in old_account_file_hashes,
                created_at_valid,
            )
        )
        rows.append(
            {
                "sample_id": sample.sample_id,
                "participant_id": sample.participant_id,
                "label": sample.label,
                "repetition": f"R{sample.repetition:02d}",
                "filename": sample.path.name,
                "created_at": created_at,
                "frame_count": sample.frames.shape[0],
                "frame_width": sample.frames.shape[1],
                "file_sha256": sample.sha256,
                "sequence_sha256": sample.sequence_sha256,
                "missing_left_frames": sample.missing_left_frames,
                "missing_right_frames": sample.missing_right_frames,
                "duplicate_sequence": sequence_counts[sample.sequence_sha256] > 1,
                "overlap_old_account_sequence": overlap_old_account,
                "overlap_savings_sequence": overlap_savings,
                "valid": row_valid,
            }
        )

    sample_ids = {sample.sample_id for sample in samples}
    checks = {
        "exactly_25_json_files": len(paths) == 25,
        "all_25_samples_valid": len(samples) == 25 and not errors,
        "exact_account_ids_r01_r25": sample_ids == EXPECTED_ACCOUNT_IDS,
        "account_label_only": all(sample.label == "account" for sample in samples),
        "unique_filenames": len({path.name for path in paths}) == len(paths),
        "unique_sample_ids": len(sample_ids) == len(samples),
        "unique_sequence_content": all(count == 1 for count in sequence_counts.values()),
        "no_old_account_sequence_overlap": not any(
            sample.sequence_sha256 in old_account_sequence_hashes for sample in samples
        ),
        "no_savings_sequence_overlap": not any(
            sample.sequence_sha256 in savings_sequence_hashes for sample in samples
        ),
        "all_file_bytes_differ_from_old_account": not any(
            sample.sha256 in old_account_file_hashes for sample in samples
        ),
        "shape_60_by_126": all(sample.frames.shape == (60, 126) for sample in samples),
        "finite_numeric_values": all(
            np.isfinite(sample.frames).all() for sample in samples
        ),
        "no_empty_or_no_hand_frames": all(
            not np.any(
                np.all(sample.frames[:, :63] == 0.0, axis=1)
                & np.all(sample.frames[:, 63:] == 0.0, axis=1)
            )
            for sample in samples
        ),
        "created_at_metadata_valid": all(
            _valid_iso_timestamp(payloads[path.name].get("created_at"))
            for path in paths
            if path.name in payloads
        )
        and len(payloads) == 25,
    }
    status = "PASS" if all(checks.values()) and all(row["valid"] for row in rows) else "FAIL"
    report = {
        "project": "SignSync",
        "correction": "account gesture replacement",
        "status": status,
        "generated_at": utc_now(),
        "staging_directory": relative_path(STAGING_DIR),
        "phone_source_directory": (
            "/storage/emulated/0/Android/data/com.example.flutter_app/files/"
            "signsync_phone_samples"
        ),
        "json_files": len(paths),
        "valid_samples": len(samples),
        "errors": errors,
        "checks": checks,
        "samples": rows,
        "adb_commands": [
            '& "$adb" devices -l',
            (
                '& "$adb" pull "/storage/emulated/0/Android/data/'
                "com.example.flutter_app/files/signsync_phone_samples/"
                'P02_PHONE_account_R<01-25>.json" "<staging_from_a55>"'
            ),
        ],
    }
    if write_reports:
        _write_staging_reports(report, rows)
    return report


def apply_correction() -> dict[str, Any]:
    """Archive invalid data, atomically replace account, and regenerate backups."""
    validation = validate_staging(write_reports=True)
    if validation["status"] != "PASS":
        raise ValueError("Staged corrected account samples did not pass validation.")

    old_rows = _read_old_hash_manifest()
    if set(old_rows) != _expected_all_sample_ids():
        raise ValueError("Previous source hash manifest does not contain the expected 1,000 IDs.")
    _verify_non_account_files(old_rows)

    staged = {path.stem: path for path in sorted(STAGING_DIR.glob("*.json"))}
    active_account_hashes = {
        sample_id: sha256_file(PHONE_SAMPLE_DIR / f"{sample_id}.json")
        for sample_id in sorted(EXPECTED_ACCOUNT_IDS)
    }
    staged_hashes = {sample_id: sha256_file(path) for sample_id, path in staged.items()}
    old_account_hashes = {
        sample_id: old_rows[sample_id]["file_sha256"]
        for sample_id in sorted(EXPECTED_ACCOUNT_IDS)
    }

    active_is_old = active_account_hashes == old_account_hashes
    active_is_corrected = active_account_hashes == staged_hashes
    if not active_is_old and not active_is_corrected:
        raise ValueError("Active account files are a mixed or unknown state; refusing replacement.")

    if active_is_old:
        _archive_old_account(old_rows)
        for sample_id, source in staged.items():
            target = PHONE_SAMPLE_DIR / f"{sample_id}.json"
            temporary = target.with_suffix(".json.account_correction_tmp")
            shutil.copyfile(source, temporary)
            if sha256_file(temporary) != staged_hashes[sample_id]:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"Temporary copy hash mismatch for {sample_id}.")
            os.replace(temporary, target)
    elif not INVALIDATED_ACCOUNT_DIR.is_dir():
        raise ValueError("Corrected account is active but the invalidated archive is missing.")

    _verify_non_account_files(old_rows)
    corrected = _validate_full_dataset(PHONE_SAMPLE_DIR)
    if corrected["status"] != "PASS":
        raise ValueError("Corrected canonical dataset failed full validation.")

    comparison_rows = _non_account_comparison_rows(old_rows)
    write_csv(
        CORRECTION_ROOT / "non_account_975_integrity_comparison.csv",
        comparison_rows,
        [
            "sample_id",
            "label",
            "source_path",
            "previous_file_sha256",
            "corrected_file_sha256",
            "unchanged",
        ],
    )
    corrected_rows = corrected["manifest_rows"]
    write_csv(
        CORRECTED_HASH_MANIFEST,
        corrected_rows,
        [
            "sample_id",
            "label",
            "repetition",
            "source_path",
            "file_sha256",
            "sequence_sha256",
        ],
    )

    changed_account = sum(
        old_rows[sample_id]["file_sha256"]
        != next(
            row["file_sha256"]
            for row in corrected_rows
            if row["sample_id"] == sample_id
        )
        for sample_id in EXPECTED_ACCOUNT_IDS
    )
    summary = {
        "status": "PASS",
        "generated_at": utc_now(),
        "previous_total": 1000,
        "corrected_total": corrected["sample_count"],
        "unchanged_non_account_samples": sum(
            row["unchanged"] for row in comparison_rows
        ),
        "replaced_account_samples": changed_account,
        "unexpected_changed_files": [
            row["sample_id"] for row in comparison_rows if not row["unchanged"]
        ],
        "added_unintended_files": sorted(
            set(row["sample_id"] for row in corrected_rows) - set(old_rows)
        ),
        "missing_unintended_files": sorted(
            set(old_rows) - set(row["sample_id"] for row in corrected_rows)
        ),
        "corrected_dataset_manifest": relative_path(CORRECTED_HASH_MANIFEST),
        "corrected_dataset_manifest_sha256": sha256_file(CORRECTED_HASH_MANIFEST),
        "old_account_archive": relative_path(INVALIDATED_ACCOUNT_DIR),
        "old_account_archive_manifest_sha256": sha256_file(
            INVALIDATED_ACCOUNT_DIR / "SHA256SUMS.txt"
        ),
        "full_dataset_checks": corrected["checks"],
    }
    if (
        summary["unchanged_non_account_samples"] != 975
        or changed_account != 25
        or summary["unexpected_changed_files"]
        or summary["added_unintended_files"]
        or summary["missing_unintended_files"]
    ):
        raise ValueError("Dataset change boundary is not exactly 25 account replacements.")
    write_json(CORRECTION_ROOT / "dataset_change_summary.json", summary)

    backup_report = _create_and_verify_backups(corrected_rows)
    summary["backup_validation"] = backup_report
    write_json(CORRECTION_ROOT / "dataset_change_summary.json", summary)
    return verify_corrected_state()


def verify_corrected_state() -> dict[str, Any]:
    old_rows = _read_old_hash_manifest()
    corrected = _validate_full_dataset(PHONE_SAMPLE_DIR)
    comparison = _non_account_comparison_rows(old_rows)
    staging = validate_staging(write_reports=True)
    canonical_hash = (
        sha256_file(OLD_CANONICAL_BACKUP) if OLD_CANONICAL_BACKUP.is_file() else None
    )
    timestamped_hash = (
        sha256_file(TIMESTAMPED_CORRECTED_BACKUP)
        if TIMESTAMPED_CORRECTED_BACKUP.is_file()
        else None
    )
    checks = {
        "staging_validation_passed": staging["status"] == "PASS",
        "corrected_dataset_passed": corrected["status"] == "PASS",
        "unchanged_non_account_975": sum(row["unchanged"] for row in comparison) == 975,
        "invalidated_account_archive_exists": (
            len(list(INVALIDATED_ACCOUNT_DIR.glob("P02_PHONE_account_R*.json"))) == 25
            and (INVALIDATED_ACCOUNT_DIR / "SHA256SUMS.txt").is_file()
        ),
        "invalidated_old_backup_exists": (
            INVALIDATED_BACKUP.is_file()
            and sha256_file(INVALIDATED_BACKUP).upper()
            == EXPECTED_OLD_BACKUP_SHA256
        ),
        "corrected_backups_exist_and_match": (
            canonical_hash is not None
            and canonical_hash == timestamped_hash
            and canonical_hash.upper() != EXPECTED_OLD_BACKUP_SHA256
        ),
        "corrected_manifest_exists": CORRECTED_HASH_MANIFEST.is_file(),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "generated_at": utc_now(),
        "checks": checks,
        "sample_count": corrected["sample_count"],
        "per_label_counts": corrected["per_label_counts"],
        "corrected_dataset_manifest_sha256": (
            sha256_file(CORRECTED_HASH_MANIFEST)
            if CORRECTED_HASH_MANIFEST.is_file()
            else None
        ),
        "old_account_archive": relative_path(INVALIDATED_ACCOUNT_DIR),
        "old_account_archive_manifest_sha256": (
            sha256_file(INVALIDATED_ACCOUNT_DIR / "SHA256SUMS.txt")
            if (INVALIDATED_ACCOUNT_DIR / "SHA256SUMS.txt").is_file()
            else None
        ),
        "invalidated_backup": relative_path(INVALIDATED_BACKUP),
        "invalidated_backup_sha256": (
            sha256_file(INVALIDATED_BACKUP) if INVALIDATED_BACKUP.is_file() else None
        ),
        "timestamped_corrected_backup": relative_path(TIMESTAMPED_CORRECTED_BACKUP),
        "timestamped_corrected_backup_sha256": timestamped_hash,
        "canonical_corrected_backup": relative_path(OLD_CANONICAL_BACKUP),
        "canonical_corrected_backup_sha256": canonical_hash,
    }


def _archive_old_account(old_rows: dict[str, dict[str, str]]) -> None:
    INVALIDATED_ACCOUNT_DIR.mkdir(parents=True, exist_ok=False)
    manifest_rows = []
    for sample_id in sorted(EXPECTED_ACCOUNT_IDS):
        source = PHONE_SAMPLE_DIR / f"{sample_id}.json"
        expected = old_rows[sample_id]["file_sha256"]
        if sha256_file(source) != expected:
            raise ValueError(f"Old account hash mismatch before archive: {sample_id}")
        destination = INVALIDATED_ACCOUNT_DIR / source.name
        shutil.copy2(source, destination)
        if sha256_file(destination) != expected:
            raise ValueError(f"Archived account hash mismatch: {sample_id}")
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "original_path": old_rows[sample_id]["source_path"],
                "archive_path": relative_path(destination),
                "file_sha256": expected,
                "sequence_sha256": old_rows[sample_id]["sequence_sha256"],
                "status": "INVALIDATED",
            }
        )
    write_csv(
        INVALIDATED_ACCOUNT_DIR / "original_sample_manifest.csv",
        manifest_rows,
        [
            "sample_id",
            "original_path",
            "archive_path",
            "file_sha256",
            "sequence_sha256",
            "status",
        ],
    )
    sums = "\n".join(
        f"{row['file_sha256'].upper()}  {Path(row['archive_path']).name}"
        for row in manifest_rows
    )
    (INVALIDATED_ACCOUNT_DIR / "SHA256SUMS.txt").write_text(
        sums + "\n", encoding="utf-8"
    )
    (INVALIDATED_ACCOUNT_DIR / "README.md").write_text(
        """# INVALIDATED DATASET COMPONENT

Status: **SUPERSEDED - INCORRECT ACCOUNT GESTURE DATA**

The original account gesture was incorrectly recorded and was not meaningfully distinct from the savings gesture. These 25 samples are preserved for audit evidence only and are excluded from all corrected training, validation, testing, deployment, and evaluation.

- Detected: 2026-07-19
- Original active path: `ml/data_phone/landmark_samples/`
- Replacement scope: account R01-R25 only
- Future training use: forbidden
""",
        encoding="utf-8",
    )


def _create_and_verify_backups(
    corrected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if sha256_file(OLD_CANONICAL_BACKUP).upper() != EXPECTED_OLD_BACKUP_SHA256:
        raise ValueError("Old canonical backup no longer matches the invalidated baseline.")
    INVALIDATED_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if INVALIDATED_BACKUP.exists():
        if sha256_file(INVALIDATED_BACKUP).upper() != EXPECTED_OLD_BACKUP_SHA256:
            raise ValueError("Existing invalidated backup has an unexpected hash.")
    else:
        shutil.copy2(OLD_CANONICAL_BACKUP, INVALIDATED_BACKUP)
    (INVALIDATED_BACKUP_DIR / "README.md").write_text(
        """# Superseded Dataset Backup

`sprint_2_16B_banking_phone_samples_1000_backup_incorrect_account_20260719.zip` is retained as historical evidence only. It contains the invalid account gesture recordings that conflicted with savings and must not be used as the corrected project dataset.

Historical invalid SHA-256: `F3F76C6BBE06305C7AE82E2772C5DACA7F76619444F7ECA892D7AA253986B70B`.
""",
        encoding="utf-8",
    )

    _write_deterministic_zip(PHONE_SAMPLE_DIR, TIMESTAMPED_CORRECTED_BACKUP)
    extracted_validation = _verify_backup_extraction(
        TIMESTAMPED_CORRECTED_BACKUP, corrected_rows
    )
    if extracted_validation["status"] != "PASS":
        raise ValueError("Timestamped corrected backup extraction validation failed.")

    temporary = OLD_CANONICAL_BACKUP.with_suffix(".zip.account_correction_tmp")
    shutil.copyfile(TIMESTAMPED_CORRECTED_BACKUP, temporary)
    if sha256_file(temporary) != sha256_file(TIMESTAMPED_CORRECTED_BACKUP):
        temporary.unlink(missing_ok=True)
        raise ValueError("Canonical corrected backup temporary hash mismatch.")
    os.replace(temporary, OLD_CANONICAL_BACKUP)
    canonical_validation = _verify_backup_extraction(OLD_CANONICAL_BACKUP, corrected_rows)
    if canonical_validation["status"] != "PASS":
        raise ValueError("Canonical corrected backup extraction validation failed.")

    manifest = {
        "project": "SignSync",
        "status": "PASS",
        "generated_at": utc_now(),
        "dataset_status": "corrected_account_dataset_v2",
        "json_files": 1000,
        "labels": 40,
        "samples_per_label": 25,
        "corrected_account_samples": 25,
        "unchanged_non_account_samples": 975,
        "content_manifest": relative_path(CORRECTED_HASH_MANIFEST),
        "content_manifest_sha256": sha256_file(CORRECTED_HASH_MANIFEST),
        "superseded_backup": {
            "path": relative_path(INVALIDATED_BACKUP),
            "sha256": sha256_file(INVALIDATED_BACKUP),
            "status": "SUPERSEDED - INCORRECT ACCOUNT GESTURE DATA",
        },
        "timestamped_corrected_backup": {
            "path": relative_path(TIMESTAMPED_CORRECTED_BACKUP),
            "sha256": sha256_file(TIMESTAMPED_CORRECTED_BACKUP),
            "extraction_validation": extracted_validation,
        },
        "canonical_corrected_backup": {
            "path": relative_path(OLD_CANONICAL_BACKUP),
            "sha256": sha256_file(OLD_CANONICAL_BACKUP),
            "extraction_validation": canonical_validation,
        },
    }
    write_json(CORRECTED_BACKUP_MANIFEST, manifest)
    CORRECTED_BACKUP_SHA256SUMS.write_text(
        "\n".join(
            [
                f"{sha256_file(INVALIDATED_BACKUP).upper()}  {relative_path(INVALIDATED_BACKUP)}",
                f"{sha256_file(TIMESTAMPED_CORRECTED_BACKUP).upper()}  {relative_path(TIMESTAMPED_CORRECTED_BACKUP)}",
                f"{sha256_file(OLD_CANONICAL_BACKUP).upper()}  {relative_path(OLD_CANONICAL_BACKUP)}",
                f"{sha256_file(CORRECTED_HASH_MANIFEST).upper()}  {relative_path(CORRECTED_HASH_MANIFEST)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_deterministic_zip(source_dir: Path, destination: Path) -> None:
    paths = sorted(source_dir.glob("*.json"))
    if len(paths) != 1000:
        raise ValueError(f"Refusing backup creation with {len(paths)} JSON files.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in paths:
            info = zipfile.ZipInfo(path.name, date_time=(2026, 7, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100600 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    os.replace(temporary, destination)


def _verify_backup_extraction(
    backup: Path, corrected_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    expected = {Path(row["source_path"]).name: row["file_sha256"] for row in corrected_rows}
    with tempfile.TemporaryDirectory(prefix="signsync_account_backup_") as temp_name:
        temp_dir = Path(temp_name)
        with zipfile.ZipFile(backup) as archive:
            names = archive.namelist()
            if any(Path(name).name != name for name in names):
                raise ValueError("Corrected backup contains a non-flat or unsafe path.")
            archive.extractall(temp_dir)
        paths = sorted(temp_dir.glob("*.json"))
        actual = {path.name: sha256_file(path) for path in paths}
        full = _validate_full_dataset(temp_dir)
    checks = {
        "exactly_1000_json_files": len(actual) == 1000,
        "content_hashes_match_canonical_manifest": actual == expected,
        "full_dataset_validation_passed": full["status"] == "PASS",
        "corrected_account_samples_25": full["per_label_counts"].get("account") == 25,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "backup": relative_path(backup),
        "checks": checks,
    }


def _validate_full_dataset(sample_dir: Path) -> dict[str, Any]:
    paths = sorted(sample_dir.glob("*.json"))
    samples = [load_phone_sequence(path) for path in paths]
    label_order = {label: index for index, label in enumerate(FINAL_LABELS)}
    samples.sort(key=lambda sample: (label_order[sample.label], sample.repetition))
    counts = Counter(sample.label for sample in samples)
    ids = Counter(sample.sample_id for sample in samples)
    sequence_groups: dict[str, list[PhoneSequence]] = defaultdict(list)
    for sample in samples:
        sequence_groups[sample.sequence_sha256].append(sample)
    duplicate_groups = [group for group in sequence_groups.values() if len(group) > 1]
    account_sequences = {
        sample.sequence_sha256 for sample in samples if sample.label == "account"
    }
    savings_sequences = {
        sample.sequence_sha256 for sample in samples if sample.label == "savings"
    }
    checks = {
        "json_file_count_1000": len(paths) == 1000,
        "valid_sample_count_1000": len(samples) == 1000,
        "exact_40_labels": set(counts) == set(FINAL_LABELS) and len(counts) == 40,
        "every_label_has_25": all(counts[label] == 25 for label in FINAL_LABELS),
        "unique_sample_ids": all(value == 1 for value in ids.values()),
        "unique_filenames": len({path.name for path in paths}) == len(paths),
        "zero_exact_duplicate_sequences": not duplicate_groups,
        "zero_account_savings_sequence_overlap": not (
            account_sequences & savings_sequences
        ),
        "all_shapes_60_by_126": all(
            sample.frames.shape == (60, 126) for sample in samples
        ),
        "all_values_finite": all(np.isfinite(sample.frames).all() for sample in samples),
    }
    rows = [
        {
            "sample_id": sample.sample_id,
            "label": sample.label,
            "repetition": sample.repetition,
            "source_path": f"ml/data_phone/landmark_samples/{sample.path.name}",
            "file_sha256": sample.sha256,
            "sequence_sha256": sample.sequence_sha256,
        }
        for sample in samples
    ]
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "sample_count": len(samples),
        "per_label_counts": {label: counts[label] for label in FINAL_LABELS},
        "checks": checks,
        "manifest_rows": rows,
    }


def _verify_non_account_files(old_rows: dict[str, dict[str, str]]) -> None:
    failures = [
        row["sample_id"]
        for row in old_rows.values()
        if row["label"] != "account"
        and sha256_file(ROOT / Path(row["source_path"])) != row["file_sha256"]
    ]
    if failures:
        raise ValueError(
            f"Unexpected changes found in {len(failures)} non-account files: {failures[:5]}"
        )


def _non_account_comparison_rows(
    old_rows: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows = []
    for sample_id, row in sorted(old_rows.items()):
        if row["label"] == "account":
            continue
        actual = sha256_file(ROOT / Path(row["source_path"]))
        rows.append(
            {
                "sample_id": sample_id,
                "label": row["label"],
                "source_path": row["source_path"],
                "previous_file_sha256": row["file_sha256"],
                "corrected_file_sha256": actual,
                "unchanged": actual == row["file_sha256"],
            }
        )
    return rows


def _read_old_hash_manifest() -> dict[str, dict[str, str]]:
    with OLD_HASH_MANIFEST.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    return {row["sample_id"]: row for row in rows}


def _expected_all_sample_ids() -> set[str]:
    return {
        f"P02_PHONE_{label}_R{repetition:02d}"
        for label in FINAL_LABELS
        for repetition in range(1, 26)
    }


def _valid_iso_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _write_staging_reports(
    report: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    write_json(CORRECTION_ROOT / "corrected_account_validation.json", report)
    write_csv(
        CORRECTION_ROOT / "corrected_account_validation.csv",
        rows,
        [
            "sample_id",
            "participant_id",
            "label",
            "repetition",
            "filename",
            "created_at",
            "frame_count",
            "frame_width",
            "file_sha256",
            "sequence_sha256",
            "missing_left_frames",
            "missing_right_frames",
            "duplicate_sequence",
            "overlap_old_account_sequence",
            "overlap_savings_sequence",
            "valid",
        ],
    )
    checks = "\n".join(
        f"- [{'x' if passed else ' '}] {name.replace('_', ' ')}"
        for name, passed in report["checks"].items()
    )
    (CORRECTION_ROOT / "corrected_account_validation.md").write_text(
        f"""# Corrected Account Staging Validation

## Status: {report['status']}

- Staged files: {report['json_files']}
- Valid account samples: {report['valid_samples']}
- Repetition coverage: R01-R25
- Expected shape: 60 x 126
- Canonical dataset modified by this phase: no

## Checks

{checks}

The staged files were pulled byte-for-byte from the Samsung A55. No raw JSON was repaired or rewritten. Replacement is permitted only when this report is PASS.
""",
        encoding="utf-8",
    )
    (CORRECTION_ROOT / "adb_commands_used.txt").write_text(
        """$adb = "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe"
& "$adb" devices -l
# Executed once for each repetition 01 through 25:
& "$adb" pull "/storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples/P02_PHONE_account_R<01-25>.json" "ml/data_phone/corrections/account_20260719/staging_from_a55/"
""",
        encoding="utf-8",
    )


def _print_staging_summary(report: dict[str, Any]) -> None:
    print("Corrected Account Staging Validation")
    print("------------------------------------")
    print(f"Staged JSON files: {report['json_files']}")
    print(f"Valid account samples: {report['valid_samples']}")
    print(f"Errors: {len(report['errors'])}")
    print(f"Status: {report['status']}")


def _print_apply_summary(report: dict[str, Any]) -> None:
    print("Corrected Account Dataset Verification")
    print("--------------------------------------")
    print(f"Active samples: {report['sample_count']}")
    print(f"Account samples: {report['per_label_counts'].get('account')}")
    print(f"Savings samples: {report['per_label_counts'].get('savings')}")
    print(
        "Corrected manifest SHA-256: "
        f"{report['corrected_dataset_manifest_sha256']}"
    )
    print(
        "Canonical backup SHA-256: "
        f"{report['canonical_corrected_backup_sha256']}"
    )
    print(f"Status: {report['status']}")


if __name__ == "__main__":
    raise SystemExit(main())

"""Create the frozen leakage-safe 600/200/200 Sprint 2.17 phone split."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from sprint_2_17_config import (
    COMBINED_MANIFEST,
    DERIVED_REPORT_DIR,
    FINAL_LABELS,
    LABEL_TO_INDEX,
    MANIFEST_DIR,
    METADATA_DIR,
    PHONE_SAMPLE_DIR,
    PHONE_TEST_MANIFEST,
    PHONE_TRAIN_MANIFEST,
    PHONE_VALIDATION_MANIFEST,
    PILOT_LABELS,
    PILOT_MANIFEST_PATH,
    SEED,
    ensure_output_directories,
    split_for_repetition,
)
from sprint_2_17_utils import (
    load_phone_sequences,
    read_csv,
    relative_path,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


SPLIT_REPORT = DERIVED_REPORT_DIR / "phone_split_summary.md"
MANIFEST_HASHES = METADATA_DIR / "manifest_sha256.json"
TEST_LOCK = METADATA_DIR / "test_set_lock.json"

FIELDS = [
    "sample_id",
    "participant_id",
    "label",
    "label_index",
    "repetition",
    "source_path",
    "source_file_hash",
    "split",
    "sequence_shape",
    "origin",
    "domain",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_directories()
    validation = json.loads(
        (DERIVED_REPORT_DIR / "raw_dataset_validation.json").read_text(
            encoding="utf-8"
        )
    )
    if validation.get("status") != "PASS":
        raise ValueError("Raw dataset validation must pass before splitting.")

    output_paths = [
        PHONE_TRAIN_MANIFEST,
        PHONE_VALIDATION_MANIFEST,
        PHONE_TEST_MANIFEST,
        COMBINED_MANIFEST,
        TEST_LOCK,
    ]
    if not args.overwrite and any(path.exists() for path in output_paths):
        existing = [relative_path(path) for path in output_paths if path.exists()]
        raise FileExistsError(f"Split artifacts already exist: {existing}")

    pilot_assignments = _load_pilot_assignments()
    samples = load_phone_sequences(PHONE_SAMPLE_DIR)
    rows: list[dict[str, object]] = []
    pilot_preserved = True
    for sample in samples:
        expected_split = split_for_repetition(sample.repetition)
        if sample.label in PILOT_LABELS:
            preserved_split = pilot_assignments.get(sample.sample_id)
            if preserved_split != expected_split:
                pilot_preserved = False
                raise ValueError(
                    f"Pilot split mismatch for {sample.sample_id}: "
                    f"existing={preserved_split}, expected={expected_split}"
                )
            split = preserved_split
        else:
            split = expected_split
        rows.append(
            {
                "sample_id": sample.sample_id,
                "participant_id": sample.participant_id,
                "label": sample.label,
                "label_index": LABEL_TO_INDEX[sample.label],
                "repetition": f"R{sample.repetition:02d}",
                "source_path": relative_path(sample.path),
                "source_file_hash": sample.sha256,
                "split": split,
                "sequence_shape": "60x126",
                "origin": "Samsung Galaxy A55 phone landmarks",
                "domain": "phone",
            }
        )

    split_rows = {
        "train": [row for row in rows if row["split"] == "train"],
        "validation": [row for row in rows if row["split"] == "validation"],
        "test": [row for row in rows if row["split"] == "test"],
    }
    expected_counts = {"train": 600, "validation": 200, "test": 200}
    actual_counts = {split: len(items) for split, items in split_rows.items()}
    if actual_counts != expected_counts:
        raise ValueError(f"Unexpected split counts: {actual_counts}")
    for label in FINAL_LABELS:
        per_label = Counter(
            row["split"] for row in rows if row["label"] == label
        )
        if per_label != Counter({"train": 15, "validation": 5, "test": 5}):
            raise ValueError(f"Unexpected split for {label}: {dict(per_label)}")
    if len({row["sample_id"] for row in rows}) != 1000:
        raise ValueError("A phone source sample appears more than once.")

    write_csv(PHONE_TRAIN_MANIFEST, split_rows["train"], FIELDS)
    write_csv(PHONE_VALIDATION_MANIFEST, split_rows["validation"], FIELDS)
    write_csv(PHONE_TEST_MANIFEST, split_rows["test"], FIELDS)
    write_json(
        COMBINED_MANIFEST,
        {
            "schema_version": 1,
            "created_at": utc_now(),
            "seed": SEED,
            "policy": "R01-R15 train, R16-R20 validation, R21-R25 test",
            "pilot_assignment_source": relative_path(PILOT_MANIFEST_PATH),
            "pilot_assignments_preserved": pilot_preserved,
            "counts": actual_counts,
            "rows": rows,
        },
    )
    manifest_hashes = {
        relative_path(path): sha256_file(path)
        for path in (
            PHONE_TRAIN_MANIFEST,
            PHONE_VALIDATION_MANIFEST,
            PHONE_TEST_MANIFEST,
            COMBINED_MANIFEST,
        )
    }
    write_json(MANIFEST_HASHES, manifest_hashes)
    write_json(
        TEST_LOCK,
        {
            "status": "locked_not_evaluated",
            "created_at": utc_now(),
            "test_samples": 200,
            "test_manifest": relative_path(PHONE_TEST_MANIFEST),
            "test_manifest_sha256": sha256_file(PHONE_TEST_MANIFEST),
            "selection_prohibition": [
                "hyperparameter tuning",
                "epoch selection",
                "threshold selection",
                "architecture selection",
                "augmentation selection",
                "model comparison",
                "early stopping",
            ],
        },
    )
    SPLIT_REPORT.write_text(
        _report(actual_counts, pilot_preserved, manifest_hashes),
        encoding="utf-8",
    )

    print("Sprint 2.17 Frozen Phone Split")
    print("--------------------------------")
    print("Train: 600")
    print("Validation: 200")
    print("Locked test: 200")
    print("Per label: 15 / 5 / 5")
    print(f"Pilot assignments preserved: {pilot_preserved}")
    print(f"Test manifest SHA-256: {sha256_file(PHONE_TEST_MANIFEST)}")
    print("PASS: frozen leakage-safe phone split created.")
    return 0


def _load_pilot_assignments() -> dict[str, str]:
    rows = read_csv(PILOT_MANIFEST_PATH)
    if len(rows) != 100:
        raise ValueError("The Sprint 2.16A pilot manifest must contain 100 rows.")
    mapping = {"train": "train", "val": "validation", "test": "test"}
    assignments: dict[str, str] = {}
    for row in rows:
        if row["label"] not in PILOT_LABELS:
            raise ValueError("The pilot manifest contains a non-pilot label.")
        split = mapping.get(row["split"])
        if split is None:
            raise ValueError(f"Unknown pilot split: {row['split']}")
        assignments[row["sample_id"]] = split
    if len(assignments) != 100:
        raise ValueError("The pilot manifest contains duplicate sample IDs.")
    return assignments


def _report(
    counts: dict[str, int],
    pilot_preserved: bool,
    hashes: dict[str, str],
) -> str:
    hash_lines = "\n".join(f"- `{path}`: `{digest}`" for path, digest in hashes.items())
    return f"""# Sprint 2.17 Frozen Phone Split

## Status: PASS

- Train: {counts['train']}
- Validation: {counts['validation']}
- Locked test: {counts['test']}
- Per label: 15 train / 5 validation / 5 test
- Pilot assignments preserved: {pilot_preserved}
- Cross-split sample leakage: 0
- Random reshuffling: none
- Deterministic policy: R01-R15 / R16-R20 / R21-R25

The 200-sample phone test set is locked and unavailable to training, model selection, early stopping, and confidence calibration.

## Manifest SHA-256

{hash_lines}
"""


if __name__ == "__main__":
    raise SystemExit(main())

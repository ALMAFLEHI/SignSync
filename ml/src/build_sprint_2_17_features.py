"""Build traceable 756-feature artifacts and training-only augmentation."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np

from labels import ALPHABET_LABELS, DIGIT_LABELS
from sprint_2_16A_experiment_utils import load_augmentation_config
from sprint_2_17_config import (
    AUGMENTATION_SEED,
    CANDIDATE_ROOT,
    DERIVED_AUGMENTATION_DIR,
    DERIVED_CHECKSUM_DIR,
    DERIVED_FEATURE_DIR,
    DERIVED_REPORT_DIR,
    FEATURE_ORDER,
    FINAL_LABELS,
    HISTORICAL_DATASET_PATH,
    HISTORICAL_TRAIN_FEATURES,
    LABEL_TO_INDEX,
    METADATA_DIR,
    PHONE_AUGMENTED_FEATURES,
    PHONE_SAMPLE_DIR,
    PHONE_TEST_FEATURES,
    PHONE_TEST_MANIFEST,
    PHONE_TRAIN_FEATURES,
    PHONE_TRAIN_MANIFEST,
    PHONE_VALIDATION_FEATURES,
    PHONE_VALIDATION_MANIFEST,
    REMOVED_LABELS,
    ROOT,
    ensure_output_directories,
)
from sprint_2_17_utils import (
    augment_sequence,
    load_phone_sequence,
    load_phone_sequences,
    read_csv,
    relative_path,
    sequence_sha256,
    sha256_file,
    stable_rng,
    statistical_features,
    utc_now,
    write_csv,
    write_json,
)


AUGMENTATION_MANIFEST = (
    DERIVED_AUGMENTATION_DIR / "phone_train_augmentation_manifest.csv"
)
HISTORICAL_REPORT_JSON = DERIVED_REPORT_DIR / "historical_dataset_inspection.json"
HISTORICAL_REPORT_CSV = DERIVED_REPORT_DIR / "historical_dataset_per_label.csv"
HISTORICAL_REPORT_MD = DERIVED_REPORT_DIR / "historical_dataset_inspection.md"
FEATURE_REPORT = DERIVED_REPORT_DIR / "feature_preparation_summary.md"
FEATURE_HASHES = DERIVED_CHECKSUM_DIR / "derived_feature_sha256.json"
FEATURE_CONTRACT = METADATA_DIR / "feature_contract.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_output_directories()
    outputs = [
        PHONE_TRAIN_FEATURES,
        PHONE_VALIDATION_FEATURES,
        PHONE_TEST_FEATURES,
        PHONE_AUGMENTED_FEATURES,
        HISTORICAL_TRAIN_FEATURES,
    ]
    if not args.overwrite and any(path.exists() for path in outputs):
        existing = [relative_path(path) for path in outputs if path.exists()]
        raise FileExistsError(f"Feature artifacts already exist: {existing}")

    split_specs = [
        ("train", PHONE_TRAIN_MANIFEST, PHONE_TRAIN_FEATURES, 600),
        (
            "validation",
            PHONE_VALIDATION_MANIFEST,
            PHONE_VALIDATION_FEATURES,
            200,
        ),
        ("test", PHONE_TEST_MANIFEST, PHONE_TEST_FEATURES, 200),
    ]
    phone_summary: dict[str, dict[str, object]] = {}
    for split, manifest, output, expected_count in split_specs:
        phone_summary[split] = _build_phone_features(
            split, manifest, output, expected_count
        )

    augmentation_summary = _build_augmentation()
    historical_summary = _build_historical_features()
    _write_feature_contract()
    shutil.copy2(
        ROOT / "ml" / "config" / "sprint_2_16A_augmentation_config.json",
        METADATA_DIR / "augmentation_config.json",
    )
    hashes = {relative_path(path): sha256_file(path) for path in outputs}
    hashes[relative_path(AUGMENTATION_MANIFEST)] = sha256_file(
        AUGMENTATION_MANIFEST
    )
    write_json(FEATURE_HASHES, hashes)
    FEATURE_REPORT.write_text(
        _feature_report(phone_summary, augmentation_summary, historical_summary),
        encoding="utf-8",
    )

    print("Sprint 2.17 Feature Preparation")
    print("--------------------------------")
    print("Phone train features: 600 x 756")
    print("Phone validation features: 200 x 756")
    print("Locked phone test features: 200 x 756")
    print("Training-only augmented features: 600 x 756")
    print(
        "Historical final-label train features: "
        f"{historical_summary['retained_training_samples']} x 756"
    )
    print("Phone/historical exact overlap: 0")
    print("PASS: feature and augmentation artifacts prepared.")
    return 0


def _build_phone_features(
    split: str,
    manifest_path: Path,
    output_path: Path,
    expected_count: int,
) -> dict[str, object]:
    rows = read_csv(manifest_path)
    if len(rows) != expected_count or {row["split"] for row in rows} != {split}:
        raise ValueError(f"Unexpected {split} manifest contents.")
    sequences = []
    labels = []
    sample_ids = []
    source_paths = []
    source_hashes = []
    for row in rows:
        path = ROOT / Path(row["source_path"])
        sample = load_phone_sequence(path)
        if sample.sample_id != row["sample_id"] or sample.sha256 != row["source_file_hash"]:
            raise ValueError(f"Manifest/source mismatch for {row['sample_id']}.")
        sequences.append(sample.frames)
        labels.append(sample.label)
        sample_ids.append(sample.sample_id)
        source_paths.append(row["source_path"])
        source_hashes.append(sample.sha256)
    X = statistical_features(np.stack(sequences).astype(np.float32))
    y = np.asarray([LABEL_TO_INDEX[label] for label in labels], dtype=np.int64)
    if X.shape != (expected_count, 756) or not np.isfinite(X).all():
        raise ValueError(f"Invalid {split} feature matrix: {X.shape}")
    np.savez_compressed(
        output_path,
        X=X,
        y=y,
        sample_ids=np.asarray(sample_ids),
        labels=np.asarray(labels),
        source_paths=np.asarray(source_paths),
        source_hashes=np.asarray(source_hashes),
        split=np.asarray(split),
    )
    return {
        "samples": expected_count,
        "shape": list(X.shape),
        "labels": len(set(labels)),
        "path": relative_path(output_path),
    }


def _build_augmentation() -> dict[str, object]:
    rows = read_csv(PHONE_TRAIN_MANIFEST)
    config = load_augmentation_config()
    augmented_features = []
    labels = []
    sample_ids = []
    source_ids = []
    manifest_rows = []
    for row in rows:
        sample = load_phone_sequence(ROOT / Path(row["source_path"]))
        augmented, parameters = augment_sequence(
            sample.frames,
            stable_rng(AUGMENTATION_SEED, sample.sample_id),
            config,
        )
        for start in (0, 63):
            source_missing = np.all(sample.frames[:, start : start + 63] == 0.0, axis=1)
            if not np.all(augmented[source_missing, start : start + 63] == 0.0):
                raise ValueError(f"Augmentation changed a zero hand slot: {sample.sample_id}")
        derived_id = f"{sample.sample_id}__aug01"
        augmented_features.append(statistical_features(augmented))
        labels.append(sample.label)
        sample_ids.append(derived_id)
        source_ids.append(sample.sample_id)
        manifest_rows.append(
            {
                "sample_id": derived_id,
                "source_sample_id": sample.sample_id,
                "source_path": relative_path(sample.path),
                "source_file_hash": sample.sha256,
                "label": sample.label,
                "label_index": LABEL_TO_INDEX[sample.label],
                "split": "train",
                "derivative": "aug01",
                **parameters,
            }
        )
    X = np.stack(augmented_features).astype(np.float32)
    y = np.asarray([LABEL_TO_INDEX[label] for label in labels], dtype=np.int64)
    if X.shape != (600, 756) or len(set(sample_ids)) != 600:
        raise ValueError("Expected 600 unique training-only augmented feature rows.")
    np.savez_compressed(
        PHONE_AUGMENTED_FEATURES,
        X=X,
        y=y,
        sample_ids=np.asarray(sample_ids),
        source_sample_ids=np.asarray(source_ids),
        labels=np.asarray(labels),
        split=np.asarray("train"),
        augmentation_seed=np.asarray(AUGMENTATION_SEED),
    )
    write_csv(
        AUGMENTATION_MANIFEST,
        manifest_rows,
        [
            "sample_id",
            "source_sample_id",
            "source_path",
            "source_file_hash",
            "label",
            "label_index",
            "split",
            "derivative",
            "translation_x",
            "translation_y",
            "scale",
            "rotation_degrees",
            "jitter_sigma",
        ],
    )
    return {
        "real_training_samples": 600,
        "augmented_training_samples": 600,
        "effective_phone_training_items": 1200,
        "seed": AUGMENTATION_SEED,
        "translation": [-0.0125, 0.0125],
        "scale": [0.98, 1.02],
        "rotation_degrees": [-2.5, 2.5],
        "jitter_sigma": 0.0015,
        "validation_derivatives": 0,
        "test_derivatives": 0,
    }


def _build_historical_features() -> dict[str, object]:
    with np.load(HISTORICAL_DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X", "sample_ids", "labels", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            raise ValueError(f"Historical dataset missing arrays: {sorted(missing)}")
        X_all = dataset["X"].astype(np.float32)
        ids = dataset["sample_ids"].astype(str)
        labels = dataset["labels"].astype(str)
        splits = dataset["splits"].astype(str)
    if X_all.shape != (805, 60, 126) or not np.isfinite(X_all).all():
        raise ValueError(f"Invalid historical sequence matrix: {X_all.shape}")
    if len(set(ids)) != 805:
        raise ValueError("Historical sample IDs are not unique.")

    final_mask = np.isin(labels, np.asarray(FINAL_LABELS))
    removed_mask = np.isin(labels, np.asarray(REMOVED_LABELS))
    alphabet_mask = np.isin(labels, np.asarray(ALPHABET_LABELS))
    digit_mask = np.isin(labels, np.asarray(DIGIT_LABELS))
    train_mask = final_mask & (splits == "train")
    phone_hashes = {
        sample.sequence_sha256 for sample in load_phone_sequences(PHONE_SAMPLE_DIR)
    }
    historical_final_hashes = {
        sequence_sha256(sequence) for sequence in X_all[final_mask]
    }
    overlap = phone_hashes.intersection(historical_final_hashes)
    if overlap:
        raise ValueError("Exact phone/historical sequence overlap was found.")

    X_train_sequences = X_all[train_mask]
    train_labels = labels[train_mask]
    train_ids = ids[train_mask]
    X_train = statistical_features(X_train_sequences)
    y_train = np.asarray(
        [LABEL_TO_INDEX[label] for label in train_labels], dtype=np.int64
    )
    if X_train.shape != (260, 756):
        raise ValueError(f"Expected 260 historical training rows, found {X_train.shape}.")
    np.savez_compressed(
        HISTORICAL_TRAIN_FEATURES,
        X=X_train,
        y=y_train,
        sample_ids=train_ids,
        labels=train_labels,
        source_dataset=np.asarray(relative_path(HISTORICAL_DATASET_PATH)),
        split=np.asarray("historical_train_only"),
    )

    per_label_rows = []
    for label_index, label in enumerate(FINAL_LABELS):
        mask = labels == label
        counts = Counter(splits[mask])
        per_label_rows.append(
            {
                "label_index": label_index,
                "label": label,
                "total": int(np.sum(mask)),
                "train": counts["train"],
                "validation_excluded": counts["val"],
                "test_excluded": counts["test"],
            }
        )
    write_csv(
        HISTORICAL_REPORT_CSV,
        per_label_rows,
        [
            "label_index",
            "label",
            "total",
            "train",
            "validation_excluded",
            "test_excluded",
        ],
    )
    summary = {
        "source_path": relative_path(HISTORICAL_DATASET_PATH),
        "origin": "P02 laptop-recorded MediaPipe landmark dataset",
        "total_samples": len(X_all),
        "participants": ["P02"],
        "sequence_shape": [60, 126],
        "invalid_samples": 0,
        "final_40_label_samples": int(np.sum(final_mask)),
        "final_40_split_counts": dict(Counter(splits[final_mask])),
        "retained_training_samples": int(np.sum(train_mask)),
        "historical_validation_excluded": int(np.sum(final_mask & (splits == "val"))),
        "historical_test_excluded": int(np.sum(final_mask & (splits == "test"))),
        "removed_label_samples": int(np.sum(removed_mask)),
        "alphabet_samples": int(np.sum(alphabet_mask)),
        "digit_samples": int(np.sum(digit_mask)),
        "phone_exact_sequence_overlap": len(overlap),
        "per_label": per_label_rows,
    }
    write_json(HISTORICAL_REPORT_JSON, summary)
    HISTORICAL_REPORT_MD.write_text(_historical_report(summary), encoding="utf-8")
    return summary


def _write_feature_contract() -> None:
    write_json(
        FEATURE_CONTRACT,
        {
            "schema_version": 1,
            "created_at": utc_now(),
            "sequence_shape": [60, 126],
            "model_input_shape": [1, 756],
            "dtype": "float32",
            "hand_slot_mapping": {
                "left": {"indices": [0, 62], "landmarks": 21, "coordinates": "x,y,z"},
                "right": {"indices": [63, 125], "landmarks": 21, "coordinates": "x,y,z"},
            },
            "statistic_order": FEATURE_ORDER,
            "standard_deviation": {"type": "population", "ddof": 0},
            "flattening_order": (
                "Concatenate six 126-value groups in statistic_order; preserve "
                "left/right slot and landmark x,y,z ordering within each group."
            ),
            "missing_hand_policy": "A missing 63-value hand slot remains all zeros.",
            "additional_flutter_scaling_required": False,
            "canonical_python_implementation": "ml/src/sprint_2_16A_experiment_utils.py:statistical_features",
            "canonical_flutter_implementation": "flutter_app/lib/services/feature_engine.dart",
        },
    )


def _historical_report(summary: dict[str, object]) -> str:
    return f"""# Sprint 2.17 Historical Dataset Inspection

## Status: PASS

- Historical samples: {summary['total_samples']}
- Final 40-label samples: {summary['final_40_label_samples']}
- Final-label historical train retained: {summary['retained_training_samples']}
- Historical validation excluded: {summary['historical_validation_excluded']}
- Historical test excluded: {summary['historical_test_excluded']}
- Alphabet samples excluded: {summary['alphabet_samples']}
- Digit samples excluded: {summary['digit_samples']}
- Removed-label samples excluded: {summary['removed_label_samples']}
- Invalid samples: {summary['invalid_samples']}
- Exact overlap with phone sequences: {summary['phone_exact_sequence_overlap']}
- Participant: P02
- Origin: laptop-recorded MediaPipe landmarks

Only validated historical training rows belonging to the final 40 labels are available to Experiment C. Historical validation and test rows never enter training or phone-domain metrics.
"""


def _feature_report(
    phone: dict[str, dict[str, object]],
    augmentation: dict[str, object],
    historical: dict[str, object],
) -> str:
    return f"""# Sprint 2.17 Feature Preparation

## Status: PASS

- Phone train: {phone['train']['samples']} x 756
- Phone validation: {phone['validation']['samples']} x 756
- Locked phone test: {phone['test']['samples']} x 756
- Training-only augmented phone rows: {augmentation['augmented_training_samples']}
- Historical training rows available to Experiment C: {historical['retained_training_samples']}
- Feature order: mean, population standard deviation, minimum, maximum, first frame, last frame
- Validation augmentation: 0
- Test augmentation: 0
- Phone/historical exact sequence overlap: 0

All derived rows retain source IDs and hashes. No source JSON or historical NPZ was modified.
"""


if __name__ == "__main__":
    raise SystemExit(main())

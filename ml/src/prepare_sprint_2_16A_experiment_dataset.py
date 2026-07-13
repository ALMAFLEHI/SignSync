"""Build the leakage-safe real-data dataset for both Sprint 2.16A experiments."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter

import numpy as np

from labels import (
    ALL_LABELS_V3_76,
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)
from sprint_2_16A_experiment_config import (
    ACTIVE_SCOPE_PATH,
    COMBINED_MANIFEST_PATH,
    DATASET_COUNTS_CSV_PATH,
    EXPERIMENT_DATASET_DIR,
    HISTORICAL_SEQUENCE_DATASET_PATH,
    PARTICIPANT_ID,
    PHONE_SPLIT_MANIFEST_PATH,
    REAL_SEQUENCE_DATASET_PATH,
    phone_split_for_repetition,
)
from sprint_2_16A_experiment_utils import load_phone_sequences, statistical_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Filter historical V2 data, append phone data, and preserve every split."""
    args = parse_args()
    try:
        arrays, rows, summary = prepare_real_dataset()
        write_outputs(arrays, rows, summary, overwrite=args.overwrite)
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        print(f"FAIL: {exc}")
        return 1

    print("Sprint 2.16A Active Real Dataset Preparation")
    print("---------------------------------------------")
    print(f"historical source: {summary['historical_total']}")
    print(f"historical active retained: {summary['historical_active']}")
    print(f"historical removed excluded: {summary['historical_removed']}")
    print(f"phone samples added: {summary['phone_total']}")
    print(f"mixed real samples: {summary['mixed_total']}")
    print(
        "mixed train/val/test: "
        f"{summary['mixed_splits']['train']}/"
        f"{summary['mixed_splits']['val']}/"
        f"{summary['mixed_splits']['test']}"
    )
    print(f"classes: {summary['classes']}")
    print(f"dataset: {REAL_SEQUENCE_DATASET_PATH.as_posix()}")
    print("PASS: leakage-safe active real dataset prepared.")
    return 0


def prepare_real_dataset() -> tuple[dict[str, np.ndarray], list[dict[str, object]], dict[str, object]]:
    """Return active historical and phone arrays plus an auditable manifest."""
    active_scope = json.loads(ACTIVE_SCOPE_PATH.read_text(encoding="utf-8"))
    active_labels = ALPHABET_LABELS + DIGIT_LABELS + active_scope[
        "active_banking_intents"
    ]
    if active_labels != ALL_LABELS_V3_76:
        raise ValueError("Active scope JSON does not match the versioned V3 class order.")
    if active_scope["removed_banking_intents"] != REMOVED_BANKING_INTENTS_V3_10:
        raise ValueError("Active scope JSON removed-label order does not match labels.py.")

    if not HISTORICAL_SEQUENCE_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Missing historical dataset: {HISTORICAL_SEQUENCE_DATASET_PATH.as_posix()}"
        )
    with np.load(HISTORICAL_SEQUENCE_DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            raise ValueError(f"Historical dataset missing arrays: {sorted(missing)}")
        historical = {key: dataset[key] for key in dataset.files}

    historical_labels = historical["labels"].astype(str)
    historical_sample_ids = historical["sample_ids"].astype(str)
    historical_splits = historical["splits"].astype(str)
    if len(historical["X"]) != 805:
        raise ValueError(f"Expected 805 historical rows, found {len(historical['X'])}.")
    if len(historical_sample_ids) != len(set(historical_sample_ids)):
        raise ValueError("Historical dataset contains duplicate sample IDs.")
    active_mask = np.isin(historical_labels, np.asarray(active_labels))
    removed_mask = np.isin(
        historical_labels, np.asarray(REMOVED_BANKING_INTENTS_V3_10)
    )
    if np.any(~active_mask & ~removed_mask):
        unexpected = sorted(set(historical_labels[~active_mask & ~removed_mask]))
        raise ValueError(f"Historical labels outside V2/V3 partition: {unexpected}")

    active_X = historical["X"][active_mask].astype(np.float32, copy=False)
    active_sample_ids = historical_sample_ids[active_mask]
    active_labels_array = historical_labels[active_mask]
    active_splits = historical_splits[active_mask]
    if active_X.shape != (705, 60, 126):
        raise ValueError(f"Expected active historical shape (705, 60, 126), found {active_X.shape}.")
    if not np.isfinite(active_X).all():
        raise ValueError("Historical active data contains NaN or infinite values.")

    phone_samples = load_phone_sequences()
    if len(phone_samples) != 100:
        raise ValueError(f"Expected 100 validated phone samples, found {len(phone_samples)}.")
    phone_X = np.stack([sample.frames for sample in phone_samples]).astype(np.float32)
    phone_ids = np.asarray([sample.sample_id for sample in phone_samples])
    phone_labels = np.asarray([sample.label for sample in phone_samples])
    phone_splits = np.asarray(
        [phone_split_for_repetition(sample.repetition) for sample in phone_samples]
    )

    X = np.concatenate([active_X, phone_X], axis=0)
    sample_ids = np.concatenate([active_sample_ids, phone_ids])
    labels = np.concatenate([active_labels_array, phone_labels])
    splits = np.concatenate([active_splits, phone_splits])
    if len(sample_ids) != len(set(sample_ids.astype(str))):
        raise ValueError("Duplicate sample IDs exist across historical and phone sources.")
    if X.shape != (805, 60, 126) or not np.isfinite(X).all():
        raise ValueError(f"Unexpected mixed real sequence matrix: {X.shape}")

    mapping = {label: index for index, label in enumerate(active_labels)}
    y = np.asarray([mapping[label] for label in labels], dtype=np.int64)
    features = statistical_features(X)
    if features.shape != (805, 756):
        raise ValueError(f"Unexpected mixed feature matrix: {features.shape}")

    rows: list[dict[str, object]] = []
    active_indices = np.flatnonzero(active_mask)
    for output_index, source_index in enumerate(active_indices):
        sample_id = active_sample_ids[output_index]
        rows.append(
            {
                "row_index": output_index,
                "sample_id": sample_id,
                "source_type": "historical",
                "participant": "P02",
                "label": active_labels_array[output_index],
                "repetition": _repetition_from_sample_id(sample_id),
                "split": active_splits[output_index],
                "sequence_source": (
                    f"{HISTORICAL_SEQUENCE_DATASET_PATH.as_posix()}#row={source_index}"
                ),
                "augmentation_status": "original",
            }
        )
    for phone_offset, sample in enumerate(phone_samples):
        rows.append(
            {
                "row_index": len(active_X) + phone_offset,
                "sample_id": sample.sample_id,
                "source_type": "phone",
                "participant": PARTICIPANT_ID,
                "label": sample.label,
                "repetition": sample.repetition,
                "split": phone_split_for_repetition(sample.repetition),
                "sequence_source": sample.path.as_posix(),
                "augmentation_status": "original",
            }
        )

    _validate_leakage(rows)
    historical_split_counts = Counter(active_splits)
    phone_split_counts = Counter(phone_splits)
    mixed_split_counts = Counter(splits)
    expected_historical = {"train": 488, "val": 76, "test": 141}
    expected_phone = {"train": 60, "val": 20, "test": 20}
    expected_mixed = {"train": 548, "val": 96, "test": 161}
    if dict(historical_split_counts) != expected_historical:
        raise ValueError(f"Unexpected active historical splits: {dict(historical_split_counts)}")
    if dict(phone_split_counts) != expected_phone:
        raise ValueError(f"Unexpected phone splits: {dict(phone_split_counts)}")
    if dict(mixed_split_counts) != expected_mixed:
        raise ValueError(f"Unexpected mixed splits: {dict(mixed_split_counts)}")

    arrays = {
        "X_sequences": X.astype(np.float32, copy=False),
        "X_features": features.astype(np.float32, copy=False),
        "y": y,
        "sample_ids": sample_ids,
        "labels": labels,
        "splits": splits,
        "source_types": np.asarray([row["source_type"] for row in rows]),
        "participants": np.asarray([row["participant"] for row in rows]),
        "label_names": np.asarray(active_labels),
        "feature_order": np.asarray(
            ["mean", "std", "min", "max", "first_frame", "last_frame"]
        ),
    }
    class_counts = Counter(labels)
    summary = {
        "historical_total": len(historical["X"]),
        "historical_active": len(active_X),
        "historical_removed": int(np.sum(removed_mask)),
        "historical_splits": dict(historical_split_counts),
        "phone_total": len(phone_X),
        "phone_splits": dict(phone_split_counts),
        "mixed_total": len(X),
        "mixed_splits": dict(mixed_split_counts),
        "classes": len(active_labels),
        "minimum_class_count": min(class_counts.values()),
        "maximum_class_count": max(class_counts.values()),
        "class_imbalance_ratio": max(class_counts.values()) / min(class_counts.values()),
    }
    return arrays, rows, summary


def write_outputs(
    arrays: dict[str, np.ndarray],
    rows: list[dict[str, object]],
    summary: dict[str, object],
    overwrite: bool,
) -> None:
    """Save only new controlled-experiment datasets and manifests."""
    if REAL_SEQUENCE_DATASET_PATH.exists() and not overwrite:
        raise FileExistsError(
            f"Controlled dataset already exists: {REAL_SEQUENCE_DATASET_PATH.as_posix()}"
        )
    EXPERIMENT_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(REAL_SEQUENCE_DATASET_PATH, **arrays)

    COMBINED_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with COMBINED_MANIFEST_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(
        (row["source_type"], row["split"], row["label"]) for row in rows
    )
    DATASET_COUNTS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_COUNTS_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["source_type", "split", "label", "count"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for source_type, split, label in sorted(counts):
            writer.writerow(
                {
                    "source_type": source_type,
                    "split": split,
                    "label": label,
                    "count": counts[(source_type, split, label)],
                }
            )

    mapping = {
        label: index for index, label in enumerate(arrays["label_names"].astype(str))
    }
    (EXPERIMENT_DATASET_DIR / "signsync_scope_v3_40_label_mapping.json").write_text(
        json.dumps(mapping, indent=2), encoding="utf-8"
    )
    (
        EXPERIMENT_DATASET_DIR / "signsync_scope_v3_40_label_groups.json"
    ).write_text(
        json.dumps(
            {
                "all_labels": ALL_LABELS_V3_76,
                "alphabet_mode": ALPHABET_LABELS,
                "number_mode": DIGIT_LABELS,
                "banking_intent_mode": BANKING_INTENTS_V3_40,
                "removed_banking_intents": REMOVED_BANKING_INTENTS_V3_10,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (EXPERIMENT_DATASET_DIR / "preprocessing_config.json").write_text(
        json.dumps(
            {
                "sequence_shape": [60, 126],
                "feature_order": [
                    "mean",
                    "std",
                    "min",
                    "max",
                    "first_frame",
                    "last_frame",
                ],
                "feature_shape": [756],
                "standard_deviation_ddof": 0,
                "output_classes": 76,
                "summary": summary,
                "phone_split_manifest": PHONE_SPLIT_MANIFEST_PATH.as_posix(),
                "combined_manifest": COMBINED_MANIFEST_PATH.as_posix(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _validate_leakage(rows: list[dict[str, object]]) -> None:
    split_by_id: dict[str, set[str]] = {}
    for row in rows:
        split_by_id.setdefault(str(row["sample_id"]), set()).add(str(row["split"]))
    leaked = {sample_id: splits for sample_id, splits in split_by_id.items() if len(splits) > 1}
    if leaked:
        raise ValueError(f"Cross-split sample leakage found: {leaked}")


def _repetition_from_sample_id(sample_id: str) -> int:
    match = re.search(r"_R(\d+)$", sample_id)
    if not match:
        raise ValueError(f"Cannot parse repetition from sample ID: {sample_id}")
    return int(match.group(1))


if __name__ == "__main__":
    raise SystemExit(main())

"""Check the Sprint 2.16A mixed laptop + phone dataset when it exists."""

from __future__ import annotations

import csv
from collections import Counter

from labels import ALL_LABELS_V3_76, REMOVED_BANKING_INTENTS_V3_10
from phone_dataset_config import (
    DATASET_REPORT_MD_PATH,
    LANDMARK_DIMENSION,
    PHONE_PILOT_DATASET_PATH,
    TARGET_FRAMES,
    WEAK_LABELS,
)


def main() -> int:
    """Validate the phone-augmented dataset or report pending status."""
    rows: list[dict[str, str]] = []
    if not PHONE_PILOT_DATASET_PATH.exists():
        print("PENDING: phone-augmented dataset has not been created yet.")
        print(f"expected path: {PHONE_PILOT_DATASET_PATH.as_posix()}")
        return 0

    import numpy as np

    with np.load(PHONE_PILOT_DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            print(f"FAIL: missing arrays: {sorted(missing)}")
            return 1
        X = dataset["X"]
        y = dataset["y"]
        labels = dataset["labels"].astype(str)
        label_names = dataset["label_names"].astype(str).tolist()
        sample_ids = dataset["sample_ids"].astype(str)
        splits = dataset["splits"].astype(str)

    rows.append({"check": "X rank", "status": "PASS" if X.ndim == 3 else "FAIL", "detail": str(X.shape)})
    v3_mapping = {label: index for index, label in enumerate(ALL_LABELS_V3_76)}
    rows.append(
        {
            "check": "sequence shape",
            "status": "PASS" if X.shape[1:] == (TARGET_FRAMES, LANDMARK_DIMENSION) else "FAIL",
            "detail": str(X.shape[1:]),
        }
    )
    rows.append(
        {
            "check": "active class contract",
            "status": "PASS" if label_names == ALL_LABELS_V3_76 else "FAIL",
            "detail": str(len(label_names)),
        }
    )
    rows.append(
        {
            "check": "active labels only",
            "status": "PASS" if set(labels) == set(ALL_LABELS_V3_76) else "FAIL",
            "detail": str(len(set(labels))),
        }
    )
    rows.append(
        {
            "check": "removed labels excluded",
            "status": "PASS"
            if not set(labels).intersection(REMOVED_BANKING_INTENTS_V3_10)
            else "FAIL",
            "detail": "0 removed labels expected",
        }
    )
    rows.append(
        {
            "check": "unique sample IDs",
            "status": "PASS" if len(sample_ids) == len(set(sample_ids)) else "FAIL",
            "detail": str(len(sample_ids)),
        }
    )
    rows.append(
        {
            "check": "label indices",
            "status": "PASS"
            if len(y)
            and np.array_equal(
                y,
                np.asarray(
                    [v3_mapping[label] for label in labels],
                    dtype=np.int64,
                ),
            )
            else "FAIL",
            "detail": "indices match V3 label order" if len(y) else "empty",
        }
    )
    rows.append({"check": "y length", "status": "PASS" if len(y) == len(X) else "FAIL", "detail": str(len(y))})
    rows.append(
        {
            "check": "finite values",
            "status": "PASS" if np.isfinite(X).all() else "FAIL",
            "detail": "finite" if np.isfinite(X).all() else "NaN/Inf found",
        }
    )
    split_counts = Counter(splits)
    label_counts = Counter(labels)
    for split in ("train", "val", "test"):
        rows.append({"check": f"split_{split}", "status": "PASS", "detail": str(split_counts[split])})
    for label in WEAK_LABELS:
        rows.append({"check": f"weak_label_{label}", "status": "PASS", "detail": str(label_counts[label])})

    passed = all(row["status"] == "PASS" for row in rows)
    csv_path = DATASET_REPORT_MD_PATH.with_suffix(".check.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    print("Sprint 2.16A Phone-Augmented Dataset Check")
    print("------------------------------------------")
    print(f"dataset: {PHONE_PILOT_DATASET_PATH.as_posix()}")
    print(f"X shape: {tuple(X.shape)}")
    print(f"split counts: {dict(split_counts)}")
    print("PASS: phone-augmented dataset check passed." if passed else "FAIL: dataset check failed.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

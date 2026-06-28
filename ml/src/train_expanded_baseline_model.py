"""Train and select Sprint 2.12 scikit-learn baselines on the expanded V2 dataset."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from typing import Any

import numpy as np

from expanded_dataset_config import (
    DATASET_PATH,
    EXPECTED_TEST_SAMPLES,
    EXPECTED_TRAIN_SAMPLES,
    EXPECTED_VAL_SAMPLES,
    LABEL_GROUPS_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_LABEL_GROUPS_PATH,
    MODEL_LABEL_NAMES_PATH,
    MODEL_OUTPUT_DIR,
    MODEL_PATH,
    SPLIT_CSV_PATH,
    TRAINING_REPORT_CSV_PATH,
    TRAINING_REPORT_MD_PATH,
)
from expanded_model_feature_utils import FEATURE_MODE, STATS_FEATURE_SIZE, create_statistical_features


def parse_args() -> argparse.Namespace:
    """Parse safe training options for the expanded baseline workflow."""
    parser = argparse.ArgumentParser(
        description="Train Sprint 2.12 expanded-dataset scikit-learn baseline models."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def load_dataset() -> dict[str, np.ndarray]:
    """Load the prepared expanded dataset with required-array validation."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Expanded dataset is missing: {DATASET_PATH.as_posix()}")
    with np.load(DATASET_PATH, allow_pickle=False) as dataset:
        required = {"X", "y", "sample_ids", "labels", "label_names", "splits"}
        missing = required.difference(dataset.files)
        if missing:
            raise ValueError(f"Expanded dataset is missing arrays: {sorted(missing)}")
        return {key: dataset[key] for key in dataset.files}


def split_counts(dataset: dict[str, np.ndarray]) -> Counter[str]:
    """Return train, validation, and test counts from the prepared dataset."""
    return Counter(dataset["splits"].astype(str))


def validate_split_csv(dataset: dict[str, np.ndarray]) -> None:
    """Ensure the saved CSV split assignments match the dataset sample IDs."""
    if not SPLIT_CSV_PATH.exists():
        raise FileNotFoundError(f"Split CSV is missing: {SPLIT_CSV_PATH.as_posix()}")
    with SPLIT_CSV_PATH.open("r", newline="", encoding="utf-8") as split_file:
        rows = list(csv.DictReader(split_file))
    if len(rows) != len(dataset["sample_ids"]):
        raise ValueError("Split CSV row count does not match the expanded dataset.")
    csv_lookup = {row["sample_id"]: row.get("split", "") for row in rows}
    sample_ids = dataset["sample_ids"].astype(str)
    splits = dataset["splits"].astype(str)
    if set(csv_lookup) != set(sample_ids):
        raise ValueError("Split CSV sample IDs do not match the expanded dataset.")
    if any(csv_lookup[sample_id] != split for sample_id, split in zip(sample_ids, splits)):
        raise ValueError("Split CSV assignments do not match the expanded dataset.")


def build_candidate_models(random_state: int) -> list[tuple[str, Any]]:
    """Create laptop-friendly classifiers; scaling is embedded for logistic regression."""
    from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return [
        (
            "LogisticRegression",
            make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=2500, random_state=random_state, solver="lbfgs"),
            ),
        ),
        (
            "RandomForestClassifier",
            RandomForestClassifier(
                n_estimators=250, random_state=random_state, class_weight="balanced", n_jobs=-1
            ),
        ),
        (
            "ExtraTreesClassifier",
            ExtraTreesClassifier(
                n_estimators=250, random_state=random_state, class_weight="balanced", n_jobs=-1
            ),
        ),
    ]


def train_candidates(
    features: np.ndarray, y: np.ndarray, splits: np.ndarray, random_state: int
) -> list[dict[str, object]]:
    """Fit each candidate only on train data and score only against validation data."""
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support

    train_mask = splits == "train"
    val_mask = splits == "val"
    results: list[dict[str, object]] = []
    for name, model in build_candidate_models(random_state):
        model.fit(features[train_mask], y[train_mask])
        predictions = model.predict(features[val_mask])
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            y[val_mask], predictions, average="macro", zero_division=0
        )
        results.append(
            {
                "model_name": name,
                "model": model,
                "validation_accuracy": float(accuracy_score(y[val_mask], predictions)),
                "validation_macro_precision": float(macro_precision),
                "validation_macro_recall": float(macro_recall),
                "validation_macro_f1": float(macro_f1),
            }
        )
    return results


def select_best(results: list[dict[str, object]]) -> dict[str, object]:
    """Select by validation macro F1 and then validation accuracy without test leakage."""
    priority = {"ExtraTreesClassifier": 3, "RandomForestClassifier": 2, "LogisticRegression": 1}
    return max(
        results,
        key=lambda result: (
            float(result["validation_macro_f1"]),
            float(result["validation_accuracy"]),
            priority[str(result["model_name"])],
        ),
    )


def write_reports(
    dataset: dict[str, np.ndarray], features: np.ndarray, results: list[dict[str, object]], best: dict[str, object]
) -> None:
    """Write candidate comparison reports and model metadata after training succeeds."""
    TRAINING_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRAINING_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        fieldnames = [
            "model_name", "validation_accuracy", "validation_macro_precision",
            "validation_macro_recall", "validation_macro_f1", "selected_best",
        ]
        writer = csv.DictWriter(report_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "model_name": result["model_name"],
                    "validation_accuracy": f"{float(result['validation_accuracy']):.6f}",
                    "validation_macro_precision": f"{float(result['validation_macro_precision']):.6f}",
                    "validation_macro_recall": f"{float(result['validation_macro_recall']):.6f}",
                    "validation_macro_f1": f"{float(result['validation_macro_f1']):.6f}",
                    "selected_best": "yes" if result is best else "no",
                }
            )
    counts = split_counts(dataset)
    candidate_text = "\n".join(
        f"- {result['model_name']}: validation accuracy {float(result['validation_accuracy']):.4f}, "
        f"macro F1 {float(result['validation_macro_f1']):.4f}"
        for result in results
    )
    content = f"""# Sprint 2.12 Expanded Baseline Training Report

## Dataset
- Dataset path: {DATASET_PATH.as_posix()}
- X shape: {tuple(dataset['X'].shape)}
- Feature mode: {FEATURE_MODE}
- Feature shape: {tuple(features.shape)}
- Labels: {len(dataset['label_names'])}
- Train/validation/test: {counts['train']}/{counts['val']}/{counts['test']}

## Candidate Models
{candidate_text}

## Selected Model
- Model: {best['model_name']}
- Validation accuracy: {float(best['validation_accuracy']):.4f}
- Validation macro F1: {float(best['validation_macro_f1']):.4f}
- Model output: {MODEL_PATH.as_posix()}

## Scope Note
This is a single-participant controlled dataset baseline. It measures the expanded V2 pipeline, not production accuracy.
"""
    TRAINING_REPORT_MD_PATH.write_text(content, encoding="utf-8")
    METRICS_SUMMARY_PATH.write_text(
        json.dumps(
            {
                "dataset_path": DATASET_PATH.as_posix(),
                "feature_mode": FEATURE_MODE,
                "feature_shape": list(features.shape),
                "split_counts": dict(counts),
                "selected_model": best["model_name"],
                "validation_accuracy": float(best["validation_accuracy"]),
                "validation_macro_f1": float(best["validation_macro_f1"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def print_dry_run(dataset: dict[str, np.ndarray]) -> None:
    """Print future training inputs without fitting models or writing artifacts."""
    counts = split_counts(dataset)
    features = create_statistical_features(dataset["X"])
    print("Sprint 2.12 Expanded Baseline Training Dry Run")
    print("----------------------------------------------")
    print(f"dataset path: {DATASET_PATH.as_posix()}")
    print(f"X shape: {tuple(dataset['X'].shape)}")
    print(f"feature shape: {tuple(features.shape)}")
    print(f"expected feature width: {STATS_FEATURE_SIZE}")
    print(f"train/val/test: {counts['train']}/{counts['val']}/{counts['test']}")
    print("candidates: LogisticRegression, RandomForestClassifier, ExtraTreesClassifier")
    print("Dry run completed. No model training or files were created.")


def main() -> int:
    """Dry-run or train expanded baseline candidates, never using test data for selection."""
    args = parse_args()
    try:
        dataset = load_dataset()
        validate_split_csv(dataset)
        counts = split_counts(dataset)
        expected_counts = {
            "train": EXPECTED_TRAIN_SAMPLES,
            "val": EXPECTED_VAL_SAMPLES,
            "test": EXPECTED_TEST_SAMPLES,
        }
        if dict(counts) != expected_counts:
            raise ValueError(f"Unexpected dataset split counts: {dict(counts)}")
        if args.dry_run:
            print_dry_run(dataset)
            return 0
        if MODEL_PATH.exists() and not args.overwrite:
            print(f"Model already exists: {MODEL_PATH.as_posix()}. Use --overwrite to replace it.")
            return 1

        import joblib

        features = create_statistical_features(dataset["X"])
        results = train_candidates(features, dataset["y"], dataset["splits"].astype(str), args.random_state)
        best = select_best(results)
        MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(best["model"], MODEL_PATH)
        MODEL_LABEL_NAMES_PATH.write_text(
            json.dumps(dataset["label_names"].astype(str).tolist(), indent=2),
            encoding="utf-8",
        )
        if not LABEL_GROUPS_PATH.exists():
            raise FileNotFoundError(f"Missing dataset label groups: {LABEL_GROUPS_PATH.as_posix()}")
        MODEL_LABEL_GROUPS_PATH.write_text(LABEL_GROUPS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        write_reports(dataset, features, results, best)
        print("Sprint 2.12 Expanded Baseline Training Summary")
        print("----------------------------------------------")
        print(f"selected model: {best['model_name']}")
        print(f"validation accuracy: {float(best['validation_accuracy']):.4f}")
        print(f"validation macro F1: {float(best['validation_macro_f1']):.4f}")
        print(f"model path: {MODEL_PATH.as_posix()}")
        print("next command: python ml/src/evaluate_expanded_baseline_model.py")
        return 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

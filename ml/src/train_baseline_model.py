"""Train Sprint 2.6 baseline classifiers on the prepared trial dataset."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from model_config import (
    DATASET_PATH,
    DEFAULT_FEATURE_MODE,
    FEATURE_MODES,
    FLATTEN_FEATURE_SIZE,
    LABEL_NAMES_OUTPUT_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_OUTPUT_PATH,
    MODEL_OUTPUT_DIR,
    SCALER_OUTPUT_PATH,
    STATS_FEATURE_SIZE,
    TRAINING_REPORT_CSV_PATH,
    TRAINING_REPORT_MD_PATH,
)


def parse_args() -> argparse.Namespace:
    """Parse baseline training options."""
    parser = argparse.ArgumentParser(
        description="Train Sprint 2.6 baseline recognition models."
    )
    parser.add_argument("--feature-mode", choices=FEATURE_MODES, default=DEFAULT_FEATURE_MODE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def load_dataset() -> dict[str, np.ndarray]:
    """Load the prepared Sprint 2.5 dataset."""
    dataset_path = Path(DATASET_PATH)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path.as_posix()}")

    with np.load(dataset_path, allow_pickle=False) as dataset:
        return {key: dataset[key] for key in dataset.files}


def create_features(X: np.ndarray, feature_mode: str) -> np.ndarray:
    """Convert sequence landmarks into model-ready feature vectors."""
    if feature_mode == "stats":
        means = X.mean(axis=1)
        stds = X.std(axis=1)
        mins = X.min(axis=1)
        maxs = X.max(axis=1)
        first_frames = X[:, 0, :]
        last_frames = X[:, -1, :]
        return np.concatenate([means, stds, mins, maxs, first_frames, last_frames], axis=1)

    if feature_mode == "flatten":
        return X.reshape(X.shape[0], -1)

    raise ValueError(f"Unsupported feature mode: {feature_mode}")


def split_data(dataset: dict[str, np.ndarray], features: np.ndarray) -> dict[str, np.ndarray]:
    """Return train and validation arrays only for model selection."""
    splits = dataset["splits"].astype(str)
    train_mask = splits == "train"
    val_mask = splits == "val"
    return {
        "X_train": features[train_mask],
        "y_train": dataset["y"][train_mask],
        "X_val": features[val_mask],
        "y_val": dataset["y"][val_mask],
    }


def train_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    random_state: int,
) -> list[dict[str, object]]:
    """Train Logistic Regression and Random Forest baselines."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler

    results: list[dict[str, object]] = []

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    logistic_model = LogisticRegression(
        max_iter=2000,
        random_state=random_state,
        solver="lbfgs",
    )
    logistic_model.fit(X_train_scaled, y_train)
    logistic_predictions = logistic_model.predict(X_val_scaled)
    results.append(
        {
            "model_name": "LogisticRegression",
            "model": logistic_model,
            "scaler": scaler,
            "validation_accuracy": float(accuracy_score(y_val, logistic_predictions)),
            "uses_scaler": True,
        }
    )

    forest_model = RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        class_weight="balanced",
    )
    forest_model.fit(X_train, y_train)
    forest_predictions = forest_model.predict(X_val)
    results.append(
        {
            "model_name": "RandomForestClassifier",
            "model": forest_model,
            "scaler": None,
            "validation_accuracy": float(accuracy_score(y_val, forest_predictions)),
            "uses_scaler": False,
        }
    )

    return results


def select_best_model(results: list[dict[str, object]]) -> dict[str, object]:
    """Select the best validation model with stable tie-breaking."""
    return max(
        results,
        key=lambda result: (
            float(result["validation_accuracy"]),
            1 if result["model_name"] == "LogisticRegression" else 0,
        ),
    )


def write_training_reports(
    dataset: dict[str, np.ndarray],
    features: np.ndarray,
    feature_mode: str,
    results: list[dict[str, object]],
    best_result: dict[str, object],
) -> None:
    """Write CSV, Markdown, and JSON training summaries."""
    TRAINING_REPORT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with TRAINING_REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(
            report_file,
            fieldnames=[
                "model_name",
                "feature_mode",
                "validation_accuracy",
                "selected_best",
                "uses_scaler",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "model_name": result["model_name"],
                    "feature_mode": feature_mode,
                    "validation_accuracy": f"{float(result['validation_accuracy']):.6f}",
                    "selected_best": "yes" if result is best_result else "no",
                    "uses_scaler": "yes" if result["uses_scaler"] else "no",
                }
            )

    splits = dataset["splits"].astype(str)
    train_count = int(np.count_nonzero(splits == "train"))
    val_count = int(np.count_nonzero(splits == "val"))
    markdown_rows = "\n".join(
        f"- {result['model_name']}: validation accuracy {float(result['validation_accuracy']):.4f}"
        for result in results
    )
    content = f"""# Sprint 2.6 Training Report

## Dataset
- Dataset path: {DATASET_PATH}
- X shape: {tuple(dataset['X'].shape)}
- Feature mode: {feature_mode}
- Feature shape: {tuple(features.shape)}
- Number of labels: {len(dataset['label_names'])}
- Train samples: {train_count}
- Validation samples: {val_count}

## Tested Models
{markdown_rows}

## Selected Best Model
- Model: {best_result['model_name']}
- Validation accuracy: {float(best_result['validation_accuracy']):.4f}
- Model output path: {MODEL_OUTPUT_PATH.as_posix()}

## Important Note
This is a trial baseline model trained on only 55 samples. It validates the machine learning pipeline but does not represent final production performance.
"""
    TRAINING_REPORT_MD_PATH.write_text(content, encoding="utf-8")

    summary = {
        "dataset_path": DATASET_PATH,
        "x_shape": list(dataset["X"].shape),
        "feature_mode": feature_mode,
        "feature_shape": list(features.shape),
        "number_of_labels": int(len(dataset["label_names"])),
        "train_samples": train_count,
        "validation_samples": val_count,
        "tested_models": [
            {
                "model_name": str(result["model_name"]),
                "validation_accuracy": float(result["validation_accuracy"]),
                "uses_scaler": bool(result["uses_scaler"]),
            }
            for result in results
        ],
        "selected_best_model": str(best_result["model_name"]),
        "selected_validation_accuracy": float(best_result["validation_accuracy"]),
        "scaler_required": bool(best_result["uses_scaler"]),
        "model_output_path": MODEL_OUTPUT_PATH.as_posix(),
        "scaler_output_path": SCALER_OUTPUT_PATH.as_posix(),
    }
    METRICS_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def print_dry_run(dataset: dict[str, np.ndarray], feature_mode: str) -> None:
    """Print expected training configuration without fitting models."""
    feature_size = STATS_FEATURE_SIZE if feature_mode == "stats" else FLATTEN_FEATURE_SIZE
    splits = dataset["splits"].astype(str)
    print("Sprint 2.6 Baseline Training Dry Run")
    print("------------------------------------")
    print(f"dataset path: {DATASET_PATH}")
    print(f"X shape: {tuple(dataset['X'].shape)}")
    print(f"y shape: {tuple(dataset['y'].shape)}")
    print(f"feature mode: {feature_mode}")
    print(f"expected feature shape: ({dataset['X'].shape[0]}, {feature_size})")
    print(f"number of labels: {len(dataset['label_names'])}")
    print(f"train samples: {int(np.count_nonzero(splits == 'train'))}")
    print(f"validation samples: {int(np.count_nonzero(splits == 'val'))}")
    print(f"model output path: {MODEL_OUTPUT_PATH.as_posix()}")
    print(f"scaler output path: {SCALER_OUTPUT_PATH.as_posix()}")
    print(f"label names output path: {LABEL_NAMES_OUTPUT_PATH.as_posix()}")
    print("Dry run completed. No model training was performed and no files were saved.")


def main() -> int:
    """Run baseline training or a dry-run only."""
    args = parse_args()
    dataset = load_dataset()

    if args.dry_run:
        print_dry_run(dataset, args.feature_mode)
        return 0

    if MODEL_OUTPUT_PATH.exists() and not args.overwrite:
        print(
            f"Model output already exists: {MODEL_OUTPUT_PATH.as_posix()}. "
            "Use --overwrite to replace it."
        )
        return 1

    import joblib

    features = create_features(dataset["X"], args.feature_mode)
    split_arrays = split_data(dataset, features)
    results = train_models(
        split_arrays["X_train"],
        split_arrays["y_train"],
        split_arrays["X_val"],
        split_arrays["y_val"],
        args.random_state,
    )
    best_result = select_best_model(results)

    Path(MODEL_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    joblib.dump(best_result["model"], MODEL_OUTPUT_PATH)
    if best_result["uses_scaler"]:
        joblib.dump(best_result["scaler"], SCALER_OUTPUT_PATH)
    elif SCALER_OUTPUT_PATH.exists() and args.overwrite:
        SCALER_OUTPUT_PATH.unlink()

    label_names = [str(label) for label in dataset["label_names"]]
    LABEL_NAMES_OUTPUT_PATH.write_text(json.dumps(label_names, indent=2), encoding="utf-8")
    write_training_reports(dataset, features, args.feature_mode, results, best_result)

    print("Sprint 2.6 Baseline Training Summary")
    print("------------------------------------")
    print(f"best model name: {best_result['model_name']}")
    print(f"validation accuracy: {float(best_result['validation_accuracy']):.4f}")
    print(f"model output path: {MODEL_OUTPUT_PATH.as_posix()}")
    print(f"training report CSV: {TRAINING_REPORT_CSV_PATH.as_posix()}")
    print(f"training report Markdown: {TRAINING_REPORT_MD_PATH.as_posix()}")
    print("next command: python ml/src/evaluate_baseline_model.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

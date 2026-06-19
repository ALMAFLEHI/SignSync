"""Check that the existing Sprint 2.5 and Sprint 2.6 inputs are ready to validate."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from pipeline_validation_config import (
    CONFUSION_MATRIX_PATH,
    DATASET_PATH,
    EVALUATION_REPORT_PATH,
    EXPECTED_LABEL_COUNT,
    EXPECTED_SPLIT_COUNTS,
    EXPECTED_X_SHAPE,
    EXPECTED_Y_SHAPE,
    INPUT_CHECK_REPORT_MD,
    LABEL_MAPPING_PATH,
    LABEL_NAMES_PATH,
    MODEL_PATH,
    SPLIT_CSV_PATH,
    STATS_FEATURE_SIZE,
    TRAINING_REPORT_PATH,
    report_path,
)


def check_path(name: str, path: str | Path) -> tuple[bool, str]:
    """Check one required path without changing it."""
    resolved_path = Path(path)
    passed = resolved_path.exists()
    detail = resolved_path.as_posix() if passed else f"missing: {resolved_path.as_posix()}"
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
    return passed, detail


def load_dataset_summary() -> tuple[bool, dict[str, object]]:
    """Load the prepared dataset and validate its expected trial dimensions."""
    try:
        with np.load(DATASET_PATH, allow_pickle=False) as dataset:
            X = dataset["X"]
            y = dataset["y"]
            label_names = dataset["label_names"]
            splits = dataset["splits"].astype(str)
    except Exception as exc:
        print(f"FAIL dataset load: {exc}")
        return False, {"error": str(exc)}

    split_counts = Counter(splits)
    checks = {
        "X shape": tuple(X.shape) == EXPECTED_X_SHAPE,
        "y shape": tuple(y.shape) == EXPECTED_Y_SHAPE,
        "label count": len(label_names) == EXPECTED_LABEL_COUNT,
        "train count": split_counts["train"] == EXPECTED_SPLIT_COUNTS["train"],
        "val count": split_counts["val"] == EXPECTED_SPLIT_COUNTS["val"],
        "test count": split_counts["test"] == EXPECTED_SPLIT_COUNTS["test"],
    }
    print(f"X shape: {tuple(X.shape)}")
    print(f"y shape: {tuple(y.shape)}")
    print(f"number of labels: {len(label_names)}")
    print(
        "train/val/test counts: "
        f"{split_counts['train']}/{split_counts['val']}/{split_counts['test']}"
    )
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")

    return all(checks.values()), {
        "x_shape": list(X.shape),
        "y_shape": list(y.shape),
        "label_count": int(len(label_names)),
        "split_counts": dict(split_counts),
        "stats_feature_shape": [int(X.shape[0]), STATS_FEATURE_SIZE],
    }


def check_saved_model() -> tuple[bool, str]:
    """Load the saved model and ensure its expected stats feature width is 756."""
    try:
        import joblib

        model = joblib.load(MODEL_PATH)
        feature_count = getattr(model, "n_features_in_", None)
        passed = feature_count == STATS_FEATURE_SIZE
        detail = (
            f"{type(model).__name__}; n_features_in_={feature_count}; "
            f"expected={STATS_FEATURE_SIZE}"
        )
        print(f"{'PASS' if passed else 'FAIL'} saved model load: {detail}")
        return passed, detail
    except Exception as exc:
        detail = str(exc)
        print(f"FAIL saved model load: {detail}")
        return False, detail


def check_label_names() -> tuple[bool, str]:
    """Load label names and confirm their trial vocabulary count."""
    try:
        label_names = json.loads(Path(LABEL_NAMES_PATH).read_text(encoding="utf-8"))
        passed = isinstance(label_names, list) and len(label_names) == EXPECTED_LABEL_COUNT
        detail = f"label names count={len(label_names) if isinstance(label_names, list) else 'invalid'}"
        print(f"{'PASS' if passed else 'FAIL'} label names JSON: {detail}")
        return passed, detail
    except Exception as exc:
        detail = str(exc)
        print(f"FAIL label names JSON: {detail}")
        return False, detail


def write_report(checks: list[tuple[str, bool, str]], dataset_summary: dict[str, object]) -> None:
    """Write a reusable Markdown evidence report for the input check."""
    output_path = report_path(INPUT_CHECK_REPORT_MD)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {name} | {'PASS' if passed else 'FAIL'} | {detail} |"
        for name, passed, detail in checks
    )
    content = f"""# Sprint 2.7 Input Check Report

## Result
| Check | Status | Detail |
| --- | --- | --- |
{rows}

## Dataset Summary
- X shape: {dataset_summary.get('x_shape', 'not available')}
- y shape: {dataset_summary.get('y_shape', 'not available')}
- Number of labels: {dataset_summary.get('label_count', 'not available')}
- Train/validation/test counts: {dataset_summary.get('split_counts', 'not available')}
- Stats feature shape: {dataset_summary.get('stats_feature_shape', 'not available')}

## Scope
This check only reads the prepared dataset and saved model artifacts. It does not retrain a model or modify the dataset.
"""
    output_path.write_text(content, encoding="utf-8")


def main() -> int:
    """Run the Sprint 2.7 input checks and write the Markdown report."""
    print("Sprint 2.7 Input Check")
    print("----------------------")

    checks: list[tuple[str, bool, str]] = []
    for name, path in [
        ("Sprint 2.5 dataset", DATASET_PATH),
        ("Sprint 2.6 model", MODEL_PATH),
        ("Sprint 2.6 label names", LABEL_NAMES_PATH),
        ("Sprint 2.5 split CSV", SPLIT_CSV_PATH),
        ("Sprint 2.5 label mapping", LABEL_MAPPING_PATH),
        ("Sprint 2.6 training report", TRAINING_REPORT_PATH),
        ("Sprint 2.6 evaluation report", EVALUATION_REPORT_PATH),
        ("Sprint 2.6 confusion matrix", CONFUSION_MATRIX_PATH),
    ]:
        passed, detail = check_path(name, path)
        checks.append((name, passed, detail))

    dataset_passed, dataset_summary = load_dataset_summary()
    checks.append(("Sprint 2.5 dataset contents", dataset_passed, str(dataset_summary)))
    model_passed, model_detail = check_saved_model()
    checks.append(("Saved model feature shape", model_passed, model_detail))
    labels_passed, labels_detail = check_label_names()
    checks.append(("Saved label names", labels_passed, labels_detail))
    write_report(checks, dataset_summary)

    all_passed = all(passed for _, passed, _ in checks)
    print(f"input check report: {report_path(INPUT_CHECK_REPORT_MD).as_posix()}")
    print("PASS: Sprint 2.7 input check passed." if all_passed else "FAIL: Sprint 2.7 input check failed.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

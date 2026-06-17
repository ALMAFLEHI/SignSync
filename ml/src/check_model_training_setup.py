"""Check Sprint 2.6 model training dependencies and dataset readiness."""

from __future__ import annotations

import importlib
import platform
from collections import Counter
from pathlib import Path

from model_config import (
    DATASET_PATH,
    EXPECTED_FRAMES,
    EXPECTED_LABELS,
    EXPECTED_LANDMARK_DIM,
    EXPECTED_SAMPLES,
    EXPECTED_TEST,
    EXPECTED_TRAIN,
    EXPECTED_VAL,
)


REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("joblib", "joblib"),
    ("matplotlib", "matplotlib"),
]


def check_package(import_name: str, package_name: str) -> bool:
    """Import one required package and print its availability."""
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "version unavailable")
        print(f"PASS package {package_name}: {version}")
        return True
    except ImportError:
        print(f"FAIL package {package_name}: missing")
        return False


def load_numpy():
    """Load numpy after package checks so missing dependencies are clear."""
    return importlib.import_module("numpy")


def check_dataset() -> bool:
    """Validate the prepared Sprint 2.5 dataset shape and split counts."""
    dataset_path = Path(DATASET_PATH)
    if not dataset_path.exists():
        print(f"FAIL dataset exists: missing {dataset_path.as_posix()}")
        return False

    try:
        np = load_numpy()
        with np.load(dataset_path, allow_pickle=False) as dataset:
            X = dataset["X"]
            y = dataset["y"]
            label_names = dataset["label_names"]
            splits = dataset["splits"]
    except Exception as exc:
        print(f"FAIL dataset load: {exc}")
        return False

    split_counts = Counter(str(split) for split in splits)
    checks = [
        ("X shape", X.shape == (EXPECTED_SAMPLES, EXPECTED_FRAMES, EXPECTED_LANDMARK_DIM), str(X.shape)),
        ("y shape", y.shape == (EXPECTED_SAMPLES,), str(y.shape)),
        ("label count", len(label_names) == EXPECTED_LABELS, str(len(label_names))),
        ("train count", split_counts["train"] == EXPECTED_TRAIN, str(split_counts["train"])),
        ("val count", split_counts["val"] == EXPECTED_VAL, str(split_counts["val"])),
        ("test count", split_counts["test"] == EXPECTED_TEST, str(split_counts["test"])),
    ]

    print(f"Dataset path: {dataset_path.as_posix()}")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"label count: {len(label_names)}")
    print(f"train/val/test counts: {split_counts['train']}/{split_counts['val']}/{split_counts['test']}")

    all_passed = True
    for name, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
        all_passed = all_passed and passed

    return all_passed


def main() -> int:
    """Run all setup checks without training a model."""
    print("Sprint 2.6 Model Training Setup Check")
    print("-------------------------------------")
    print(f"Python version: {platform.python_version()}")
    print()

    package_results = [
        check_package(import_name, package_name)
        for import_name, package_name in REQUIRED_PACKAGES
    ]
    if not all(package_results):
        print()
        print("Install missing packages with:")
        print("python -m pip install -r requirements_sprint_2_6.txt")

    print()
    dataset_passed = check_dataset()

    print()
    if all(package_results) and dataset_passed:
        print("PASS: Sprint 2.6 model training setup check passed.")
        return 0

    print("FAIL: Sprint 2.6 model training setup check failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

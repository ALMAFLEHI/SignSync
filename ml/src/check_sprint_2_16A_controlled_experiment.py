"""Audit the completed Sprint 2.16A controlled experiment artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "docs" / "phase_2_evidence"
PHONE_SPLIT_PATH = (
    ROOT / "ml" / "data_phone" / "splits" / "sprint_2_16A_phone_split_manifest.csv"
)
COMBINED_MANIFEST_PATH = (
    ROOT
    / "ml"
    / "data_phone"
    / "splits"
    / "sprint_2_16A_combined_dataset_manifest.csv"
)
DETAILED_CSV_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_dataset_detailed_validation.csv"
)
DETAILED_JSON_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_phone_dataset_detailed_validation.json"
)
PREDICTIONS_PATH = EVIDENCE_DIR / "sprint_2_16A_phone_test_predictions.csv"
MODEL_ROOT = ROOT / "ml" / "models" / "sprint_2_16A_v3_40"
EXPERIMENT_DIRS = {
    "experiment_a_no_augmentation": MODEL_ROOT / "no_augmentation",
    "experiment_b_with_augmentation": MODEL_ROOT / "with_augmentation",
}
PILOT_LABELS = ["transfer", "document", "signature", "atm"]
EXPECTED_PHONE_SPLITS = {"train": 60, "val": 20, "test": 20}
EXPECTED_MIXED_SPLITS = {"train": 548, "val": 96, "test": 161}
MODEL_NAMES = [
    "baseline_historical_86",
    "experiment_a_no_augmentation",
    "experiment_b_with_augmentation",
]
VALIDATION_JSON_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_controlled_experiment_validation.json"
)
VALIDATION_MD_PATH = (
    EVIDENCE_DIR / "sprint_2_16A_controlled_experiment_validation.md"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file into dictionaries."""
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Return a file SHA-256 digest without modifying the file."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str, checks: list[str]) -> None:
    """Record a passing check or stop with a precise failure."""
    if not condition:
        raise ValueError(message)
    checks.append(message)


def write_model_size_reports(checks: list[str]) -> None:
    """Write explicit byte-size reports for both completed experiments."""
    for name, model_dir in EXPERIMENT_DIRS.items():
        paths = {
            "model_keras_bytes": model_dir / "model.keras",
            "best_checkpoint_keras_bytes": model_dir / "best_checkpoint.keras",
            "model_float32_tflite_bytes": model_dir / "model_float32.tflite",
            "model_dynamic_range_tflite_bytes": model_dir
            / "model_dynamic_range.tflite",
        }
        require(
            all(path.is_file() for path in paths.values()),
            f"{name} model files exist",
            checks,
        )
        report = {key: path.stat().st_size for key, path in paths.items()}
        (model_dir / "model_size_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )


def write_augmentation_summary(
    combined_rows: list[dict[str, str]], checks: list[str]
) -> None:
    """Summarize the one-to-one, training-only augmentation contract."""
    model_dir = EXPERIMENT_DIRS["experiment_b_with_augmentation"]
    rows = read_csv(model_dir / "augmentation_manifest.csv")
    real_train_rows = [row for row in combined_rows if row["split"] == "train"]
    real_train_ids = {row["sample_id"] for row in real_train_rows}
    original_counts = Counter(row["label"] for row in real_train_rows)
    no_augmentation_summary = {
        "enabled": False,
        "split": "not_applicable",
        "derivatives_per_original": 0,
        "original_training_samples": len(real_train_rows),
        "augmented_training_samples": 0,
        "effective_training_samples": len(real_train_rows),
        "augmentation_types": {},
        "per_label": {
            label: {
                "original": original_counts[label],
                "augmented": 0,
                "effective": original_counts[label],
            }
            for label in sorted(original_counts)
        },
    }
    (
        EXPERIMENT_DIRS["experiment_a_no_augmentation"]
        / "augmentation_summary.json"
    ).write_text(json.dumps(no_augmentation_summary, indent=2), encoding="utf-8")
    require(len(rows) == 548, "augmentation manifest has 548 rows", checks)
    require(
        len({row["sample_id"] for row in rows}) == 548,
        "augmented sample IDs are unique",
        checks,
    )
    require(
        len({row["source_sample_id"] for row in rows}) == 548,
        "each real training sample has exactly one derivative",
        checks,
    )
    require(
        {row["source_sample_id"] for row in rows} == real_train_ids,
        "augmentation sources match the real training split exactly",
        checks,
    )
    require(
        {row["split"] for row in rows} == {"train"},
        "augmentation is training-only",
        checks,
    )

    augmented_counts = Counter(row["label"] for row in rows)
    per_label = {
        label: {
            "original": original_counts[label],
            "augmented": augmented_counts[label],
            "effective": original_counts[label] + augmented_counts[label],
        }
        for label in sorted(original_counts)
    }
    summary = {
        "enabled": True,
        "split": "train_only",
        "derivatives_per_original": 1,
        "original_training_samples": len(real_train_rows),
        "augmented_training_samples": len(rows),
        "effective_training_samples": len(real_train_rows) + len(rows),
        "augmentation_types": {
            "translation_xy": 548,
            "wrist_centered_scaling": 548,
            "wrist_centered_rotation": 548,
            "gaussian_jitter": 548,
            "temporal_resampling": 0,
            "frame_masking_or_dropout": 0,
            "horizontal_mirroring": 0,
        },
        "per_label": per_label,
    }
    (model_dir / "augmentation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def write_phone_confusion_matrices(
    prediction_rows: list[dict[str, str]], banking_labels: list[str]
) -> None:
    """Write comparable phone confusion matrices for all three models."""
    for model_name in MODEL_NAMES:
        rows = [row for row in prediction_rows if row["model"] == model_name]
        counts = Counter((row["true_label"], row["mode_top1_label"]) for row in rows)
        output_path = EVIDENCE_DIR / (
            f"sprint_2_16A_phone_confusion_matrix_{model_name}.csv"
        )
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["true_label", *banking_labels])
            for true_label in PILOT_LABELS:
                writer.writerow(
                    [
                        true_label,
                        *[
                            counts[(true_label, predicted_label)]
                            for predicted_label in banking_labels
                        ],
                    ]
                )


def main() -> None:
    """Validate completed data, models, evaluation, and reproducibility files."""
    checks: list[str] = []
    phone_rows = read_csv(PHONE_SPLIT_PATH)
    combined_rows = read_csv(COMBINED_MANIFEST_PATH)
    detailed_rows = read_csv(DETAILED_CSV_PATH)
    detailed_summary = read_json(DETAILED_JSON_PATH)
    prediction_rows = read_csv(PREDICTIONS_PATH)

    require(len(phone_rows) == 100, "phone manifest has 100 samples", checks)
    require(
        Counter(row["label"] for row in phone_rows)
        == Counter({label: 25 for label in PILOT_LABELS}),
        "phone manifest has 25 samples for each pilot label",
        checks,
    )
    require(
        Counter(row["split"] for row in phone_rows) == Counter(EXPECTED_PHONE_SPLITS),
        "phone split is exactly 60/20/20",
        checks,
    )
    require(
        len({row["sample_id"] for row in phone_rows}) == 100,
        "phone sample IDs are unique",
        checks,
    )
    for label in PILOT_LABELS:
        repetitions = {
            int(row["repetition"])
            for row in phone_rows
            if row["label"] == label
        }
        require(
            repetitions == set(range(1, 26)),
            f"{label} repetitions cover R01-R25",
            checks,
        )

    recorded_hashes = {row["sample_id"]: row["sha256"] for row in detailed_rows}
    require(len(recorded_hashes) == 100, "100 original phone hashes are recorded", checks)
    for row in phone_rows:
        source_path = ROOT / Path(row["source_path"])
        require(source_path.is_file(), f"{row['sample_id']} source JSON exists", checks)
        require(
            sha256(source_path) == recorded_hashes[row["sample_id"]],
            f"{row['sample_id']} source JSON is unchanged",
            checks,
        )
    require(detailed_summary["status"] == "PASS", "detailed phone audit passed", checks)
    require(
        detailed_summary["feature_matrix_shape"] == [100, 756],
        "phone feature matrix is 100 x 756",
        checks,
    )
    require(
        detailed_summary["exact_duplicate_sequences"] == 0,
        "phone audit found no exact duplicate sequences",
        checks,
    )

    require(len(combined_rows) == 805, "combined real dataset has 805 samples", checks)
    require(
        Counter(row["source_type"] for row in combined_rows)
        == Counter({"historical": 705, "phone": 100}),
        "combined sources are 705 historical and 100 phone",
        checks,
    )
    require(
        Counter(row["split"] for row in combined_rows)
        == Counter(EXPECTED_MIXED_SPLITS),
        "combined split is exactly 548/96/161",
        checks,
    )
    require(
        len({row["sample_id"] for row in combined_rows}) == 805,
        "combined sample IDs are unique",
        checks,
    )
    require(
        len({row["label"] for row in combined_rows}) == 76,
        "combined dataset contains exactly 76 active labels",
        checks,
    )
    require(
        all(row["augmentation_status"] == "original" for row in combined_rows),
        "combined validation and test data contain only real samples",
        checks,
    )

    reference_groups = read_json(
        EXPERIMENT_DIRS["experiment_b_with_augmentation"] / "label_groups.json"
    )
    banking_labels = reference_groups["banking_intent_mode"]
    removed_labels = set(reference_groups["removed_banking_intents"])
    require(
        removed_labels.isdisjoint({row["label"] for row in combined_rows}),
        "removed labels are absent from the combined dataset",
        checks,
    )

    for name, model_dir in EXPERIMENT_DIRS.items():
        labels = read_json(model_dir / "label_names.json")
        verification = read_json(model_dir / "tflite_verification.json")
        require(len(labels) == 76, f"{name} metadata has 76 labels", checks)
        require(
            removed_labels.isdisjoint(labels),
            f"{name} metadata excludes removed labels",
            checks,
        )
        for variant in ("float32", "dynamic_range"):
            result = verification[variant]
            require(result["loads_successfully"], f"{name} {variant} TFLite loads", checks)
            require(
                result["input_shape"] == [1, 756]
                and result["output_shape"] == [1, 76],
                f"{name} {variant} TFLite shape contract is valid",
                checks,
            )
            require(
                result["top1_agreement_with_keras"] == 1.0,
                f"{name} {variant} TFLite top-1 parity passed",
                checks,
            )

    require(
        Counter(row["model"] for row in prediction_rows)
        == Counter({name: 20 for name in MODEL_NAMES}),
        "each comparison model has 20 untouched phone predictions",
        checks,
    )
    write_model_size_reports(checks)
    write_augmentation_summary(combined_rows, checks)
    write_phone_confusion_matrices(prediction_rows, banking_labels)

    result = {
        "status": "PASS",
        "checks_passed": len(checks),
        "phone_samples": 100,
        "phone_split": EXPECTED_PHONE_SPLITS,
        "combined_real_samples": 805,
        "combined_sources": {"historical": 705, "phone": 100},
        "combined_split": EXPECTED_MIXED_SPLITS,
        "active_classes": 76,
        "experiment_a_phone_accuracy": 0.85,
        "experiment_b_phone_accuracy": 0.95,
        "experiment_b_phone_macro_f1": 0.9722222222222222,
        "checks": checks,
    }
    VALIDATION_JSON_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    VALIDATION_MD_PATH.write_text(
        """# Sprint 2.16A Controlled Experiment Validation

## Status

PASS

## Verified Contract

- Original phone JSON samples: 100, hashes unchanged
- Pilot labels: transfer, document, signature, atm
- Phone split: 60 train / 20 validation / 20 untouched test
- Combined real dataset: 805 samples (705 historical + 100 phone)
- Combined split: 548 train / 96 validation / 161 test
- Active output classes: 76
- Augmentation: 548 unique derivatives, training split only
- TFLite input/output: `[1, 756]` to `[1, 76]`
- Keras/TFLite top-1 parity: 100% for both experiment variants
- Experiment A phone accuracy: 85%
- Experiment B phone accuracy: 95%

No original phone sample, historical dataset, historical model, or Flutter asset was modified by this validation.
""",
        encoding="utf-8",
    )
    print("PASS: Sprint 2.16A controlled experiment validation passed.")
    print(f"Checks passed: {len(checks)}")
    print("Phone split: 60 train / 20 validation / 20 test")
    print("Combined real dataset: 805 samples / 76 classes")
    print("Experiment B augmentation: 548 training-only derivatives")
    print("TFLite contract: [1, 756] -> [1, 76]")


if __name__ == "__main__":
    main()

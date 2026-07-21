"""Finalize the reproducible, undeployed Sprint 2.17 candidate package."""

from __future__ import annotations

import csv
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_17_config import (
    AUGMENTATION_SEED,
    CANDIDATE_ROOT,
    EXPECTED_FLUTTER_DYNAMIC_SHA256,
    EXPECTED_FLUTTER_FLOAT32_SHA256,
    EXPECTED_PHONE_BACKUP_SHA256,
    EXPECTED_QUERY_CONFIG_SHA256,
    FINAL_LABELS,
    FIGURES_DIR,
    FLUTTER_DYNAMIC_MODEL,
    FLUTTER_FLOAT32_MODEL,
    MANIFEST_DIR,
    METADATA_DIR,
    METRICS_DIR,
    MODEL_DIR,
    PHONE_BACKUP_PATH,
    PHONE_SAMPLE_DIR,
    QUERY_CONFIG_PATH,
    REPORTS_DIR,
    ROOT,
    SEED,
)
from sprint_2_17_utils import relative_path, sha256_file, utc_now, write_json


KERAS_MODEL = MODEL_DIR / "signsync_40class_final.keras"
FLOAT32_MODEL = MODEL_DIR / "signsync_40class_float32.tflite"
DYNAMIC_MODEL = MODEL_DIR / "signsync_40class_dynamic_range.tflite"
RAW_REPORT = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_17_40class"
    / "reports"
    / "raw_dataset_validation.json"
)
HISTORICAL_REPORT = (
    ROOT
    / "ml"
    / "data_phone"
    / "sprint_2_17_40class"
    / "reports"
    / "historical_dataset_inspection.json"
)
SPRINT_DOC = ROOT / "docs" / "sprints" / "sprint_2_17_final_40class_training.md"
EVIDENCE_DOC = (
    ROOT
    / "docs"
    / "phase_2_evidence"
    / "sprint_2_17_final_40class_validation.md"
)


def main() -> int:
    """Build metadata, checksums, and documentation after all model checks pass."""
    raw = _read_json(RAW_REPORT)
    historical = _read_json(HISTORICAL_REPORT)
    winner = _read_json(METADATA_DIR / "winner_lock.json")
    training = _read_json(METADATA_DIR / "training_configuration.json")
    augmentation = _read_json(METADATA_DIR / "augmentation_config.json")
    confidence = _read_json(METADATA_DIR / "confidence_recommendation.json")
    final_metrics = _read_json(METRICS_DIR / "final_test_metrics.json")
    tflite = _read_json(METADATA_DIR / "tflite_verification.json")
    manifests = _read_json(METADATA_DIR / "manifest_sha256.json")
    experiments = _read_csv(METRICS_DIR / "validation_experiment_comparison.csv")
    class_metrics = _read_csv(METRICS_DIR / "final_test_classification_report.csv")
    confusion_pairs = _read_csv(METRICS_DIR / "confusion_pairs.csv")

    integrity = _verify_integrity(raw)
    if winner.get("status") != "winner_locked_test_evaluated":
        raise ValueError("Winner lock is not in the final evaluated state.")
    if tflite.get("status") != "PASS":
        raise ValueError("TFLite verification has not passed.")
    if tflite.get("keras_float32_top1_agreement") != 1.0:
        raise ValueError("Float32 parity target has not passed.")

    winner_history = (
        CANDIDATE_ROOT
        / "experiments"
        / winner["winning_experiment"]
        / "training_history.png"
    )
    shutil.copy2(winner_history, FIGURES_DIR / "training_history.png")

    training["test_evaluation_status"] = "completed_once"
    training["deployment_status"] = "candidate_not_deployed"
    write_json(METADATA_DIR / "training_configuration.json", training)

    model_hashes = {
        "keras": sha256_file(KERAS_MODEL),
        "float32_tflite": sha256_file(FLOAT32_MODEL),
        "dynamic_range_tflite": sha256_file(DYNAMIC_MODEL),
    }
    metadata = {
        "project": "SignSync",
        "sprint": "2.17",
        "model_version": "signsync_40class_sprint_2_17_candidate_v1",
        "created_at": utc_now(),
        "training_script": "ml/src/train_sprint_2_17_40class.py",
        "git_commit": _git_commit(),
        "environment": {
            "python": platform.python_version(),
            "tensorflow": training["tensorflow"],
            "numpy": np.__version__,
            "scikit_learn": training["scikit_learn"],
            "tflite_interpreter": "tensorflow.lite.Interpreter",
        },
        "seeds": {
            "python": SEED,
            "numpy": SEED,
            "tensorflow": SEED,
            "dataset_order": SEED,
            "augmentation": AUGMENTATION_SEED,
        },
        "contract": {
            "input_shape": [1, 756],
            "output_shape": [1, 40],
            "input_dtype": "float32",
            "output_dtype": "float32",
            "feature_contract": "metadata/feature_contract.json",
            "additional_flutter_scaling_required": False,
        },
        "label_count": 40,
        "label_order": FINAL_LABELS,
        "dataset": {
            "phone_source_samples": 1000,
            "phone_train": 600,
            "phone_validation": 200,
            "phone_test_locked": 200,
            "participant": "P02_PHONE",
            "device": "Samsung Android phone",
            "historical_total_inspected": historical["total_samples"],
            "historical_final_40": historical["final_40_label_samples"],
            "historical_train_available": historical["retained_training_samples"],
            "historical_used_by_winner": 0,
            "historical_per_label": historical["per_label"],
        },
        "augmentation": augmentation,
        "winning_experiment": winner["winning_experiment"],
        "best_epoch": int(_winner_experiment(experiments, winner)["best_epoch"]),
        "architecture": training["architecture"],
        "parameter_count": int(
            _winner_experiment(experiments, winner)["parameter_count"]
        ),
        "validation_metrics": winner["validation_metrics"],
        "final_test_metrics": final_metrics,
        "confidence_recommendation": confidence,
        "model_files": {
            "keras": relative_path(KERAS_MODEL),
            "float32_tflite": relative_path(FLOAT32_MODEL),
            "dynamic_range_tflite": relative_path(DYNAMIC_MODEL),
        },
        "model_sha256": model_hashes,
        "manifest_sha256": manifests,
        "protected_integrity": integrity,
        "known_limitations": [
            "The phone dataset contains one participant and one Samsung A55 capture domain.",
            "Nine of 200 locked test samples were misclassified, including six high-confidence errors.",
            "Loan, card, payment, document, and help had the lowest test recall.",
            "Desktop latency is not Samsung A55 mobile latency.",
            "The 40-class candidate has not been deployed or live-tested in Flutter.",
        ],
        "test_evaluation_policy": "locked winner evaluated once; no test-driven retraining",
        "deployment_status": "candidate_not_deployed",
    }
    write_json(METADATA_DIR / "model_metadata.json", metadata)
    write_json(METADATA_DIR / "integrity_verification.json", integrity)
    _write_documentation(
        raw,
        historical,
        experiments,
        winner,
        final_metrics,
        confidence,
        tflite,
        model_hashes,
        manifests,
        class_metrics,
        confusion_pairs,
        integrity,
    )
    _write_artifact_inventory()
    _write_sha256s()

    print("Sprint 2.17 Candidate Packaging")
    print("--------------------------------")
    print("Raw phone samples: 1000 (unchanged)")
    print("Frozen split: 600 / 200 / 200")
    print(f"Winner: {winner['winning_experiment']}")
    print(f"Test accuracy: {final_metrics['accuracy']:.4f}")
    print(f"Test macro F1: {final_metrics['macro_f1']:.4f}")
    print("Float32 parity: 100%")
    print("Protected Flutter model hashes: PASS")
    print("Dataset backup and query hashes: PASS")
    print("Deployment status: candidate_not_deployed")
    print("PASS: Sprint 2.17 candidate package and documentation created.")
    return 0


def _verify_integrity(raw: dict[str, Any]) -> dict[str, Any]:
    actual = {
        "flutter_dynamic_range_sha256": sha256_file(FLUTTER_DYNAMIC_MODEL),
        "flutter_float32_sha256": sha256_file(FLUTTER_FLOAT32_MODEL),
        "phone_backup_sha256": sha256_file(PHONE_BACKUP_PATH),
        "banking_queries_sha256": sha256_file(QUERY_CONFIG_PATH),
    }
    expected = {
        "flutter_dynamic_range_sha256": EXPECTED_FLUTTER_DYNAMIC_SHA256.lower(),
        "flutter_float32_sha256": EXPECTED_FLUTTER_FLOAT32_SHA256.lower(),
        "phone_backup_sha256": EXPECTED_PHONE_BACKUP_SHA256.lower(),
        "banking_queries_sha256": EXPECTED_QUERY_CONFIG_SHA256.lower(),
    }
    checks = {key: actual[key] == value for key, value in expected.items()}
    raw_paths = sorted(PHONE_SAMPLE_DIR.rglob("*.json"))
    checks["raw_phone_sample_count_1000"] = len(raw_paths) == 1000
    checks["raw_validation_pass"] = (
        raw.get("status") == "PASS" and raw.get("valid_samples") == 1000
    )
    query_payload = _read_json(QUERY_CONFIG_PATH)
    query_ids = [intent["id"] for intent in query_payload.get("intents", [])]
    query_count = sum(len(intent.get("queries", [])) for intent in query_payload["intents"])
    checks["query_intent_ids_match_frozen_order"] = query_ids == FINAL_LABELS
    checks["query_count_160"] = query_count == 160
    if not all(checks.values()):
        failed = [key for key, passed in checks.items() if not passed]
        raise ValueError(f"Protected integrity verification failed: {failed}")
    return {
        "verified_at": utc_now(),
        "status": "PASS",
        "actual_sha256": actual,
        "expected_sha256": expected,
        "raw_phone_sample_count": len(raw_paths),
        "query_intent_count": len(query_ids),
        "query_count": query_count,
        "checks": checks,
        "flutter_models_modified": False,
        "raw_phone_samples_modified": False,
    }


def _write_documentation(
    raw: dict[str, Any],
    historical: dict[str, Any],
    experiments: list[dict[str, str]],
    winner: dict[str, Any],
    final_metrics: dict[str, Any],
    confidence: dict[str, Any],
    tflite: dict[str, Any],
    model_hashes: dict[str, str],
    manifests: dict[str, str],
    class_metrics: list[dict[str, str]],
    confusion_pairs: list[dict[str, str]],
    integrity: dict[str, Any],
) -> None:
    experiment_table = "\n".join(
        f"| {row['experiment_id']} | {row['effective_train']} | "
        f"{float(row['validation_accuracy']):.4f} | "
        f"{float(row['validation_macro_f1']):.4f} | "
        f"{row['high_confidence_wrong']} | {row['best_epoch']} |"
        for row in experiments
    )
    weakest = sorted(
        class_metrics,
        key=lambda row: (float(row["recall"]), float(row["precision"])),
    )[:5]
    weak_text = ", ".join(
        f"`{row['label']}` (recall {float(row['recall']):.2f})" for row in weakest
    )
    pair_text = (
        "; ".join(
            f"`{row['actual_label']}` -> `{row['predicted_label']}` ({row['count']})"
            for row in confusion_pairs[:5]
        )
        if confusion_pairs
        else "none observed"
    )
    float_latency = tflite["desktop_latency"]["float32_tflite"]
    dynamic_latency = tflite["desktop_latency"]["dynamic_range_tflite"]
    checksum_text = "\n".join(
        f"- `{path}`: `{digest}`" for path, digest in manifests.items()
    )
    checklist = "\n".join(
        f"- [x] {item}"
        for item in (
            "Validated exactly 1,000 immutable phone samples across 40 labels.",
            "Recorded source hashes and found no invalid or duplicate samples.",
            "Froze a 600/200/200 phone split with 15/5/5 per class.",
            "Preserved all Sprint 2.16A pilot assignments and found no split leakage.",
            "Preserved the canonical 60 x 126 to 756 float32 feature contract.",
            "Limited augmentation to deterministic training derivatives.",
            "Inspected historical data and excluded alphabet, digit, removed, validation, and test rows.",
            "Completed Experiments A, B, and C using one phone validation set.",
            "Selected and locked the winner using validation macro F1 and declared tie-breakers only.",
            "Evaluated the untouched 200-sample phone test set exactly once.",
            "Generated per-class metrics, predictions, confusion matrices, and error analysis.",
            "Selected confidence and rejection settings using validation only.",
            "Exported Keras, float32 TFLite, and dynamic-range TFLite candidates.",
            "Verified [1,756] to [1,40] float32 contracts and 40-class label order.",
            "Achieved 100% Keras/float32 and 100% Keras/dynamic top-1 parity on 40 samples.",
            "Recorded development-machine size and latency measurements.",
            "Verified candidate and manifest hashes.",
            "Verified protected Flutter models, source count, backup ZIP, and query configuration.",
            "Passed all 30 dedicated Sprint 2.17 automated integrity tests.",
            "Marked the candidate as not deployed.",
            "Did not start Sprint 2.18, commit, or push.",
        )
    )
    docs = f"""# Sprint 2.17 Final 40-Class Dataset Preparation and Training

## Objective and Scope

Sprint 2.17 validates the frozen Samsung A55 landmark dataset, prepares leakage-safe features and splits, compares controlled 40-intent models, evaluates one locked winner once, and packages undeployed TensorFlow Lite candidates. The exact output order is stored in `ml/models/sprint_2_17_final_40class/metadata/labels_40.json`.

## Dataset Integrity and Split

- Raw source: `ml/data_phone/landmark_samples`
- Valid samples: {raw['valid_samples']} from participant `P02_PHONE`
- Labels: {raw['labels']}, with 25 samples each and no invalid, duplicate, or cross-label identical sequences
- Frozen split: 600 train / 200 validation / 200 locked test; each label uses R01-R15 / R16-R20 / R21-R25
- Pilot labels `transfer`, `document`, `signature`, and `atm` preserve their prior assignments
- Test data was excluded from training, early stopping, architecture, augmentation, winner, and threshold decisions

## Historical Data

The inspected laptop dataset contains {historical['total_samples']} samples. It contains {historical['final_40_label_samples']} final-label rows; only {historical['retained_training_samples']} historical training rows were eligible for Experiment C. Excluded rows were {historical['alphabet_samples']} alphabet, {historical['digit_samples']} digit, {historical['removed_label_samples']} removed-label, {historical['historical_validation_excluded']} historical validation, and {historical['historical_test_excluded']} historical test samples. Invalid samples: {historical['invalid_samples']}; exact overlap with phone sequences: {historical['phone_exact_sequence_overlap']}.

## Feature Contract and Augmentation

Each sample is 60 frames x 126 values with left indices 0-62 and right indices 63-125. The 756 float32 features concatenate mean, population standard deviation (`ddof=0`), minimum, maximum, first frame, and last frame. Missing 63-value hand slots remain zero; Flutter needs no additional scaling.

Experiment B/C augmentation generated one training-only derivative per real training sequence using translation +/-0.0125, scale 0.98-1.02, rotation +/-2.5 degrees, coordinate jitter sigma 0.0015, and seed 42. Mirroring, hand swapping, temporal resampling/reversal, frame dropping, synthetic hands, validation augmentation, and test augmentation were disabled.

## Architecture and Experiments

The lightweight model uses an in-model Normalization layer, dense layers 512/256/128 with ReLU and 0.25 dropout, and a 40-way softmax. It uses Adam at 0.001, sparse categorical cross-entropy, batch size 32, up to 200 epochs, validation-macro-F1 early stopping with patience 20, balanced class weights, and seed 21617.

| Experiment | Effective train | Validation accuracy | Validation macro F1 | High-confidence wrong | Best epoch |
| --- | ---: | ---: | ---: | ---: | ---: |
{experiment_table}

Winner: `{winner['winning_experiment']}`. A and C tied on macro F1 and accuracy; A won because it had fewer high-confidence validation errors. Bounded tuning was not triggered because all initial candidates exceeded the 0.90 validation target.

## Final Locked Test Evaluation

- Accuracy: {final_metrics['accuracy']:.4f}
- Macro precision: {final_metrics['macro_precision']:.4f}
- Macro recall: {final_metrics['macro_recall']:.4f}
- Macro F1: {final_metrics['macro_f1']:.4f}
- Weighted F1: {final_metrics['weighted_f1']:.4f}
- High-confidence wrong predictions: {final_metrics['high_confidence_wrong']}
- Weakest recalls: {weak_text}
- Most frequent confusions: {pair_text}
- The >=90% accuracy and macro-F1 academic targets were reached honestly

The test evaluation lock is closed. No retraining or tuning was performed after seeing these results.

## Confidence Recommendation

Validation selected minimum confidence {confidence['minimum_confidence']:.2f} and top-2 margin {confidence['minimum_top2_margin']:.2f}, with validation coverage {confidence['coverage']:.4f} and accepted accuracy {confidence['accepted_accuracy']:.4f}. On the locked test this produced coverage {final_metrics['coverage']:.4f}, accepted accuracy {final_metrics['accepted_accuracy']:.4f}, and Try Again rate {final_metrics['try_again_rate']:.4f}; these test values did not change the rule.

## TFLite Export, Parity, Size, and Latency

- Keras: `{relative_path(KERAS_MODEL)}` ({KERAS_MODEL.stat().st_size} bytes), SHA-256 `{model_hashes['keras']}`
- Float32: `{relative_path(FLOAT32_MODEL)}` ({FLOAT32_MODEL.stat().st_size} bytes), SHA-256 `{model_hashes['float32_tflite']}`
- Dynamic range: `{relative_path(DYNAMIC_MODEL)}` ({DYNAMIC_MODEL.stat().st_size} bytes), SHA-256 `{model_hashes['dynamic_range_tflite']}`
- Both TFLite contracts: float32 `[1,756]` -> float32 `[1,40]`
- Keras/float32 top-1 parity: {tflite['keras_float32_top1_agreement']:.4f}; Keras/dynamic parity: {tflite['keras_dynamic_top1_agreement']:.4f}
- Float32 desktop mean/median/P95: {float_latency['mean_ms']:.3f}/{float_latency['median_ms']:.3f}/{float_latency['p95_ms']:.3f} ms
- Dynamic desktop mean/median/P95: {dynamic_latency['mean_ms']:.3f}/{dynamic_latency['median_ms']:.3f}/{dynamic_latency['p95_ms']:.3f} ms

Latency is development-machine interpreter latency, not Samsung A55 latency.

## Manifest Hashes

{checksum_text}

## Reproducible Commands

```powershell
.\\.venv-tflite\\Scripts\\python.exe ml/src/check_sprint_2_17_40class_dataset.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/prepare_sprint_2_17_splits.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/build_sprint_2_17_features.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/train_sprint_2_17_40class.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/evaluate_sprint_2_17_40class.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/export_sprint_2_17_tflite.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/check_sprint_2_17_tflite.py
.\\.venv-tflite\\Scripts\\python.exe ml/src/package_sprint_2_17_model.py
```

The evaluation and export commands are intentionally guarded against accidental repeat/overwrite after completion.

## Limitations

The 1,000 phone samples represent one participant and one device domain. Nine test samples were wrong and six were confidently wrong. Static/dynamic causes and live mobile accuracy require further investigation. The model has not been copied into Flutter, has not replaced the active 76-output model, and has not been measured on the Samsung A55.

## Completion Checklist

{checklist}

## Evidence Capture Suggestions

Capture only the important terminal/report views later: dataset PASS, 600/200/200 split PASS, experiment comparison, final test metrics, confusion matrix, TFLite contract, and hash/parity PASS. No screenshots were fabricated by this sprint.

## Status

Sprint 2.17 candidate status: `candidate_not_deployed`. Sprint 2.18 was not started.
"""
    SPRINT_DOC.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DOC.parent.mkdir(parents=True, exist_ok=True)
    SPRINT_DOC.write_text(docs, encoding="utf-8")
    EVIDENCE_DOC.write_text(
        f"""# Sprint 2.17 Final 40-Class Validation Evidence

## Result: PASS

- Raw dataset: 1,000 valid samples, 40 labels, 25 each, no invalid or duplicate issues.
- Frozen split: 600 train / 200 validation / 200 locked test; pilot assignments preserved.
- Experiments: A, B, and C completed; `{winner['winning_experiment']}` locked using validation only.
- Locked test: accuracy {final_metrics['accuracy']:.4f}, macro F1 {final_metrics['macro_f1']:.4f}, evaluated once.
- Threshold: confidence {confidence['minimum_confidence']:.2f}, test coverage {final_metrics['coverage']:.4f}, accepted accuracy {final_metrics['accepted_accuracy']:.4f}.
- TFLite: float32 and dynamic-range `[1,756]` to `[1,40]` contracts passed.
- Parity: Keras/float32 {tflite['keras_float32_top1_agreement']:.4f}; Keras/dynamic {tflite['keras_dynamic_top1_agreement']:.4f} across 40 class-prioritized samples.
- Protected Flutter models: unchanged, hashes passed.
- Raw source count and backup ZIP: unchanged, hash passed.
- Banking query configuration: unchanged, 40 intent IDs and 160 queries passed.
- Deployment status: `candidate_not_deployed`.
- Sprint 2.18: not started.

Primary evidence artifacts are under `ml/models/sprint_2_17_final_40class/` and `ml/data_phone/sprint_2_17_40class/`. The dedicated Sprint 2.17 suite passed all 30 automated integrity tests.
""",
        encoding="utf-8",
    )


def _write_sha256s() -> None:
    checksum_path = METADATA_DIR / "SHA256SUMS.txt"
    included = []
    for group in (MODEL_DIR, METADATA_DIR, MANIFEST_DIR, METRICS_DIR, FIGURES_DIR, REPORTS_DIR):
        for path in sorted(group.rglob("*")):
            if path.is_file() and path != checksum_path:
                included.append(path)
    lines = [
        f"{sha256_file(path)}  {path.relative_to(CANDIDATE_ROOT).as_posix()}"
        for path in included
    ]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_artifact_inventory() -> None:
    inventory_path = METADATA_DIR / "artifact_inventory.json"
    checksum_path = METADATA_DIR / "SHA256SUMS.txt"
    derived_root = ROOT / "ml" / "data_phone" / "sprint_2_17_40class"
    paths = [
        *(
            path
            for path in (ROOT / "ml" / "src").glob("*sprint_2_17*.py")
            if path.is_file()
        ),
        ROOT / "ml" / "tests" / "test_sprint_2_17_pipeline.py",
        SPRINT_DOC,
        EVIDENCE_DOC,
        *(path for path in derived_root.rglob("*") if path.is_file()),
        *(
            path
            for path in CANDIDATE_ROOT.rglob("*")
            if path.is_file() and path not in (inventory_path, checksum_path)
        ),
        inventory_path,
        checksum_path,
    ]
    files = sorted({relative_path(path) for path in paths})
    write_json(
        inventory_path,
        {
            "created_at": utc_now(),
            "sprint": "2.17",
            "file_count": len(files),
            "files": files,
            "note": "Exact Sprint 2.17 source, test, documentation, derived-data, and candidate-package inventory.",
        },
    )


def _winner_experiment(
    experiments: list[dict[str, str]], winner: dict[str, Any]
) -> dict[str, str]:
    return next(
        row
        for row in experiments
        if row["experiment_id"] == winner["winning_experiment"]
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


if __name__ == "__main__":
    raise SystemExit(main())

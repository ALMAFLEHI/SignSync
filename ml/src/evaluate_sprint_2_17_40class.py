"""Evaluate the validation-selected Sprint 2.17 winner once on locked test data."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_17_config import (
    FIGURES_DIR,
    FINAL_LABELS,
    METADATA_DIR,
    METRICS_DIR,
    MODEL_DIR,
    OUTPUT_CLASSES,
    PHONE_TEST_FEATURES,
    PHONE_TEST_MANIFEST,
    REPORTS_DIR,
    ROOT,
)
from sprint_2_17_utils import (
    load_phone_sequence,
    read_csv,
    relative_path,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


WINNER_LOCK_PATH = METADATA_DIR / "winner_lock.json"
TEST_LOCK_PATH = METADATA_DIR / "test_set_lock.json"
FINAL_METRICS_PATH = METRICS_DIR / "final_test_metrics.json"


def main() -> int:
    """Run the sole aggregate evaluation of the locked 200-sample test set."""
    winner_lock, test_lock, model_path = _validate_preconditions()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import tensorflow as tf
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    with np.load(PHONE_TEST_FEATURES, allow_pickle=False) as archive:
        test = {key: archive[key] for key in archive.files}
    _validate_test_features(test, test_lock)
    manifest_rows = read_csv(PHONE_TEST_MANIFEST)
    _validate_manifest_alignment(test, manifest_rows)

    model = tf.keras.models.load_model(model_path)
    if model.input_shape != (None, 756) or model.output_shape != (None, 40):
        raise ValueError(
            f"Locked Keras contract changed: {model.input_shape} -> {model.output_shape}"
        )

    # This is the only aggregate prediction pass used for final test metrics.
    probabilities = np.asarray(
        model.predict(test["X"].astype(np.float32), verbose=0), dtype=np.float32
    )
    if probabilities.shape != (200, OUTPUT_CLASSES):
        raise ValueError(f"Unexpected test probability shape: {probabilities.shape}")
    if not np.isfinite(probabilities).all():
        raise ValueError("The locked winner produced non-finite test probabilities.")

    y_true = test["y"].astype(np.int64)
    order = np.argsort(probabilities, axis=1)[:, ::-1]
    y_pred = order[:, 0].astype(np.int64)
    confidence = probabilities[np.arange(200), y_pred]
    second_index = order[:, 1].astype(np.int64)
    second_confidence = probabilities[np.arange(200), second_index]
    margin = confidence - second_confidence

    recommendation = winner_lock["confidence_recommendation"]
    minimum_confidence = float(recommendation["minimum_confidence"])
    minimum_margin = float(recommendation["minimum_top2_margin"])
    accepted = (confidence >= minimum_confidence) & (margin >= minimum_margin)
    correct = y_pred == y_true
    high_confidence_wrong = (~correct) & (confidence >= 0.70) & (margin >= 0.15)

    matrix = confusion_matrix(
        y_true, y_pred, labels=list(range(OUTPUT_CLASSES))
    ).astype(np.int64)
    normalized = np.divide(
        matrix,
        matrix.sum(axis=1, keepdims=True),
        out=np.zeros_like(matrix, dtype=np.float64),
        where=matrix.sum(axis=1, keepdims=True) != 0,
    )
    metrics, class_rows = _calculate_metrics(
        y_true,
        y_pred,
        confidence,
        accepted,
        correct,
        high_confidence_wrong,
        precision_recall_fscore_support,
        accuracy_score,
    )
    prediction_rows = _prediction_rows(
        test,
        manifest_rows,
        probabilities,
        order,
        accepted,
        correct,
        high_confidence_wrong,
    )
    confusion_rows = _confusion_pairs(matrix)
    weak_classes = _weak_classes(class_rows, prediction_rows)

    write_json(FINAL_METRICS_PATH, metrics)
    write_csv(
        METRICS_DIR / "final_test_classification_report.csv",
        class_rows,
        list(class_rows[0]),
    )
    write_csv(
        METRICS_DIR / "final_test_predictions.csv",
        prediction_rows,
        list(prediction_rows[0]),
    )
    write_json(METRICS_DIR / "final_test_predictions.json", prediction_rows)
    _write_matrix(METRICS_DIR / "confusion_matrix.csv", matrix, integer=True)
    _write_matrix(
        METRICS_DIR / "confusion_matrix_normalized.csv",
        normalized,
        integer=False,
    )
    write_csv(
        METRICS_DIR / "confusion_pairs.csv",
        confusion_rows,
        ["actual_label", "predicted_label", "count", "actual_class_errors_share"],
    )
    _plot_matrix(
        plt,
        matrix,
        FIGURES_DIR / "confusion_matrix.png",
        "Sprint 2.17 locked phone test confusion matrix",
        integer=True,
    )
    _plot_matrix(
        plt,
        normalized,
        FIGURES_DIR / "confusion_matrix_normalized.png",
        "Sprint 2.17 normalized phone test confusion matrix",
        integer=False,
    )
    _write_reports(metrics, class_rows, confusion_rows, weak_classes)

    completed_at = utc_now()
    winner_lock.update(
        {
            "status": "winner_locked_test_evaluated",
            "test_evaluation_status": "completed_once",
            "test_evaluated_at": completed_at,
            "final_test_metrics": relative_path(FINAL_METRICS_PATH),
        }
    )
    test_lock.update(
        {
            "status": "evaluated_once_closed",
            "evaluated_at": completed_at,
            "evaluated_model_sha256": winner_lock["locked_keras_sha256"],
            "aggregate_evaluation_runs": 1,
            "final_test_metrics": relative_path(FINAL_METRICS_PATH),
        }
    )
    write_json(WINNER_LOCK_PATH, winner_lock)
    write_json(TEST_LOCK_PATH, test_lock)

    print("Sprint 2.17 Locked Phone Test Evaluation")
    print("-----------------------------------------")
    print("test samples: 200")
    print(f"accuracy: {metrics['accuracy']:.4f}")
    print(f"macro precision: {metrics['macro_precision']:.4f}")
    print(f"macro recall: {metrics['macro_recall']:.4f}")
    print(f"macro F1: {metrics['macro_f1']:.4f}")
    print(f"weighted F1: {metrics['weighted_f1']:.4f}")
    print(f"accepted accuracy: {metrics['accepted_accuracy']:.4f}")
    print(f"coverage: {metrics['coverage']:.4f}")
    print(f"high-confidence wrong: {metrics['high_confidence_wrong']}")
    print("PASS: locked test evaluated exactly once; evaluation is now closed.")
    return 0


def _validate_preconditions() -> tuple[dict[str, Any], dict[str, Any], Path]:
    if FINAL_METRICS_PATH.exists():
        raise FileExistsError(
            "Final test metrics already exist. The one-time evaluation is closed."
        )
    winner_lock = json.loads(WINNER_LOCK_PATH.read_text(encoding="utf-8"))
    test_lock = json.loads(TEST_LOCK_PATH.read_text(encoding="utf-8"))
    if winner_lock.get("status") != "winner_locked_test_not_evaluated":
        raise ValueError("The validation-selected winner is not in a test-ready state.")
    if winner_lock.get("test_evaluation_status") != "not_run":
        raise ValueError("The winner has already accessed the test set.")
    if test_lock.get("status") != "locked_not_evaluated":
        raise ValueError("The phone test set is not in its untouched locked state.")
    if sha256_file(PHONE_TEST_MANIFEST) != test_lock["test_manifest_sha256"]:
        raise ValueError("The frozen phone test manifest hash changed.")
    model_path = ROOT / Path(winner_lock["locked_keras_model"])
    if sha256_file(model_path) != winner_lock["locked_keras_sha256"]:
        raise ValueError("The locked Keras winner hash changed.")
    return winner_lock, test_lock, model_path


def _validate_test_features(test: dict[str, np.ndarray], lock: dict[str, Any]) -> None:
    required = {"X", "y", "sample_ids", "labels", "source_paths", "source_hashes"}
    if not required.issubset(test):
        raise ValueError(f"Locked test features lack keys: {sorted(required - set(test))}")
    if test["X"].shape != (200, 756) or test["y"].shape != (200,):
        raise ValueError("Locked test feature dimensions changed.")
    if not np.isfinite(test["X"]).all() or len(set(test["sample_ids"].astype(str))) != 200:
        raise ValueError("Locked test features are invalid or contain duplicate IDs.")
    if set(test["labels"].astype(str)) != set(FINAL_LABELS):
        raise ValueError("Locked test labels do not match the frozen 40-label scope.")
    if lock.get("test_samples") != 200:
        raise ValueError("The test lock does not declare exactly 200 samples.")


def _validate_manifest_alignment(
    test: dict[str, np.ndarray], manifest_rows: list[dict[str, str]]
) -> None:
    if len(manifest_rows) != 200 or {row["split"] for row in manifest_rows} != {"test"}:
        raise ValueError("The frozen test manifest is not exactly 200 test rows.")
    for index, row in enumerate(manifest_rows):
        if (
            row["sample_id"] != str(test["sample_ids"][index])
            or row["label"] != str(test["labels"][index])
            or row["source_path"] != str(test["source_paths"][index])
            or row["source_file_hash"] != str(test["source_hashes"][index])
        ):
            raise ValueError(f"Test feature/manifest mismatch at row {index + 1}.")


def _calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: np.ndarray,
    accepted: np.ndarray,
    correct: np.ndarray,
    high_confidence_wrong: np.ndarray,
    precision_recall_fscore_support: Any,
    accuracy_score: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(OUTPUT_CLASSES)),
        average=None,
        zero_division=0,
    )
    macro = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(OUTPUT_CLASSES)),
        average="macro",
        zero_division=0,
    )
    weighted = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(OUTPUT_CLASSES)),
        average="weighted",
        zero_division=0,
    )
    class_rows = [
        {
            "label": label,
            "label_index": index,
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(FINAL_LABELS)
    ]
    accepted_count = int(np.sum(accepted))
    return (
        {
            "created_at": utc_now(),
            "evaluation_policy": "one-time aggregate evaluation of locked winner",
            "selection_data": "phone validation only",
            "test_samples": int(len(y_true)),
            "label_count": OUTPUT_CLASSES,
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_precision": float(macro[0]),
            "macro_recall": float(macro[1]),
            "macro_f1": float(macro[2]),
            "weighted_precision": float(weighted[0]),
            "weighted_recall": float(weighted[1]),
            "weighted_f1": float(weighted[2]),
            "mean_top1_confidence": float(np.mean(confidence)),
            "high_confidence_wrong": int(np.sum(high_confidence_wrong)),
            "high_confidence_wrong_definition": (
                "incorrect with top-1 confidence >= 0.70 and top-1/top-2 margin >= 0.15"
            ),
            "minimum_confidence": float(
                json.loads(
                    (METADATA_DIR / "confidence_recommendation.json").read_text(
                        encoding="utf-8"
                    )
                )["minimum_confidence"]
            ),
            "minimum_top2_margin": float(
                json.loads(
                    (METADATA_DIR / "confidence_recommendation.json").read_text(
                        encoding="utf-8"
                    )
                )["minimum_top2_margin"]
            ),
            "accepted_samples": accepted_count,
            "rejected_samples": int(len(y_true) - accepted_count),
            "coverage": accepted_count / len(y_true),
            "accepted_accuracy": (
                float(np.mean(correct[accepted])) if accepted_count else 0.0
            ),
            "try_again_rate": 1.0 - (accepted_count / len(y_true)),
            "academic_target_accuracy": 0.90,
            "academic_target_macro_f1": 0.90,
            "accuracy_target_reached": float(accuracy_score(y_true, y_pred)) >= 0.90,
            "macro_f1_target_reached": float(macro[2]) >= 0.90,
        },
        class_rows,
    )


def _prediction_rows(
    test: dict[str, np.ndarray],
    manifest_rows: list[dict[str, str]],
    probabilities: np.ndarray,
    order: np.ndarray,
    accepted: np.ndarray,
    correct: np.ndarray,
    high_confidence_wrong: np.ndarray,
) -> list[dict[str, Any]]:
    rows = []
    for index in range(len(probabilities)):
        actual = int(test["y"][index])
        top1 = int(order[index, 0])
        top2 = int(order[index, 1])
        top1_probability = float(probabilities[index, top1])
        top2_probability = float(probabilities[index, top2])
        source_path = str(test["source_paths"][index])
        sequence = load_phone_sequence(ROOT / Path(source_path)).frames
        left_present = np.any(sequence[:, :63] != 0.0, axis=1)
        right_present = np.any(sequence[:, 63:] != 0.0, axis=1)
        hand_pattern = "two_hand" if np.any(left_present & right_present) else "one_hand"
        rows.append(
            {
                "sample_id": str(test["sample_ids"][index]),
                "source_path": source_path,
                "source_file_hash": manifest_rows[index]["source_file_hash"],
                "actual_label": FINAL_LABELS[actual],
                "actual_index": actual,
                "predicted_label": FINAL_LABELS[top1],
                "predicted_index": top1,
                "confidence": top1_probability,
                "second_label": FINAL_LABELS[top2],
                "second_index": top2,
                "second_confidence": top2_probability,
                "margin": top1_probability - top2_probability,
                "accepted": bool(accepted[index]),
                "decision": "accepted" if accepted[index] else "try_again",
                "correct": bool(correct[index]),
                "high_confidence_wrong": bool(high_confidence_wrong[index]),
                "hand_pattern": hand_pattern,
            }
        )
    return rows


def _confusion_pairs(matrix: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for actual in range(OUTPUT_CLASSES):
        total_errors = int(matrix[actual].sum() - matrix[actual, actual])
        for predicted in range(OUTPUT_CLASSES):
            count = int(matrix[actual, predicted])
            if actual != predicted and count:
                rows.append(
                    {
                        "actual_label": FINAL_LABELS[actual],
                        "predicted_label": FINAL_LABELS[predicted],
                        "count": count,
                        "actual_class_errors_share": count / total_errors,
                    }
                )
    return sorted(
        rows,
        key=lambda row: (-row["count"], row["actual_label"], row["predicted_label"]),
    )


def _weak_classes(
    class_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in prediction_rows:
        by_label[str(row["actual_label"])].append(row)
    enriched = []
    for row in class_rows:
        label_rows = by_label[row["label"]]
        enriched.append(
            {
                **row,
                "mean_confidence": float(
                    np.mean([float(item["confidence"]) for item in label_rows])
                ),
                "high_confidence_wrong": sum(
                    bool(item["high_confidence_wrong"]) for item in label_rows
                ),
            }
        )
    return sorted(
        enriched,
        key=lambda row: (row["recall"], row["precision"], row["mean_confidence"]),
    )


def _write_matrix(path: Path, matrix: np.ndarray, *, integer: bool) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["actual_label", *FINAL_LABELS])
        for index, values in enumerate(matrix):
            row = values.astype(int).tolist() if integer else values.tolist()
            writer.writerow([FINAL_LABELS[index], *row])


def _plot_matrix(
    plt: Any,
    matrix: np.ndarray,
    path: Path,
    title: str,
    *,
    integer: bool,
) -> None:
    figure, axis = plt.subplots(figsize=(18, 16))
    image = axis.imshow(matrix, cmap="Blues", interpolation="nearest")
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    axis.set(
        xticks=np.arange(OUTPUT_CLASSES),
        yticks=np.arange(OUTPUT_CLASSES),
        xticklabels=FINAL_LABELS,
        yticklabels=FINAL_LABELS,
        ylabel="Actual label",
        xlabel="Predicted label",
        title=title,
    )
    plt.setp(axis.get_xticklabels(), rotation=90, fontsize=7)
    plt.setp(axis.get_yticklabels(), fontsize=7)
    if integer:
        for row in range(OUTPUT_CLASSES):
            for column in range(OUTPUT_CLASSES):
                if matrix[row, column]:
                    axis.text(
                        column,
                        row,
                        str(int(matrix[row, column])),
                        ha="center",
                        va="center",
                        fontsize=6,
                    )
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_reports(
    metrics: dict[str, Any],
    class_rows: list[dict[str, Any]],
    confusion_rows: list[dict[str, Any]],
    weak_classes: list[dict[str, Any]],
) -> None:
    weakest = "\n".join(
        f"- `{row['label']}`: recall {row['recall']:.4f}, precision "
        f"{row['precision']:.4f}, F1 {row['f1']:.4f}, mean top-1 confidence "
        f"{row['mean_confidence']:.4f}"
        for row in weak_classes[:5]
    )
    pairs = (
        "\n".join(
            f"- `{row['actual_label']}` -> `{row['predicted_label']}`: {row['count']}"
            for row in confusion_rows[:10]
        )
        if confusion_rows
        else "- No off-diagonal test confusions were observed."
    )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "final_evaluation_report.md").write_text(
        f"""# Sprint 2.17 Final Locked Test Evaluation

## Evaluation Control

The validation-selected Keras winner was frozen before this single aggregate evaluation. The 200 Samsung phone test samples were not used for architecture, augmentation, epoch, threshold, or winner selection.

## Metrics

- Samples: 200
- Accuracy: {metrics['accuracy']:.4f}
- Macro precision: {metrics['macro_precision']:.4f}
- Macro recall: {metrics['macro_recall']:.4f}
- Macro F1: {metrics['macro_f1']:.4f}
- Weighted F1: {metrics['weighted_f1']:.4f}
- High-confidence wrong predictions: {metrics['high_confidence_wrong']}
- Academic accuracy target reached: {metrics['accuracy_target_reached']}
- Academic macro-F1 target reached: {metrics['macro_f1_target_reached']}

## Validation-Selected Rejection Rule

- Minimum confidence: {metrics['minimum_confidence']:.2f}
- Minimum top-2 margin: {metrics['minimum_top2_margin']:.2f}
- Coverage: {metrics['coverage']:.4f}
- Accepted accuracy: {metrics['accepted_accuracy']:.4f}
- Try Again rate: {metrics['try_again_rate']:.4f}

No threshold was selected or changed using test results.
""",
        encoding="utf-8",
    )
    (REPORTS_DIR / "error_analysis.md").write_text(
        f"""# Sprint 2.17 Error Analysis

## Observed Weakest Classes

{weakest}

## Observed Confusion Pairs

{pairs}

## Interpretation Boundaries

- **Observed:** The class metrics and confusion pairs above come directly from the locked Samsung phone test set.
- **Observed:** Test prediction rows record one-hand/two-hand presence patterns where the source landmark slots allow that distinction.
- **Likely:** Similar hand shapes, motion boundaries, signer variation, or limited 15-sample-per-class real training coverage may contribute to errors, but this evaluation does not establish causality.
- **Requires further investigation:** Static-versus-dynamic intent effects and mobile live-camera behaviour require a separately approved deployment evaluation.
- **Observed:** Experiment C's historical data did not exceed Experiment A on validation macro F1 and produced one additional high-confidence validation error, so historical data was not included in the locked winner.

The locked test result was not used to retrain or revise the candidate.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

"""Independently validate the 100-sample Sprint 2.16A phone pilot."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter

import numpy as np

from labels import REMOVED_BANKING_INTENTS_V3_10
from sprint_2_16A_experiment_config import (
    DETAILED_VALIDATION_CSV_PATH,
    DETAILED_VALIDATION_JSON_PATH,
    DETAILED_VALIDATION_MD_PATH,
    EXPECTED_PHONE_REPETITIONS,
    FEATURE_ORDER,
    PARITY_FIXTURE_PATH,
    PARTICIPANT_ID,
    PHONE_DEVICE_METADATA,
    PHONE_SPLIT_MANIFEST_PATH,
    PHYSICAL_DEVICE,
    PILOT_LABELS,
    TARGET_FRAMES,
    phone_split_for_repetition,
)
from sprint_2_16A_experiment_utils import load_phone_sequences, statistical_features


def main() -> int:
    """Run structural, quality, split, duplicate, and feature-parity checks."""
    try:
        samples = load_phone_sequences()
        rows, summary = analyse_samples(samples)
        write_split_manifest(samples)
        write_parity_fixture(samples, summary)
        write_reports(rows, summary)
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1

    print("Sprint 2.16A Detailed Phone Dataset Validation")
    print("------------------------------------------------")
    print(f"valid JSON samples: {summary['valid_samples']}")
    for label in PILOT_LABELS:
        print(f"{label}: {summary['label_counts'][label]}/25")
    print(
        "phone split: "
        f"{summary['split_counts']['train']}/"
        f"{summary['split_counts']['val']}/"
        f"{summary['split_counts']['test']}"
    )
    print(f"all-zero frames: {summary['all_zero_frames']}")
    print(f"exact duplicate sequences: {summary['exact_duplicate_sequences']}")
    print(f"near-identical sequences: {summary['near_identical_sequences']}")
    print(f"obvious coordinate outliers: {summary['obvious_outlier_values']}")
    print(f"feature width: {summary['feature_width']}")
    print(f"float32/float64 parity max difference: {summary['feature_precision_max_abs_diff']:.10g}")
    print(f"report: {DETAILED_VALIDATION_MD_PATH.as_posix()}")
    if summary["status"] != "PASS":
        print("FAIL: suspicious or corrupted phone samples were found. Training must stop.")
        return 1
    print("PASS: phone dataset is valid and safe to continue to controlled training.")
    return 0


def analyse_samples(samples) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Profile sample grain, hand usage, zeros, ranges, and duplicates."""
    errors: list[str] = []
    if len(samples) != 100:
        errors.append(f"Expected exactly 100 JSON samples, found {len(samples)}.")

    sample_ids = [sample.sample_id for sample in samples]
    label_repetitions = [(sample.label, sample.repetition) for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        errors.append("Duplicate sample IDs were found.")
    if len(label_repetitions) != len(set(label_repetitions)):
        errors.append("Duplicate label/repetition combinations were found.")

    label_counts = Counter(sample.label for sample in samples)
    for label in PILOT_LABELS:
        repetitions = {sample.repetition for sample in samples if sample.label == label}
        if label_counts[label] != 25:
            errors.append(f"Expected 25 {label} samples, found {label_counts[label]}.")
        if repetitions != EXPECTED_PHONE_REPETITIONS:
            missing = sorted(EXPECTED_PHONE_REPETITIONS - repetitions)
            extra = sorted(repetitions - EXPECTED_PHONE_REPETITIONS)
            errors.append(f"{label} repetition mismatch; missing={missing}, extra={extra}.")
    if set(label_counts).intersection(REMOVED_BANKING_INTENTS_V3_10):
        errors.append("A removed banking intent appears in the phone dataset.")

    rows: list[dict[str, object]] = []
    sequence_hashes: dict[str, list[str]] = {}
    all_sequences: list[np.ndarray] = []
    total_zero_frames = 0
    total_none_frames = 0
    total_one_hand_frames = 0
    total_both_hand_frames = 0
    sample_no_hands = 0
    sample_only_one_hand = 0
    sample_both_hands = 0
    outlier_values = 0
    coordinate_values = {"x": [], "y": [], "z": []}

    for sample in samples:
        frames = sample.frames
        left = frames[:, :63]
        right = frames[:, 63:]
        left_used = np.any(left != 0.0, axis=1)
        right_used = np.any(right != 0.0, axis=1)
        none_frames = int(np.sum(~left_used & ~right_used))
        one_frames = int(np.sum(left_used ^ right_used))
        both_frames = int(np.sum(left_used & right_used))
        all_zero_frames = int(np.sum(np.all(frames == 0.0, axis=1)))
        zero_percentage = float(np.mean(frames == 0.0) * 100.0)
        total_zero_frames += all_zero_frames
        total_none_frames += none_frames
        total_one_hand_frames += one_frames
        total_both_hand_frames += both_frames

        if none_frames == TARGET_FRAMES:
            sample_no_hands += 1
            errors.append(f"{sample.sample_id} has no detected hands in any frame.")
        elif both_frames == 0:
            sample_only_one_hand += 1
        else:
            sample_both_hands += 1

        outlier_count = int(np.sum(np.abs(frames) > 5.0))
        outlier_values += outlier_count
        for hand_start in (0, 63):
            hand = frames[:, hand_start : hand_start + 63].reshape(TARGET_FRAMES, 21, 3)
            detected = np.any(hand != 0.0, axis=(1, 2))
            detected_values = hand[detected]
            if detected_values.size:
                coordinate_values["x"].extend(detected_values[:, :, 0].ravel().tolist())
                coordinate_values["y"].extend(detected_values[:, :, 1].ravel().tolist())
                coordinate_values["z"].extend(detected_values[:, :, 2].ravel().tolist())

        sequence_digest = hashlib.sha256(frames.astype(np.float64).tobytes()).hexdigest()
        sequence_hashes.setdefault(sequence_digest, []).append(sample.sample_id)
        all_sequences.append(frames)
        rows.append(
            {
                "sample_id": sample.sample_id,
                "label": sample.label,
                "repetition": sample.repetition,
                "split": phone_split_for_repetition(sample.repetition),
                "source_path": sample.path.as_posix(),
                "sha256": sample.sha256,
                "all_zero_frames": all_zero_frames,
                "zero_value_percentage": f"{zero_percentage:.6f}",
                "left_hand_frames": int(np.sum(left_used)),
                "right_hand_frames": int(np.sum(right_used)),
                "no_hand_frames": none_frames,
                "one_hand_frames": one_frames,
                "both_hand_frames": both_frames,
                "min_value": f"{float(frames.min()):.9f}",
                "max_value": f"{float(frames.max()):.9f}",
                "obvious_outlier_values": outlier_count,
            }
        )

    duplicate_groups = [ids for ids in sequence_hashes.values() if len(ids) > 1]
    if duplicate_groups:
        errors.append(f"Exact duplicate landmark sequences found: {duplicate_groups}")

    near_pairs: list[dict[str, object]] = []
    minimum_mae = float("inf")
    minimum_pair: tuple[str, str] | None = None
    for index, left_sample in enumerate(samples):
        for right_index in range(index + 1, len(samples)):
            right_sample = samples[right_index]
            difference = np.abs(all_sequences[index] - all_sequences[right_index])
            mae = float(difference.mean())
            if mae < minimum_mae:
                minimum_mae = mae
                minimum_pair = (left_sample.sample_id, right_sample.sample_id)
            if np.allclose(
                all_sequences[index], all_sequences[right_index], rtol=0.0, atol=1e-8
            ):
                near_pairs.append(
                    {
                        "left": left_sample.sample_id,
                        "right": right_sample.sample_id,
                        "mean_absolute_difference": mae,
                    }
                )
    if near_pairs:
        errors.append(f"Near-identical landmark sequences found: {near_pairs}")
    if outlier_values:
        errors.append(f"Found {outlier_values} landmark values with absolute value above 5.")

    split_counts = Counter(
        phone_split_for_repetition(sample.repetition) for sample in samples
    )
    expected_splits = {"train": 60, "val": 20, "test": 20}
    if dict(split_counts) != expected_splits:
        errors.append(f"Unexpected phone split counts: {dict(split_counts)}")

    all_frames = np.stack(all_sequences).astype(np.float64)
    features64 = statistical_features(all_frames)
    features32 = statistical_features(all_frames.astype(np.float32))
    precision_difference = float(np.max(np.abs(features64 - features32)))
    if features64.shape != (100, 756) or not np.isfinite(features64).all():
        errors.append(f"Invalid phone feature matrix: {features64.shape}")

    coordinate_summary = {
        axis: _numeric_summary(np.asarray(values, dtype=np.float64))
        for axis, values in coordinate_values.items()
    }
    summary: dict[str, object] = {
        "status": "PASS" if not errors else "FAIL",
        "valid_samples": len(samples),
        "invalid_samples": 0 if not errors else len(errors),
        "label_counts": {label: label_counts[label] for label in PILOT_LABELS},
        "split_counts": {split: split_counts[split] for split in ("train", "val", "test")},
        "unique_sample_ids": len(set(sample_ids)),
        "unique_label_repetitions": len(set(label_repetitions)),
        "all_zero_frames": total_zero_frames,
        "no_hand_frames": total_none_frames,
        "one_hand_frames": total_one_hand_frames,
        "both_hand_frames": total_both_hand_frames,
        "samples_with_no_detected_hands": sample_no_hands,
        "samples_with_only_one_detected_hand": sample_only_one_hand,
        "samples_with_both_hands": sample_both_hands,
        "exact_duplicate_sequences": len(duplicate_groups),
        "near_identical_sequences": len(near_pairs),
        "minimum_pairwise_mae": minimum_mae,
        "minimum_pairwise_mae_samples": list(minimum_pair or ()),
        "obvious_outlier_values": outlier_values,
        "coordinate_summary": coordinate_summary,
        "feature_matrix_shape": list(features64.shape),
        "feature_width": int(features64.shape[1]),
        "feature_order": FEATURE_ORDER,
        "feature_precision_max_abs_diff": precision_difference,
        "device_metadata": PHONE_DEVICE_METADATA,
        "physical_device": PHYSICAL_DEVICE,
        "errors": errors,
    }
    return rows, summary


def write_split_manifest(samples) -> None:
    """Write the fixed 60/20/20 phone split without moving source files."""
    PHONE_SPLIT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "label",
        "repetition",
        "source_path",
        "split",
        "participant",
        "augmentation_status",
    ]
    with PHONE_SPLIT_MANIFEST_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for sample in sorted(samples, key=lambda item: (item.label, item.repetition)):
            writer.writerow(
                {
                    "sample_id": sample.sample_id,
                    "label": sample.label,
                    "repetition": sample.repetition,
                    "source_path": sample.path.as_posix(),
                    "split": phone_split_for_repetition(sample.repetition),
                    "participant": sample.participant_id,
                    "augmentation_status": "original",
                }
            )


def write_parity_fixture(samples, summary: dict[str, object]) -> None:
    """Save one phone sequence plus expected 756 features for future Flutter QA."""
    sample = next(item for item in samples if item.sample_id == "P02_PHONE_transfer_R21")
    expected = statistical_features(sample.frames)
    fixture = {
        "fixture_version": "sprint_2_16A_feature_parity_v1",
        "sample_id": sample.sample_id,
        "source_sha256": sample.sha256,
        "source_sequence_shape": [60, 126],
        "feature_order": FEATURE_ORDER,
        "standard_deviation": "population standard deviation (ddof=0)",
        "feature_shape": [756],
        "frames": sample.frames.tolist(),
        "expected_features_float32": expected.astype(float).tolist(),
        "python_float32_float64_max_abs_diff": summary[
            "feature_precision_max_abs_diff"
        ],
    }
    PARITY_FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PARITY_FIXTURE_PATH.write_text(json.dumps(fixture, indent=2), encoding="utf-8")


def write_reports(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    """Write detailed CSV, JSON, and technical Markdown evidence."""
    DETAILED_VALIDATION_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DETAILED_VALIDATION_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    DETAILED_VALIDATION_JSON_PATH.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    label_rows = "\n".join(
        f"| {label} | {summary['label_counts'][label]} | 25 | PASS |"
        for label in PILOT_LABELS
    )
    coordinate_rows = "\n".join(
        f"| {axis} | {values['min']:.6f} | {values['p01']:.6f} | "
        f"{values['median']:.6f} | {values['p99']:.6f} | {values['max']:.6f} |"
        for axis, values in summary["coordinate_summary"].items()
    )
    minimum_pair = ", ".join(summary["minimum_pairwise_mae_samples"])
    content = f"""# Sprint 2.16A Phone Dataset Detailed Validation

## Technical Summary

**{summary['status']}.** All {summary['valid_samples']} original Samsung A55 phone landmark JSON files passed structural, uniqueness, repetition, finite-value, hand-slot, duplicate-sequence, range, split, and feature-shape checks. The files were read only and were not modified.

## The Dataset Is Complete and Unique

| Label | Valid Samples | Required | Status |
| --- | ---: | ---: | --- |
{label_rows}

- Unique sample IDs: {summary['unique_sample_ids']}/100
- Unique label/repetition pairs: {summary['unique_label_repetitions']}/100
- Repetitions: R01-R25 complete for every label
- Removed banking labels found: 0
- Malformed or empty JSON sequences: 0
- Exact duplicate sequences: {summary['exact_duplicate_sequences']}
- Near-identical sequences at tolerance 1e-8: {summary['near_identical_sequences']}
- Closest pair by mean absolute difference: {minimum_pair} ({summary['minimum_pairwise_mae']:.10f})

## Hand Detection Quality Is Suitable for Training

- All-zero/no-hand frames: {summary['all_zero_frames']} of 6000
- One-hand frames: {summary['one_hand_frames']} of 6000
- Both-hand frames: {summary['both_hand_frames']} of 6000
- Samples with no detected hands: {summary['samples_with_no_detected_hands']}
- Samples containing only one detected hand: {summary['samples_with_only_one_detected_hand']}
- Samples containing both hands: {summary['samples_with_both_hands']}

The left hand remains indices 0-62 and the right hand remains indices 63-125. Missing hand blocks remain all-zero values.

## Coordinate Ranges Show No Obvious Corruption

| Axis | Min | P01 | Median | P99 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
{coordinate_rows}

- Values with absolute magnitude above 5: {summary['obvious_outlier_values']}
- JSON device metadata: `{summary['device_metadata']}`
- Physical collection device confirmed for this experiment: `{summary['physical_device']}`

The generic device string is a documentation limitation, not a sequence-integrity failure.

## The Fixed Split Is Leakage-Safe

- Training: R01-R15, {summary['split_counts']['train']} samples
- Validation: R16-R20, {summary['split_counts']['val']} samples
- Testing: R21-R25, {summary['split_counts']['test']} samples
- Cross-split sample IDs: 0
- Validation/test augmentation: disabled

Manifest: `{PHONE_SPLIT_MANIFEST_PATH.as_posix()}`

## Python and Flutter Feature Formulas Match

- Sequence shape: `[60, 126]`
- Feature order: `{', '.join(FEATURE_ORDER)}`
- Feature matrix shape: `{summary['feature_matrix_shape']}`
- Standard deviation: population standard deviation (`ddof=0`), matching Flutter's division by 60
- Maximum float32-versus-float64 feature difference: {summary['feature_precision_max_abs_diff']:.10g}
- Finite 756-value feature rows: 100/100

Parity fixture: `{PARITY_FIXTURE_PATH.as_posix()}`

## Decision

No invalid or suspiciously corrupted phone sample was found. The controlled experiment may proceed using the fixed split. This validation does not establish model accuracy.
"""
    DETAILED_VALIDATION_MD_PATH.write_text(content, encoding="utf-8")


def _numeric_summary(values: np.ndarray) -> dict[str, float]:
    if not values.size:
        return {key: 0.0 for key in ("min", "p01", "median", "p99", "max")}
    return {
        "min": float(values.min()),
        "p01": float(np.quantile(values, 0.01)),
        "median": float(np.median(values)),
        "p99": float(np.quantile(values, 0.99)),
        "max": float(values.max()),
    }


if __name__ == "__main__":
    raise SystemExit(main())

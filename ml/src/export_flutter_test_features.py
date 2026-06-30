"""Export fixed Sprint 2.14 test feature samples for the Flutter prototype.

The Flutter app does not receive raw video in Sprint 2.14. It receives the
same 756 statistical features used by the Sprint 2.13 TFLite model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "ml" / "data_processed" / "datasets" / "signsync_expanded_v2_stats_756f.npz"
OUTPUT_DIR = PROJECT_ROOT / "flutter_app" / "assets" / "test_features"
REPORT_PATH = PROJECT_ROOT / "docs" / "phase_2_evidence" / "sprint_2_14_flutter_test_feature_export_report.md"

SAMPLE_IDS = [
    "P02_A_R01",
    "P02_payment_R01",
    "P02_document_R01",
    "P02_signature_R01",
    "P02_atm_R01",
]


def _to_json_float_list(values: np.ndarray) -> list[float]:
    return [float(value) for value in values.astype(np.float32).tolist()]


def export_samples() -> list[dict[str, object]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing feature dataset: {DATASET_PATH.relative_to(PROJECT_ROOT)}")

    dataset = np.load(DATASET_PATH, allow_pickle=False)
    features = dataset["X_features"]
    labels = dataset["labels"]
    sample_ids = dataset["sample_ids"]

    if features.shape[1] != 756:
        raise ValueError(f"Expected feature width 756, found {features.shape[1]}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exported: list[dict[str, object]] = []

    for sample_id in SAMPLE_IDS:
        matches = np.where(sample_ids == sample_id)[0]
        if len(matches) == 0:
            continue

        row_index = int(matches[0])
        feature_row = features[row_index]
        true_label = str(labels[row_index])
        payload = {
            "sample_id": sample_id,
            "true_label": true_label,
            "feature_shape": [756],
            "features": _to_json_float_list(feature_row),
        }

        output_path = OUTPUT_DIR / f"{sample_id}.json"
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        exported.append(
            {
                "sample_id": sample_id,
                "true_label": true_label,
                "feature_length": len(payload["features"]),
                "output_file": output_path.relative_to(PROJECT_ROOT).as_posix(),
            }
        )

    missing = [sample_id for sample_id in SAMPLE_IDS if sample_id not in {item["sample_id"] for item in exported}]
    if missing:
        raise ValueError(f"Missing requested sample IDs in feature dataset: {', '.join(missing)}")

    return exported


def write_report(exported: list[dict[str, object]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sprint 2.14 Flutter Test Feature Export Report",
        "",
        "## Summary",
        "",
        f"- Exported sample count: {len(exported)}",
        f"- Output folder: {OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}",
        "- Feature length confirmation: 756 values per sample",
        "",
        "## Exported Samples",
        "",
        "| Sample ID | True Label | Feature Length | Output File |",
        "|---|---:|---:|---|",
    ]

    for item in exported:
        lines.append(
            f"| {item['sample_id']} | {item['true_label']} | {item['feature_length']} | {item['output_file']} |"
        )

    lines.extend(
        [
            "",
            "## Sprint Boundary",
            "",
            "These files are prepared test feature vectors only. No raw video collection, live camera capture, "
            "landmark extraction, retraining, or TFLite reconversion was performed in Sprint 2.14.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    exported = export_samples()
    write_report(exported)

    print("Sprint 2.14 Flutter test feature export")
    print("----------------------------------------")
    print(f"Exported sample count: {len(exported)}")
    for item in exported:
        print(f"- {item['sample_id']} -> {item['output_file']} ({item['feature_length']} features)")
    print(f"Report path: {REPORT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print("Flutter test feature export completed successfully.")


if __name__ == "__main__":
    main()

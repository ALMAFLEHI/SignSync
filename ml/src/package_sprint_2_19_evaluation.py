"""Package a complete validated Sprint 2.19 evidence directory."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from sprint_2_19_config import REPORT_ROOT
from sprint_2_19_evaluation import sha256_file, write_json


REQUIRED_RELATIVE_PATHS = [
    "validated/validated_trials.csv",
    "validated/validation_report.json",
    "metrics/overall_metrics.json",
    "metrics/per_class_metrics.csv",
    "metrics/operational_metrics.json",
    "metrics/condition_metrics.csv",
    "metrics/latency_metrics.json",
    "metrics/confidence_metrics.json",
    "metrics/account_vs_savings_metrics.json",
    "metrics/weak_class_metrics.csv",
    "confusion/confusion_matrix.csv",
    "confusion/confusion_matrix_normalized.csv",
    "confusion/confusion_pairs.csv",
    "figures/confusion_matrix.png",
    "figures/confusion_matrix_normalized.png",
    "figures/per_class_recall.png",
    "figures/per_class_acceptance.png",
    "figures/confidence_distribution.png",
    "figures/coverage_vs_accepted_accuracy.png",
    "figures/latency_distribution.png",
    "figures/condition_comparison.png",
    "figures/account_vs_savings.png",
    "figures/weak_class_comparison.png",
    "reports/final_live_evaluation_report.md",
    "reports/operational_performance_report.md",
    "reports/latency_report.md",
    "reports/error_analysis.md",
    "reports/account_vs_savings_report.md",
    "reports/limitations.md",
    "metadata/trial_schedule.csv",
    "metadata/evaluation_protocol.json",
]


def build_artifact_inventory(root: Path) -> list[dict[str, object]]:
    """Build a sorted inventory without including generated inventory files."""
    excluded = {
        "metadata/artifact_inventory.json",
        "metadata/SHA256SUMS.txt",
        "sprint_2_19_evidence_package.zip",
    }
    artifacts = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        artifacts.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return artifacts


def package_evaluation(root: Path = REPORT_ROOT) -> Path:
    """Refuse incomplete physical evidence, then hash and archive it."""
    missing = [relative for relative in REQUIRED_RELATIVE_PATHS if not (root / relative).is_file()]
    raw_exports = (
        [path for path in (root / "raw_exports").glob("*") if path.is_file()]
        if (root / "raw_exports").is_dir()
        else []
    )
    if missing or not raw_exports:
        raise FileNotFoundError(
            "Physical evidence package is incomplete. "
            f"Missing={missing}; raw_export_count={len(raw_exports)}."
        )
    validation = json.loads(
        (root / "validated" / "validation_report.json").read_text(encoding="utf-8")
    )
    if validation.get("status") != "PASS" or not validation.get(
        "physical_results_validated"
    ):
        raise ValueError("Evidence packaging requires a PASS physical validation.")

    inventory = build_artifact_inventory(root)
    metadata = root / "metadata"
    write_json(metadata / "artifact_inventory.json", inventory)
    (metadata / "SHA256SUMS.txt").write_text(
        "".join(f"{item['sha256']}  {item['path']}\n" for item in inventory),
        encoding="utf-8",
    )
    archive = root / "sprint_2_19_evidence_package.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path == archive:
                continue
            zip_file.write(path, path.relative_to(root).as_posix())
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=REPORT_ROOT)
    args = parser.parse_args()
    archive = package_evaluation(args.output_root)
    print(f"PASS: evidence package created: {archive}")
    print(f"SHA-256: {sha256_file(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

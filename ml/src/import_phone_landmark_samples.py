"""Import validated Sprint 2.16A phone landmark samples into a stable local folder."""

from __future__ import annotations

import json
import shutil

from check_phone_landmark_samples import summarize_counts, target_reached, validate_all_samples
from phone_dataset_config import (
    EXPECTED_SAMPLES_PER_LABEL,
    IMPORTED_PHONE_DIR,
    WEAK_LABELS,
)


def import_samples() -> tuple[int, int]:
    """Copy valid sample JSON files into label subfolders without deleting originals."""
    samples, invalid_rows = validate_all_samples()
    if invalid_rows:
        raise ValueError("Cannot import while invalid phone sample files exist.")

    imported_count = 0
    for sample in samples:
        label_dir = IMPORTED_PHONE_DIR / sample.label
        label_dir.mkdir(parents=True, exist_ok=True)
        destination = label_dir / f"{sample.sample_id}.json"
        shutil.copy2(sample.path, destination)
        imported_count += 1

    counts = summarize_counts(samples)
    status_path = IMPORTED_PHONE_DIR / "import_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(
            {
                "imported_count": imported_count,
                "target_reached": target_reached(counts),
                "target_per_label": EXPECTED_SAMPLES_PER_LABEL,
                "counts": {label: counts[label] for label in WEAK_LABELS},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return imported_count, len(invalid_rows)


def main() -> int:
    """Import valid phone samples or report pending status."""
    try:
        imported_count, invalid_count = import_samples()
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print("Sprint 2.16A Phone Sample Import")
    print("--------------------------------")
    print(f"imported samples: {imported_count}")
    print(f"invalid samples: {invalid_count}")
    print(f"import folder: {IMPORTED_PHONE_DIR.as_posix()}")
    if imported_count == 0:
        print("PENDING: no phone samples available to import yet.")
    else:
        print("Phone sample import completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

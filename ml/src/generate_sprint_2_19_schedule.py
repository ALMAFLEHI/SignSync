"""Generate the frozen deterministic Sprint 2.19 block schedule."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from sprint_2_19_config import (
    BLOCK_COUNT,
    DOC_SCHEDULE,
    FINAL_LABELS,
    FLUTTER_SCHEDULE,
    METADATA_DIR,
    PROTOCOL_VERSION,
    RANDOM_SEED,
    REPORT_ROOT,
    STANDARD_BLOCKS,
    STANDARD_CONDITION,
    VARIATION_CONDITION,
    ensure_output_directories,
)


SCHEDULE_COLUMNS = [
    "trial_number",
    "block_number",
    "condition",
    "intended_label",
    "intended_label_index",
    "scheduled_order",
    "random_seed",
]


class XorShift32:
    """Small reproducible generator shared with the Flutter implementation."""

    def __init__(self, seed: int) -> None:
        if seed <= 0 or seed > 0xFFFFFFFF:
            raise ValueError("Seed must be an unsigned non-zero 32-bit integer.")
        self._state = seed

    def next_uint32(self) -> int:
        """Return the next unsigned 32-bit value."""
        value = self._state
        value ^= (value << 13) & 0xFFFFFFFF
        value ^= value >> 17
        value ^= (value << 5) & 0xFFFFFFFF
        self._state = value & 0xFFFFFFFF
        return self._state


def generate_schedule() -> list[dict[str, object]]:
    """Return ten balanced randomized blocks using the frozen seed."""
    generator = XorShift32(RANDOM_SEED)
    label_to_index = {label: index for index, label in enumerate(FINAL_LABELS)}
    rows: list[dict[str, object]] = []
    trial_number = 1
    for block_number in range(1, BLOCK_COUNT + 1):
        labels = list(FINAL_LABELS)
        for index in range(len(labels) - 1, 0, -1):
            swap_index = generator.next_uint32() % (index + 1)
            labels[index], labels[swap_index] = labels[swap_index], labels[index]
        condition = (
            STANDARD_CONDITION
            if block_number in STANDARD_BLOCKS
            else VARIATION_CONDITION
        )
        for scheduled_order, label in enumerate(labels, start=1):
            rows.append(
                {
                    "trial_number": trial_number,
                    "block_number": block_number,
                    "condition": condition,
                    "intended_label": label,
                    "intended_label_index": label_to_index[label],
                    "scheduled_order": scheduled_order,
                    "random_seed": RANDOM_SEED,
                }
            )
            trial_number += 1
    return rows


def write_schedule(path: Path, rows: list[dict[str, object]]) -> None:
    """Write stable UTF-8 CSV bytes for cross-platform hashing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=SCHEDULE_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    """Return uppercase SHA-256 for an artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    """Create matching documentation, Flutter, and report schedule copies."""
    ensure_output_directories()
    rows = generate_schedule()
    report_schedule = METADATA_DIR / "trial_schedule.csv"
    for path in (DOC_SCHEDULE, FLUTTER_SCHEDULE, report_schedule):
        write_schedule(path, rows)
    hashes = {sha256_file(path) for path in (DOC_SCHEDULE, FLUTTER_SCHEDULE, report_schedule)}
    if len(hashes) != 1:
        raise ValueError("Schedule copies are not byte-identical.")
    schedule_hash = hashes.pop()
    protocol = {
        "project": "SignSync",
        "sprint": "2.19",
        "protocol_version": PROTOCOL_VERSION,
        "status": "AUTOMATED_PREPARATION_ONLY_PHYSICAL_EXECUTION_PENDING",
        "random_seed": RANDOM_SEED,
        "schedule_sha256": schedule_hash,
        "blocks": 10,
        "trials": 400,
        "standard_trials": 200,
        "mild_variation_trials": 200,
        "trials_per_label": 10,
        "trials_per_label_per_condition": 5,
        "warm_up_trials_excluded": 5,
        "first_completed_inference_is_formal": True,
        "technical_failures_logged_separately": True,
        "physical_results_available": False,
    }
    (METADATA_DIR / "evaluation_protocol.json").write_text(
        json.dumps(protocol, indent=2) + "\n",
        encoding="utf-8",
    )
    (REPORT_ROOT / "README.md").write_text(
        "# Sprint 2.19 Final Technical Evaluation\n\n"
        "Automated protocol preparation is complete. Raw exports, metrics, figures, "
        "and final reports remain empty until the fresh 400-trial Samsung A55 session "
        "is completed and validated. No physical results are fabricated.\n",
        encoding="utf-8",
    )
    print("Sprint 2.19 Trial Schedule")
    print("---------------------------")
    print("trials: 400")
    print("blocks: 10")
    print("standard / mild variation: 200 / 200")
    print("per label: 5 standard + 5 mild variation")
    print(f"seed: {RANDOM_SEED}")
    print(f"SHA-256: {schedule_hash}")
    print("PASS: frozen schedule copies created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

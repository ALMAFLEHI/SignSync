"""Verify the Sprint 2.16A V3 active label scope and JSON contract."""

from __future__ import annotations

import json
from pathlib import Path

from labels import (
    ALL_LABELS_V3_76,
    ALPHABET_LABELS,
    BANKING_INTENTS_V3_40,
    DIGIT_LABELS,
    REMOVED_BANKING_INTENTS_V3_10,
)


SCOPE_PATH = Path("ml") / "config" / "signsync_active_scope_v3_40.json"


def main() -> int:
    """Validate Python and JSON scopes, then print the required summary."""
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    active_duplicates = len(BANKING_INTENTS_V3_40) - len(set(BANKING_INTENTS_V3_40))
    removed_in_active = set(REMOVED_BANKING_INTENTS_V3_10).intersection(
        BANKING_INTENTS_V3_40
    )

    checks = [
        scope.get("active_banking_intents") == BANKING_INTENTS_V3_40,
        scope.get("removed_banking_intents") == REMOVED_BANKING_INTENTS_V3_10,
        scope.get("future_model_input_shape") == [1, 756],
        scope.get("future_model_output_shape") == [1, 76],
        scope.get("historical_model_output_shape") == [1, 86],
        len(ALPHABET_LABELS) == 26,
        len(DIGIT_LABELS) == 10,
        len(BANKING_INTENTS_V3_40) == 40,
        len(REMOVED_BANKING_INTENTS_V3_10) == 10,
        len(ALL_LABELS_V3_76) == 76,
        active_duplicates == 0,
        not removed_in_active,
    ]

    print("Sprint 2.16A Active Scope V3 Verification")
    print("-----------------------------------------")
    print(f"Alphabet labels: {len(ALPHABET_LABELS)}")
    print(f"Digit labels: {len(DIGIT_LABELS)}")
    print(f"Banking intents: {len(BANKING_INTENTS_V3_40)}")
    print(f"Removed banking intents: {len(REMOVED_BANKING_INTENTS_V3_10)}")
    print(f"Future total classes: {len(ALL_LABELS_V3_76)}")
    print(f"Duplicate active labels: {active_duplicates}")
    print(f"Removed labels found in active scope: {len(removed_in_active)}")
    if all(checks):
        print("PASS: V3 active scope and machine-readable configuration match.")
        return 0
    print("FAIL: V3 active scope validation failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

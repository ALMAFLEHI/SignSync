"""Initial SignSync dataset vocabulary for Phase 2, Sprint 2.1."""

# The alphabet labels represent static ASL letters A to Z.
ALPHABET: list[str] = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]

# Digits are stored as strings so every label uses the same text format.
DIGITS: list[str] = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
]

# First banking service intent vocabulary for the FYP dataset scope.
BANKING_INTENTS_V1: list[str] = [
    "deposit",
    "withdraw",
    "balance",
    "transfer",
    "account",
    "card",
    "pin",
    "password",
    "identity_verification",
    "cash",
    "receipt",
    "fee",
    "loan",
    "savings",
    "open_account",
    "close_account",
    "fraud",
    "block_card",
    "help",
    "confirm",
]

ALL_LABELS: list[str] = ALPHABET + DIGITS + BANKING_INTENTS_V1


def _validate_labels() -> None:
    """Validate the Sprint 2.1 vocabulary before other scripts use it."""
    expected_total = 56

    if len(ALL_LABELS) != expected_total:
        raise ValueError(
            f"Expected {expected_total} labels, but found {len(ALL_LABELS)}."
        )

    if len(set(ALL_LABELS)) != len(ALL_LABELS):
        raise ValueError("Dataset labels must be unique. Duplicate labels were found.")


_validate_labels()

"""Versioned SignSync dataset vocabularies for the Phase 2 collection workflows."""

# Keep the core ASL label groups independent so V1 and V2 can share them safely.
ALPHABET_LABELS: list[str] = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
]

DIGIT_LABELS: list[str] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

# V1 is frozen for the completed Sprint 2.1 to Sprint 2.10 data and model workflow.
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
    "payment",
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

# Sprint 2.11 adds these banking intents for a later expanded-dataset evaluation.
BANKING_INTENTS_EXPANSION_V2: list[str] = [
    "statement",
    "transaction_history",
    "bill_payment",
    "online_banking",
    "mobile_banking",
    "atm",
    "branch",
    "cheque",
    "currency_exchange",
    "exchange_rate",
    "interest_rate",
    "fixed_deposit",
    "credit_card",
    "debit_card",
    "lost_card",
    "replace_card",
    "change_pin",
    "reset_password",
    "refund",
    "dispute_transaction",
    "complaint",
    "appointment",
    "customer_service",
    "update_details",
    "phone_number",
    "email_address",
    "address_change",
    "account_number",
    "card_limit",
    "daily_limit",
]

BANKING_INTENTS_V2: list[str] = BANKING_INTENTS_V1 + BANKING_INTENTS_EXPANSION_V2

ALL_LABELS_V1: list[str] = ALPHABET_LABELS + DIGIT_LABELS + BANKING_INTENTS_V1
ALL_LABELS_V2: list[str] = ALPHABET_LABELS + DIGIT_LABELS + BANKING_INTENTS_V2

NORMAL_MODE_LABELS_V1: list[str] = ALPHABET_LABELS + BANKING_INTENTS_V1
NORMAL_MODE_LABELS_V2: list[str] = ALPHABET_LABELS + BANKING_INTENTS_V2
NUMBER_MODE_LABELS: list[str] = DIGIT_LABELS

# Existing scripts retain their original public names. New recording uses V2 by default.
ALPHABET = ALPHABET_LABELS
DIGITS = DIGIT_LABELS
BANKING_INTENTS = BANKING_INTENTS_V2
ALL_LABELS = ALL_LABELS_V2


def _validate_unique(labels: list[str], label_group_name: str) -> None:
    """Raise a clear error when a label group contains duplicate entries."""
    if len(set(labels)) != len(labels):
        raise ValueError(f"{label_group_name} must contain unique labels.")


def _validate_labels() -> None:
    """Protect the frozen V1 scope and the Sprint 2.11 expanded V2 scope."""
    for label_group, label_group_name in (
        (ALPHABET_LABELS, "Alphabet labels"),
        (DIGIT_LABELS, "Digit labels"),
        (BANKING_INTENTS_V1, "V1 banking intents"),
        (BANKING_INTENTS_EXPANSION_V2, "V2 banking intent expansion"),
        (BANKING_INTENTS_V2, "V2 banking intents"),
        (ALL_LABELS_V1, "V1 all labels"),
        (ALL_LABELS_V2, "V2 all labels"),
        (NORMAL_MODE_LABELS_V2, "V2 Normal Mode labels"),
        (NUMBER_MODE_LABELS, "Number Mode labels"),
    ):
        _validate_unique(label_group, label_group_name)

    if "receipt" in ALL_LABELS_V2:
        raise ValueError("The deprecated receipt label must be excluded from every vocabulary.")
    if "payment" not in ALL_LABELS_V1 or "payment" not in ALL_LABELS_V2:
        raise ValueError("The payment label must remain in the V1 and V2 vocabularies.")
    if len(ALL_LABELS_V1) != 56:
        raise ValueError(f"V1 must contain 56 labels, found {len(ALL_LABELS_V1)}.")
    if len(BANKING_INTENTS_V2) != 50:
        raise ValueError(
            f"V2 must contain 50 banking intents, found {len(BANKING_INTENTS_V2)}."
        )
    if len(ALL_LABELS_V2) != 86:
        raise ValueError(f"V2 must contain 86 labels, found {len(ALL_LABELS_V2)}.")
    if len(NORMAL_MODE_LABELS_V2) != 76:
        raise ValueError(
            "V2 Normal Mode must contain 76 alphabet and banking labels, "
            f"found {len(NORMAL_MODE_LABELS_V2)}."
        )
    if len(NUMBER_MODE_LABELS) != 10:
        raise ValueError(
            f"Number Mode must contain 10 digit labels, found {len(NUMBER_MODE_LABELS)}."
        )


_validate_labels()

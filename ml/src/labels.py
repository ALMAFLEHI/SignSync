"""Versioned SignSync dataset vocabularies for the Phase 2 workflows."""

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
    "document",
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
    "signature",
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

BANKING_INTENTS_V2_50: list[str] = BANKING_INTENTS_V1 + BANKING_INTENTS_EXPANSION_V2

# V3 narrows only the active/future scope. Historical V2 data and models stay intact.
REMOVED_BANKING_INTENTS_V3_10: list[str] = [
    "online_banking",
    "mobile_banking",
    "currency_exchange",
    "exchange_rate",
    "fixed_deposit",
    "customer_service",
    "update_details",
    "phone_number",
    "email_address",
    "address_change",
]

BANKING_INTENTS_V3_40: list[str] = [
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
    "statement",
    "document",
    "bill_payment",
    "atm",
    "branch",
    "cheque",
    "interest_rate",
    "credit_card",
    "debit_card",
    "lost_card",
    "replace_card",
    "change_pin",
    "reset_password",
    "refund",
    "signature",
    "complaint",
    "appointment",
    "account_number",
    "card_limit",
    "daily_limit",
]

# Sprint 2.16A proved the phone-domain method using these four pilot intents.
SPRINT_2_16A_PILOT_INTENTS_4: list[str] = [
    "transfer",
    "document",
    "signature",
    "atm",
]

# Sprint 2.16B collects phone landmarks for every active banking intent not in
# the completed pilot. The order is the retained V3 banking order.
SPRINT_2_16B_REMAINING_BANKING_INTENTS_36: list[str] = [
    "deposit",
    "withdraw",
    "balance",
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
    "statement",
    "bill_payment",
    "branch",
    "cheque",
    "interest_rate",
    "credit_card",
    "debit_card",
    "lost_card",
    "replace_card",
    "change_pin",
    "reset_password",
    "refund",
    "complaint",
    "appointment",
    "account_number",
    "card_limit",
    "daily_limit",
]

# Historical aliases are retained so completed Sprint 2.11-2.15 scripts reproduce.
BANKING_INTENTS_V2: list[str] = BANKING_INTENTS_V2_50

ALL_LABELS_V1: list[str] = ALPHABET_LABELS + DIGIT_LABELS + BANKING_INTENTS_V1
ALL_LABELS_V2_86: list[str] = ALPHABET_LABELS + DIGIT_LABELS + BANKING_INTENTS_V2_50
ALL_LABELS_V3_76: list[str] = ALPHABET_LABELS + DIGIT_LABELS + BANKING_INTENTS_V3_40
ALL_LABELS_V2: list[str] = ALL_LABELS_V2_86

NORMAL_MODE_LABELS_V1: list[str] = ALPHABET_LABELS + BANKING_INTENTS_V1
NORMAL_MODE_LABELS_V2: list[str] = ALPHABET_LABELS + BANKING_INTENTS_V2
NORMAL_MODE_LABELS_V3: list[str] = ALPHABET_LABELS + BANKING_INTENTS_V3_40
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
    """Protect historical V1/V2 scopes and the active Sprint 2.16A V3 scope."""
    for label_group, label_group_name in (
        (ALPHABET_LABELS, "Alphabet labels"),
        (DIGIT_LABELS, "Digit labels"),
        (BANKING_INTENTS_V1, "V1 banking intents"),
        (BANKING_INTENTS_EXPANSION_V2, "V2 banking intent expansion"),
        (BANKING_INTENTS_V2, "V2 banking intents"),
        (REMOVED_BANKING_INTENTS_V3_10, "V3 removed banking intents"),
        (BANKING_INTENTS_V3_40, "V3 active banking intents"),
        (SPRINT_2_16A_PILOT_INTENTS_4, "Sprint 2.16A pilot intents"),
        (
            SPRINT_2_16B_REMAINING_BANKING_INTENTS_36,
            "Sprint 2.16B remaining banking intents",
        ),
        (ALL_LABELS_V1, "V1 all labels"),
        (ALL_LABELS_V2, "V2 all labels"),
        (ALL_LABELS_V3_76, "V3 all labels"),
        (NORMAL_MODE_LABELS_V2, "V2 Normal Mode labels"),
        (NORMAL_MODE_LABELS_V3, "V3 Normal Mode labels"),
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
    if len(REMOVED_BANKING_INTENTS_V3_10) != 10:
        raise ValueError("V3 must document exactly 10 removed banking intents.")
    if len(BANKING_INTENTS_V3_40) != 40:
        raise ValueError(
            f"V3 must contain 40 banking intents, found {len(BANKING_INTENTS_V3_40)}."
        )
    if len(SPRINT_2_16A_PILOT_INTENTS_4) != 4:
        raise ValueError("Sprint 2.16A must retain exactly four pilot intents.")
    if len(SPRINT_2_16B_REMAINING_BANKING_INTENTS_36) != 36:
        raise ValueError("Sprint 2.16B must contain exactly 36 remaining intents.")
    if set(SPRINT_2_16A_PILOT_INTENTS_4).intersection(
        SPRINT_2_16B_REMAINING_BANKING_INTENTS_36
    ):
        raise ValueError("Sprint 2.16A pilot and Sprint 2.16B remaining scopes overlap.")
    reconstructed_active_scope = [
        label
        for label in BANKING_INTENTS_V3_40
        if label not in SPRINT_2_16A_PILOT_INTENTS_4
    ]
    if reconstructed_active_scope != SPRINT_2_16B_REMAINING_BANKING_INTENTS_36:
        raise ValueError("Sprint 2.16B labels must preserve active V3 order.")
    if set(SPRINT_2_16A_PILOT_INTENTS_4).union(
        SPRINT_2_16B_REMAINING_BANKING_INTENTS_36
    ) != set(BANKING_INTENTS_V3_40):
        raise ValueError("Sprint 2.16A and 2.16B scopes must reconstruct V3 exactly.")
    if set(SPRINT_2_16B_REMAINING_BANKING_INTENTS_36).intersection(
        REMOVED_BANKING_INTENTS_V3_10
    ):
        raise ValueError("Removed labels cannot appear in Sprint 2.16B.")
    if set(SPRINT_2_16B_REMAINING_BANKING_INTENTS_36).intersection(
        ALPHABET_LABELS + DIGIT_LABELS
    ):
        raise ValueError("Sprint 2.16B is banking-intent-only.")
    if set(REMOVED_BANKING_INTENTS_V3_10).intersection(BANKING_INTENTS_V3_40):
        raise ValueError("Removed V3 banking intents must not appear in the active V3 scope.")
    if set(BANKING_INTENTS_V2_50) != (
        set(BANKING_INTENTS_V3_40) | set(REMOVED_BANKING_INTENTS_V3_10)
    ):
        raise ValueError("V3 retained and removed banking intents must partition V2 exactly.")
    if len(ALL_LABELS_V3_76) != 76:
        raise ValueError(f"V3 must contain 76 labels, found {len(ALL_LABELS_V3_76)}.")
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

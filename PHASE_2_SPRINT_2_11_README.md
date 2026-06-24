# Phase 2 Sprint 2.11: Banking Intent Expansion

## Goal

Sprint 2.11 expands the SignSync banking vocabulary by 30 new banking intents and prepares a safe manual raw-video recording workflow.

## What This Sprint Does

- Keeps the completed 56-label V1 vocabulary available for Sprint 2.8, 2.9, and 2.10 verification workflows.
- Activates an 86-label V2 collection vocabulary.
- Generates manual commands and an interactive runner for 300 new P02 raw recordings.
- Verifies the new collection scope after recording is completed.

## What This Sprint Does Not Do

- Extract landmarks.
- Create a new `.npz` dataset.
- Train or evaluate a model.
- Convert a model to TFLite.
- Create Flutter integration.
- Start Sprint 2.12.

## Expanded Label Scope

- Alphabet labels: 26
- Digit labels: 10
- Banking intents: 50
- Total V2 labels: 86
- Normal Mode: 76 labels (alphabet plus banking intents)
- Number Mode: 10 labels (digits only)

## New Banking Intents

`statement`, `transaction_history`, `bill_payment`, `online_banking`, `mobile_banking`, `atm`, `branch`, `cheque`, `currency_exchange`, `exchange_rate`, `interest_rate`, `fixed_deposit`, `credit_card`, `debit_card`, `lost_card`, `replace_card`, `change_pin`, `reset_password`, `refund`, `dispute_transaction`, `complaint`, `appointment`, `customer_service`, `update_details`, `phone_number`, `email_address`, `address_change`, `account_number`, `card_limit`, `daily_limit`

`payment` remains included. `receipt` remains excluded.

## Recording Scope

- Participant: P02
- Camera index: 1
- New labels: 30
- Repetitions per label: 10
- Expected videos: 300
- Notes: `Sprint 2.11 banking intent expansion`

## Commands

Run these commands from the project root.

```powershell
python -m py_compile ml/src/labels.py ml/src/sprint_2_11_intent_expansion_config.py ml/src/check_sprint_2_11_setup.py ml/src/generate_sprint_2_11_recording_commands.py ml/src/run_sprint_2_11_collection.py ml/src/check_sprint_2_11_collection.py

python ml/src/check_sprint_2_11_setup.py

python ml/src/generate_sprint_2_11_recording_commands.py

python ml/src/run_sprint_2_11_collection.py --participant P02 --camera-index 1 --dry-run

python ml/src/run_sprint_2_11_collection.py --participant P02 --camera-index 1

python ml/src/check_sprint_2_11_collection.py --participant P02
```

Do not run the real collection command until you are ready to record manually. The collection check is intended to run only after all 300 recordings are complete.

## Suggested Evidence Screenshots

- `01_sprint_2_11_setup_check_passed.png`
- `02_sprint_2_11_commands_generated.png`
- `03_sprint_2_11_collection_dry_run.png`
- `04_sprint_2_11_recording_started.png`
- `05_sprint_2_11_collection_verification_passed.png`

## Next Sprint

Sprint 2.12 will extract landmarks, prepare the expanded dataset, and train and evaluate the expanded model. Do not start it until Sprint 2.11 collection and verification are confirmed.

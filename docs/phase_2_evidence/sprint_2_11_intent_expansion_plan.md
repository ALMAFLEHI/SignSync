# Sprint 2.11 Intent Expansion Plan

## Goal

Expand the SignSync banking vocabulary by 30 practical banking intents and prepare a controlled raw-video recording workflow for them.

## Why This Expansion Is Needed

The completed V1 vocabulary supports a controlled 56-label baseline. The additional banking intents broaden the service interaction scope so later work can evaluate a more representative banking vocabulary.

## New Banking Intents

- statement
- document
- bill_payment
- online_banking
- mobile_banking
- atm
- branch
- cheque
- currency_exchange
- exchange_rate
- interest_rate
- fixed_deposit
- credit_card
- debit_card
- lost_card
- replace_card
- change_pin
- reset_password
- refund
- signature
- complaint
- appointment
- customer_service
- update_details
- phone_number
- email_address
- address_change
- account_number
- card_limit
- daily_limit

## Recording Scope

- Participant: P02
- Camera index: 1
- New labels: 30
- Repetitions per label: 10
- Expected new raw videos: 300
- Metadata note: `Sprint 2.11 banking intent expansion`

## Sprint 2.11 Rework: Replace Missing Labels and Redo Incorrect Samples

Real collection showed that `transaction_history` and `dispute_transaction` were not practical enough for the current FYP recording scope. The Sprint 2.11 vocabulary was reworked without changing the total V2 label count.

- `transaction_history` replaced by `document`
- `dispute_transaction` replaced by `signature`
- redo `atm` R01
- redo `account_number` R01
- expected rework recordings: 22
- final Sprint 2.11 expected videos: 300

## Scope Boundary

Sprint 2.11 creates only the vocabulary expansion and raw-video recording workflow. It does not perform landmark extraction, dataset preparation, model training, TFLite conversion, or Flutter work.

## Accuracy Risk

Adding 30 banking intents may reduce classification accuracy once the expanded dataset is trained. Sprint 2.12 will extract landmarks, prepare the expanded dataset, and train and evaluate it. If accuracy drops, a later collection pass can add 10 recordings only for weak banking intents identified by evaluation.

# Sprint 2.12 Expanded Dataset Plan

## Goal

Sprint 2.12 processes the completed Sprint 2.11 recordings into an expanded V2 landmark dataset, prepares an 805-sample ML dataset, trains a scikit-learn baseline, and compares the result with the Sprint 2.10 V1 baseline.

## Expanded V2 Scope

- Alphabet labels: 26
- Digit labels: 10
- Banking intents: 50
- Total labels: 86
- Normal Mode V2: alphabet plus banking intents, 76 labels
- Number Mode: digits only, 10 labels
- Expected samples: 805
- Target frames: 60
- Landmark dimension: 126
- Mask dimension: 2

## Label Decisions

- `payment` remains included.
- `receipt` remains excluded.
- `document` is included.
- `signature` is included.
- `transaction_history` is excluded.
- `dispute_transaction` is excluded.

## Sample Rules

Trial V1 labels with 5 repetitions:

- `A`, `B`, `C`, `0`, `1`, `2`, `deposit`, `withdraw`, `balance`, `help`, `confirm`

All other V2 labels use 10 repetitions.

## Split Strategy

- Trial labels with 5 repetitions: R01-R03 train, R04 validation, R05 test
- Ten-repetition labels: R01-R07 train, R08 validation, R09-R10 test

Expected split counts:

- train: 558
- validation: 86
- test: 161
- total: 805

## Scope Boundary

Sprint 2.12 does not record videos, modify raw videos, overwrite Sprint 2.10 outputs, convert to TFLite, create Flutter files, or start Sprint 2.13.

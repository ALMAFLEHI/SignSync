# Sprint 2.16B Plan: Full Banking Intent Phone Dataset Expansion

## Status

Collection workflow prepared. Manual Samsung Galaxy A55 recording is pending.

## Why This Sprint Is Necessary

Sprint 2.16A validated the phone-domain method. The four pilot intents `transfer`, `document`, `signature`, and `atm` achieved 40/40 in controlled live A55 testing after Experiment B incorporated real phone landmarks and conservative training-only augmentation.

This is a method-validation PASS, not whole-model live coverage. Banking classes without real A55 data still performed poorly. The observed laptop-camera versus phone-camera landmark domain shift means every active banking intent needs real A55 coverage before the complete banking workflow can be judged fairly.

## Exact Scope

Sprint 2.16B collects only these 36 active banking intents, in V3 order:

`deposit`, `withdraw`, `balance`, `account`, `card`, `pin`, `password`, `identity_verification`, `cash`, `payment`, `fee`, `loan`, `savings`, `open_account`, `close_account`, `fraud`, `block_card`, `help`, `confirm`, `statement`, `bill_payment`, `branch`, `cheque`, `interest_rate`, `credit_card`, `debit_card`, `lost_card`, `replace_card`, `change_pin`, `reset_password`, `refund`, `complaint`, `appointment`, `account_number`, `card_limit`, `daily_limit`.

The completed pilot labels are protected and excluded from new recording. Alphabet A-Z and digits 0-9 are reserved for Sprint 2.16C. The 10 removed banking labels remain excluded.

## Targets

- Existing Sprint 2.16A pilot: 4 labels x 25 = 100 samples
- Sprint 2.16B expansion: 36 labels x 25 = 900 new samples
- Final banking phone dataset: 40 labels x 25 = 1,000 samples
- Participant: `P02_PHONE`
- Repetitions: R01-R25 for each label
- Sequence: 60 valid frames x 126 values
- Storage: landmark JSON only; no raw video and no upload

## Workflow

1. Review the prepared collection page and automated checks.
2. Manually record the 36 labels on the Samsung Galaxy A55, one tapped sample at a time.
3. Pull the complete Android folder into a staging directory.
4. Merge only new files after matching-name SHA-256 checks protect existing samples.
5. Run `check_sprint_2_16B_phone_samples.py` throughout partial collection.
6. Continue until the checker reports 900/900 new samples and 1,000/1,000 total banking samples with zero invalid or duplicate files.
7. Create the versioned backup ZIP only after final PASS.
8. Review the evidence before any split, augmentation, or training work.

## Sprint Boundary

No augmentation or training occurs until all files are pulled and validated. Experiment A/B artifacts and the deployed Experiment B Flutter assets remain unchanged. Sprint 2.16C does not start during this sprint-preparation task.

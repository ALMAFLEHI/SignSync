# Sprint 2.19 Final Technical Recognition Evaluation

## Status: COMPLETED - REVISED VALID EVALUATION

## Objective

Produce the final corrected technical recognition evaluation without new human
testing by reproducing the locked held-out results, consolidating existing A55
deployment evidence, and re-verifying model, dataset, package, and privacy
integrity.

## Revised Valid Evaluation Design

Sprint 2.19 consolidates three separate evidence components: (1) formal offline
evaluation on the locked corrected 200-sample held-out set, (2) existing Samsung
Galaxy A55 deployment smoke testing, and (3) automated deployment and integrity
verification. The prepared 400-trial live protocol was not executed and no formal
live-device accuracy is claimed.

## Corrected Model and Dataset Identity

- Model: `signsync_40class_account_corrected_v2`
- Winner: `experiment_B_phone_augmentation`
- Input/output: float32 `[1,756] -> [1,40]`
- Active data: 1,000 real phone landmark samples; 40 classes; 25 per class
- Corrected data: 25 replacement `account` samples; 975 non-account samples preserved
- Threshold: 0.80; minimum margin: 0.00
- Dynamic-range model is the active Android model

## Formal Offline Held-Out Evaluation

- Support: 200 real Samsung A55 landmark samples, exactly 5 per class
- Correct: 191; incorrect: 9
- Accuracy: 0.9550
- Accuracy 95% Wilson CI: 0.9167 to 0.9761
- Macro precision: 0.9625
- Macro recall: 0.9550
- Macro F1: 0.9542
- Weighted F1: 0.9542

### Per-Class Metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `deposit` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `withdraw` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `balance` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `transfer` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `card` | 0.5000 | 0.6000 | 0.5455 | 5 |
| `pin` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `password` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `identity_verification` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `cash` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `payment` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `fee` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `loan` | 1.0000 | 0.6000 | 0.7500 | 5 |
| `savings` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `open_account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `close_account` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `fraud` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `block_card` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `help` | 1.0000 | 0.6000 | 0.7500 | 5 |
| `confirm` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `statement` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `document` | 1.0000 | 0.8000 | 0.8889 | 5 |
| `bill_payment` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `atm` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `branch` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `cheque` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `interest_rate` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `credit_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `debit_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `lost_card` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `replace_card` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `change_pin` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `reset_password` | 0.8333 | 1.0000 | 0.9091 | 5 |
| `refund` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `signature` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `complaint` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `appointment` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `account_number` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `card_limit` | 1.0000 | 1.0000 | 1.0000 | 5 |
| `daily_limit` | 1.0000 | 1.0000 | 1.0000 | 5 |

### Observed Confusions

- `card` -> `cash`: 1
- `card` -> `replace_card`: 1
- `document` -> `card`: 1
- `help` -> `block_card`: 1
- `help` -> `card`: 1
- `loan` -> `pin`: 1
- `loan` -> `reset_password`: 1
- `payment` -> `card`: 1
- `withdraw` -> `password`: 1

Strongest classes (F1=1.0000): `deposit`, `balance`, `transfer`, `account`, `identity_verification`, `fee`, `savings`, `open_account`, `close_account`, `fraud`, `confirm`, `statement`, `bill_payment`, `atm`, `branch`, `cheque`, `interest_rate`, `credit_card`, `debit_card`, `lost_card`, `change_pin`, `refund`, `signature`, `complaint`, `appointment`, `account_number`, `card_limit`, `daily_limit`.

Lowest F1 classes: `card` (0.5455), `help` (0.7500), `loan` (0.7500), `document` (0.8889), `payment` (0.8889), `withdraw` (0.8889), `block_card` (0.9091), `cash` (0.9091).

## Confidence and Rejection at Frozen Threshold

- Coverage: 0.9750
- Rejection rate: 0.0250
- Accepted accuracy: 0.9795
- Correct and accepted: 191
- Incorrect and accepted: 4
- Correct but rejected: 0
- Incorrect and rejected: 5
- Incorrect confidence >=0.95: 3
- Incorrect confidence >=0.90: 3
- Incorrect confidence >=0.80: 4
- Correct confidence <0.80: 0

No threshold was selected or tuned in Sprint 2.19.

## Account Versus Savings

Both `account` and `savings` achieved precision, recall, and F1 of 1.0000 on
five held-out samples each. `account` -> `savings` confusion was 0 and `savings`
-> `account` confusion was 0. This small support is not a broad generalization claim.

## Samsung A55 Smoke Evidence

The user-confirmed corrected Sprint 2.18 deployment smoke test covered all 40
intents on a Samsung Galaxy A55. Representative screenshots verify corrected-v2
model loading, `[1,756] -> [1,40]`, threshold 0.80, account recognition, document,
credit-card and complaint recognition, manual details, banker view, and local
diagnostics. Account and savings were manually checked as separate signs. This is
coverage and deployment evidence only, not a repeated-trial statistical study.

## Automated Deployment Verification

Sprint 2.18 already recorded `flutter analyze` PASS, 90 Flutter tests PASS,
Android debug APK build PASS, and the corrected post-deployment checker PASS.
That checker verified source/deployed hashes, both TFLite contracts, query
mapping, dataset integrity, package IDs, and the offline privacy boundary.
Sprint 2.19 changed no Flutter source, so no unnecessary rebuild was performed.

## Latency

The corrected package records development-machine dynamic-range TFLite latency
of 0.0317 ms mean,
0.0273 ms median,
and 0.0507 ms P95.
These values are not Samsung A55 latency. Existing A55 screenshots provide only
five in-memory timing examples and three live capture examples; they are reported
individually in `latency_summary.md`, without aggregate mobile statistics.

## Technical Targets

| Target | Status | Evidence scope |
|---|---|---|
| Held-out test accuracy >= 90% | **PASS** | formal offline |
| Held-out macro F1 >= 90% | **PASS** | formal offline |
| Corrected account recall >= 90% | **PASS** | formal offline |
| Corrected savings recall >= 90% | **PASS** | formal offline |
| Zero account/savings direct confusion | **PASS** | formal offline |
| Keras/TFLite top-1 parity 100% | **PASS** | corrected package verification |
| Model input/output contract | **PASS** | corrected Sprint 2.18 automated deployment |
| Query mapping | **PASS** | corrected Sprint 2.18 automated deployment |
| Dataset integrity | **PASS** | integrity audit |
| Offline/on-device privacy | **PASS** | deployment design and screenshots |
| A55 deployment smoke test | **PASS** | user-confirmed all-intent coverage plus representative screenshots |
| Large formal live-device statistical study | **PARTIAL** | 400-trial protocol prepared but not executed; recorded as a limitation |

## Privacy and Integrity

All inference remains on device. No cloud service, database, customer banking
data, video upload, or interaction persistence was added. Corrected model hashes,
the deployment manifest, dataset manifest, 1,000-sample count, canonical backup,
package IDs, and the supersession marker all passed.

## Limitations

- Test support is 200 samples from one participant/device collection context.
- Per-class support is five, so class estimates have substantial uncertainty.
- The A55 evidence is a coverage smoke test, not formal live accuracy evidence.
- Comprehensive raw mobile latency observations were not collected.
- The optional 400-trial protocol was prepared but not executed.
- Observed class weaknesses do not establish their underlying causes.

## Completion Checklist

- [x] Corrected 200-row prediction artifact validated without modification.
- [x] Forty frozen classes and five held-out samples per class verified.
- [x] Overall, macro, weighted, and per-class metrics reproduced.
- [x] Raw and normalized confusion matrices generated.
- [x] Confidence and rejection analysis completed at frozen threshold 0.80.
- [x] Account-versus-savings metrics and direct confusions verified.
- [x] Weak-class and error analysis completed with interpretation boundaries.
- [x] Desktop latency and existing A55 observations kept separate.
- [x] Existing A55 evidence labelled as smoke testing, not formal accuracy.
- [x] Protected hashes, dataset count, backup, package IDs, and privacy passed.
- [x] Artifact inventory, checksums, reports, figures, and evidence created.
- [x] Optional 400-trial preparation marked unexecuted; Sprint 2.20 not started.

## Completion Boundary

No new human trials were required. No 400-trial result was fabricated. No Flutter
source changed and the validated Sprint 2.18 build was not rebuilt. No model
training, fine-tuning, TFLite conversion, threshold change, dataset modification,
cloud integration, commit, push, or Sprint 2.20 work occurred.

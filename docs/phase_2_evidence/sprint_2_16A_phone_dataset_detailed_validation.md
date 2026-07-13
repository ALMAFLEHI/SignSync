# Sprint 2.16A Phone Dataset Detailed Validation

## Technical Summary

**PASS.** All 100 original Samsung A55 phone landmark JSON files passed structural, uniqueness, repetition, finite-value, hand-slot, duplicate-sequence, range, split, and feature-shape checks. The files were read only and were not modified.

## The Dataset Is Complete and Unique

| Label | Valid Samples | Required | Status |
| --- | ---: | ---: | --- |
| transfer | 25 | 25 | PASS |
| document | 25 | 25 | PASS |
| signature | 25 | 25 | PASS |
| atm | 25 | 25 | PASS |

- Unique sample IDs: 100/100
- Unique label/repetition pairs: 100/100
- Repetitions: R01-R25 complete for every label
- Removed banking labels found: 0
- Malformed or empty JSON sequences: 0
- Exact duplicate sequences: 0
- Near-identical sequences at tolerance 1e-8: 0
- Closest pair by mean absolute difference: P02_PHONE_atm_R20, P02_PHONE_atm_R24 (0.0048809123)

## Hand Detection Quality Is Suitable for Training

- All-zero/no-hand frames: 0 of 6000
- One-hand frames: 3471 of 6000
- Both-hand frames: 2529 of 6000
- Samples with no detected hands: 0
- Samples containing only one detected hand: 21
- Samples containing both hands: 79

The left hand remains indices 0-62 and the right hand remains indices 63-125. Missing hand blocks remain all-zero values.

## Coordinate Ranges Show No Obvious Corruption

| Axis | Min | P01 | Median | P99 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| x | -0.081346 | 0.137587 | 0.463577 | 0.863162 | 1.063836 |
| y | 0.147793 | 0.420677 | 0.738599 | 0.955327 | 1.129349 |
| z | -0.700906 | -0.404054 | -0.111177 | 0.000001 | 0.211202 |

- Values with absolute magnitude above 5: 0
- JSON device metadata: `Samsung Android phone`
- Physical collection device confirmed for this experiment: `Samsung Galaxy A55`

The generic device string is a documentation limitation, not a sequence-integrity failure.

## The Fixed Split Is Leakage-Safe

- Training: R01-R15, 60 samples
- Validation: R16-R20, 20 samples
- Testing: R21-R25, 20 samples
- Cross-split sample IDs: 0
- Validation/test augmentation: disabled

Manifest: `ml/data_phone/splits/sprint_2_16A_phone_split_manifest.csv`

## Python and Flutter Feature Formulas Match

- Sequence shape: `[60, 126]`
- Feature order: `mean, std, min, max, first_frame, last_frame`
- Feature matrix shape: `[100, 756]`
- Standard deviation: population standard deviation (`ddof=0`), matching Flutter's division by 60
- Maximum float32-versus-float64 feature difference: 2.980232239e-07
- Finite 756-value feature rows: 100/100

Parity fixture: `ml/data_phone/fixtures/P02_PHONE_transfer_R21_feature_parity.json`

## Decision

No invalid or suspiciously corrupted phone sample was found. The controlled experiment may proceed using the fixed split. This validation does not establish model accuracy.

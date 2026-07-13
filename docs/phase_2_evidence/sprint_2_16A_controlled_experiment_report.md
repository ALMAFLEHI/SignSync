# Sprint 2.16A Controlled Phone Dataset and Landmark Augmentation Experiment

## Technical Summary

**Recommended model: Experiment B with augmentation.** Higher untouched-phone macro F1 without a major full-test regression or more high-confidence errors. The comparison uses the same fixed real dataset, phone split, architecture, seed, optimizer, loss, early stopping rule, class weighting, and evaluation process. The 20 phone test samples and 96 validation samples remained untouched.

Sprint 2.16A is ready for controlled live A55 testing only after review and manual Flutter deployment. Sprint 2.16B remains blocked until that live test is completed.

## The Untouched Phone Test Determines the Recommendation

| Model | Phone Accuracy | Phone Macro F1 | Full Accuracy | Full Macro F1 | Threshold Pass | High-Confidence Wrong | TFLite Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline 86-class dynamic-range TFLite | 0.2500 | 0.1786 | 0.8323 | 0.8468 | 0.5000 | 5 | 587192 |
| Experiment A: 76-class without augmentation | 0.8500 | 0.8352 | 0.8820 | 0.8496 | 0.9500 | 2 | 585720 |
| Experiment B: 76-class with augmentation | 0.9500 | 0.9722 | 0.9193 | 0.9107 | 0.9500 | 0 | 585720 |

Phone metrics use active 40-intent Banking Mode filtering. Full metrics use raw top-1 predictions across the active 76-class test set. Threshold pass requires confidence at least 0.70 and a top-two gap at least 0.15.

## Pilot-Label Results Are Mixed Across the Four Signs

| Label | Baseline Acc | Exp A Acc | Exp B Acc | Baseline F1 | Exp A F1 | Exp B F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| transfer | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| document | 0.0000 | 1.0000 | 0.8000 | 0.0000 | 0.7692 | 0.8889 |
| signature | 1.0000 | 0.4000 | 1.0000 | 0.7143 | 0.5714 | 1.0000 |
| atm | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |

Detailed top-1/top-2 predictions and confidence gaps are in `docs/phase_2_evidence/sprint_2_16A_phone_test_predictions.csv`. Each model folder contains its phone confusion matrix.

## The Dataset Is Complete, Leakage-Safe, and 76-Class Only

- Historical V2 source samples: 805
- Active historical samples retained: 705
- Removed-label historical samples excluded: 100
- Real phone samples: 100
- Combined real samples: 805
- Historical/phone source counts: {'historical': 705, 'phone': 100}
- Train/validation/test: 548/96/161
- Active classes: 76 (26 alphabet, 10 digits, 40 banking intents)
- Cross-split sample duplication: 0
- Removed labels in training or output metadata: 0

Phone repetitions R01-R15 train, R16-R20 validate, and R21-R25 test. Historical assignments were preserved from the Sprint 2.12 expanded dataset.

## Feature Parity Preserves the Existing Mobile Contract

Every `[60, 126]` sequence is converted to 756 values in this order: mean, population standard deviation, minimum, maximum, first frame, and last frame. Python float32-versus-float64 parity differed by at most `2.98e-07`; all features were finite. The parity fixture preserves a real phone sequence and expected output for later Flutter testing.

## Experiment B Adds One Conservative Derivative per Training Sequence

- Original training sequences: 548
- Experiment A augmented samples: 0
- Experiment B augmented samples: 548
- Experiment B effective training rows: 1096
- Translation: x/y in [-0.0125, 0.0125]
- Scale around wrist: [0.98, 1.02]
- Rotation around wrist: [-2.5, 2.5] degrees
- Coordinate jitter sigma: 0.0015
- Temporal resampling: disabled
- Frame/landmark dropout: disabled
- Horizontal mirroring: disabled

Transforms apply only to detected non-zero hand blocks. Missing 63-value hand slots stay zero. Validation and test data are never augmented. One derivative per original training row preserves the original class proportions; balanced class weights equalize effective class contribution in both experiments.

## Training Used the Proven Sprint 2.13 Architecture

| Experiment | Effective Train | Epochs | Best Epoch | Train Acc | Val Acc | Train Loss | Val Loss | Early Stop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Experiment A: 76-class without augmentation | 548 | 53 | 33 | 0.8923 | 0.9167 | 0.3175 | 0.5830 | yes |
| Experiment B: 76-class with augmentation | 1096 | 52 | 32 | 0.9480 | 0.9271 | 0.1625 | 0.6900 | yes |

Both models use normalization, dense layers `[512, 256, 128]`, dropout 0.25, Adam at 0.001, sparse categorical cross-entropy, batch size 32, seed 42, best-checkpoint saving, and validation-accuracy early stopping with patience 20. Training-history plots and raw CSV/JSON histories are saved in each experiment folder.

## Strong Control Labels Check Historical Regression

| Control Label | Baseline | Experiment A | Experiment B |
| --- | ---: | ---: | ---: |
| A | 1.0000 | 1.0000 | 1.0000 |
| 7 | 1.0000 | 1.0000 | 1.0000 |
| deposit | 1.0000 | 1.0000 | 1.0000 |
| payment | 1.0000 | 1.0000 | 0.5000 |
| balance | 1.0000 | 1.0000 | 1.0000 |

The control subset is small and should be treated as a regression smoke test, not a robust per-class estimate.

## Both New Models Meet the 76-Class TFLite Contract

| Model | Input | Output | Input Type | Output Type | Top-1 Parity | Max Probability Difference |
| --- | --- | --- | --- | --- | ---: | ---: |
| Experiment A: 76-class without augmentation | [1, 756] | [1, 76] | float32 | float32 | 1.0000 | 0.00964367 |
| Experiment B: 76-class with augmentation | [1, 756] | [1, 76] | float32 | float32 | 1.0000 | 0.00216693 |

Both float32 and dynamic-range exports load successfully. Class order exactly matches the active V3 scope, all 40 active banking intents occur once, and no removed label appears. Flutter assets were not updated.

## Limitations and Robustness Boundaries

- Phone data comes from one participant and one Samsung Galaxy A55.
- Each phone test label has only five untouched samples, so one error changes per-label accuracy by 20 percentage points.
- The baseline has 86 outputs while new models have 76; phone comparison uses the same active 40-intent filtering, but raw full-test spaces differ.
- Device metadata inside JSON says `Samsung Android phone`; A55 identity is supplied by the controlled collection context.
- Augmentation tests only narrow spatial transforms. Temporal, dropout, and mirroring hypotheses remain untested.
- Offline improvement does not prove live-camera improvement.

## Recommended Next Step

Review the saved metrics and model artefacts, then manually deploy only the recommended model for a controlled live A55 retest. Do not replace current Flutter assets until that review decision is explicit. Keep Sprint 2.16B blocked until live testing confirms the offline result.

## Further Questions

- Does the recommended model retain its phone-test advantage during repeated live 60-frame captures?
- Are errors concentrated in pose execution, hand-slot assignment, or feature compression?
- Would a second participant/device preserve the same ranking between Experiments A and B?

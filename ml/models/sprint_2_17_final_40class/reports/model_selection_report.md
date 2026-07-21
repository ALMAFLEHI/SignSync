# Sprint 2.17 Validation-Based Model Selection

## Test-Set Protection

The locked 200-sample phone test set was not opened by training, early stopping, model comparison, confidence calibration, or winner selection.

## Comparison

| Experiment | Effective train | Validation accuracy | Validation macro F1 | High-confidence wrong | Best epoch |
| --- | ---: | ---: | ---: | ---: | ---: |
| experiment_A_phone_only | 600 | 0.9900 | 0.9899 | 1 | 46 |
| experiment_B_phone_augmentation | 1200 | 0.9850 | 0.9848 | 2 | 8 |
| experiment_C_phone_augmentation_historical | 1460 | 0.9900 | 0.9899 | 2 | 36 |

## Locked Winner

- Experiment: `experiment_A_phone_only`
- Validation macro F1: 0.9899
- Validation accuracy: 0.9900
- Selection reason: highest validation macro F1, followed by the declared tie-breakers.
- Bounded tuning triggered: False
- Test evaluation status: not run

## Confidence Recommendation

- Minimum confidence: 0.90
- Minimum top-2 margin: 0.00
- Validation coverage: 0.9600
- Accepted validation accuracy: 1.0000
- Rejection rate: 0.0400

The winner is locked and must not be altered before the one-time test evaluation.

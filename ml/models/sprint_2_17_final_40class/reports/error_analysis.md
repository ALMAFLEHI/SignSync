# Sprint 2.17 Error Analysis

## Observed Weakest Classes

- `loan`: recall 0.4000, precision 1.0000, F1 0.5714, mean top-1 confidence 0.8117
- `card`: recall 0.6000, precision 0.7500, F1 0.6667, mean top-1 confidence 0.9919
- `payment`: recall 0.6000, precision 1.0000, F1 0.7500, mean top-1 confidence 0.9376
- `document`: recall 0.8000, precision 0.8000, F1 0.8000, mean top-1 confidence 0.9220
- `help`: recall 0.8000, precision 1.0000, F1 0.8889, mean top-1 confidence 0.9985

## Observed Confusion Pairs

- `loan` -> `reset_password`: 2
- `card` -> `cash`: 1
- `card` -> `lost_card`: 1
- `document` -> `signature`: 1
- `help` -> `block_card`: 1
- `loan` -> `pin`: 1
- `payment` -> `card`: 1
- `payment` -> `document`: 1

## Interpretation Boundaries

- **Observed:** The class metrics and confusion pairs above come directly from the locked Samsung phone test set.
- **Observed:** Test prediction rows record one-hand/two-hand presence patterns where the source landmark slots allow that distinction.
- **Likely:** Similar hand shapes, motion boundaries, signer variation, or limited 15-sample-per-class real training coverage may contribute to errors, but this evaluation does not establish causality.
- **Requires further investigation:** Static-versus-dynamic intent effects and mobile live-camera behaviour require a separately approved deployment evaluation.
- **Observed:** Experiment C's historical data did not exceed Experiment A on validation macro F1 and produced one additional high-confidence validation error, so historical data was not included in the locked winner.

The locked test result was not used to retrain or revise the candidate.

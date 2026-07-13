# Sprint 2.16A Plan

## Goal

Use the approved 76-class V3 scope for future dataset preparation while preserving the historical 86-class workflow. Improve four retained weak banking labels using phone-camera landmark samples.

## Completed Setup

- Versioned the historical 50-intent/86-class V2 scope.
- Added the active 40-intent/76-class V3 scope.
- Excluded exactly 10 approved labels from future training without deleting data.
- Restricted Flutter Banking Intent Mode to the active 40 labels while retaining 86 raw model outputs for debugging.
- Revised the phone pilot to `transfer`, `document`, `signature`, and `atm`.
- Prepared validation and future mixed-dataset scripts.

## Pending Execution

Record at least 20 landmark samples per pilot label, for 80 minimum total. After validation, combine active historical samples with phone samples, prepare 756 features, train a 76-output Keras model, convert and verify TFLite, then update Flutter assets and perform a live retest.

No training, conversion, Flutter model replacement, Sprint 2.16B, or Sprint 2.17 work occurs until the samples exist.

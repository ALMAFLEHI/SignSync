# Sprint 2.16A Controlled Experiment Validation

## Status

PASS

## Verified Contract

- Original phone JSON samples: 100, hashes unchanged
- Pilot labels: transfer, document, signature, atm
- Phone split: 60 train / 20 validation / 20 untouched test
- Combined real dataset: 805 samples (705 historical + 100 phone)
- Combined split: 548 train / 96 validation / 161 test
- Active output classes: 76
- Augmentation: 548 unique derivatives, training split only
- TFLite input/output: `[1, 756]` to `[1, 76]`
- Keras/TFLite top-1 parity: 100% for both experiment variants
- Experiment A phone accuracy: 85%
- Experiment B phone accuracy: 95%

No original phone sample, historical dataset, historical model, or Flutter asset was modified by this validation.

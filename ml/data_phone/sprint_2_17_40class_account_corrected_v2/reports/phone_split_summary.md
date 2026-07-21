# Sprint 2.17 Frozen Phone Split

## Status: PASS

- Train: 600
- Validation: 200
- Locked test: 200
- Per label: 15 train / 5 validation / 5 test
- Pilot assignments preserved: True
- Cross-split sample leakage: 0
- Random reshuffling: none
- Deterministic policy: R01-R15 / R16-R20 / R21-R25

The 200-sample phone test set is locked and unavailable to training, model selection, early stopping, and confidence calibration.

## Manifest SHA-256

- `ml/models/sprint_2_17_final_40class_account_corrected_v2/manifests/phone_train_manifest.csv`: `9c3b370ee6de262772bf9b44b63c1851208834a84dfb92eb2aee5d179ff6de99`
- `ml/models/sprint_2_17_final_40class_account_corrected_v2/manifests/phone_validation_manifest.csv`: `b5c5e8ff0d0f55125238800e3f609a216a87b63bd66a7007533aa86dd7b27c84`
- `ml/models/sprint_2_17_final_40class_account_corrected_v2/manifests/phone_test_manifest.csv`: `3f67a9463d0b1a02962021104a620de7805973b9ebf30e2bc5356d1d0748d818`
- `ml/models/sprint_2_17_final_40class_account_corrected_v2/manifests/combined_split_manifest.json`: `f0a20a26c85a733c60e18d3658479661c2fbb6b2c81dee9a84a853c57ba21250`

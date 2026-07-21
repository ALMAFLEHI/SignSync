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

- `ml/models/sprint_2_17_final_40class/manifests/phone_train_manifest.csv`: `97105a02eba1140d146daa1e19286eabe45a6fe790ae09736f05222520ced1b6`
- `ml/models/sprint_2_17_final_40class/manifests/phone_validation_manifest.csv`: `ac9ecc6327ca9cef2d0ce7586b8fa8ef184ea87696d8a2ad1ae44a80035c9a06`
- `ml/models/sprint_2_17_final_40class/manifests/phone_test_manifest.csv`: `d72b28df4a6bec08b9b73cf45df596c7418aefa4a1867a72fc96475ff2d6ca9b`
- `ml/models/sprint_2_17_final_40class/manifests/combined_split_manifest.json`: `45fadddbc880e51fd18e2fa5f354764807ac593f7e014c8abe3a90de7646060f`

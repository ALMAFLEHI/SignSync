# Sprint 2.14 Flutter Validation Report

## Validation Commands

From project root:

```powershell
python ml/src/export_flutter_test_features.py
```

From `flutter_app`:

```powershell
flutter pub get
flutter analyze
flutter test
```

## Results

| Check | Result | Notes |
|---|---|---|
| Python helper syntax check | PASS | `export_flutter_test_features.py` compiled successfully. |
| Test feature export | PASS | 5 JSON feature samples exported, each with 756 values. |
| Flutter pub get | PASS | Dependencies resolved with `tflite_flutter 0.12.1` and `collection 1.19.1`. |
| Flutter analyze | PASS | No issues found. |
| Flutter test | PASS | 4 tests passed for feature engine validation and label metadata loading. |
| Android emulator run | PASS | Label metadata and TFLite model loaded successfully on Android. |
| Android manual predictions | PASS | 5 prepared test feature samples predicted correctly. |

## Validation Notes

- The local shell did not expose `python` on PATH, so validation used the bundled Python runtime to run `ml/src/export_flutter_test_features.py`.
- The Flutter prototype loads the TFLite model from app assets at runtime.
- Android emulator testing confirmed `model_dynamic_range.tflite` loads successfully.
- Mobile live camera testing was not run because it belongs to Sprint 2.15.

## Android Manual Prediction Evidence

| Sample ID | True Label | Predicted Label | Confidence | Result |
|---|---:|---:|---:|---|
| `P02_A_R01` | `A` | `A` | 94.97% | PASS |
| `P02_payment_R01` | `payment` | `payment` | 99.99% | PASS |
| `P02_document_R01` | `document` | `document` | 100.00% | PASS |
| `P02_signature_R01` | `signature` | `signature` | 100.00% | PASS |
| `P02_atm_R01` | `atm` | `atm` | 99.85% | PASS |

Normal Mode worked correctly. Number Mode filter display worked correctly.

## Evidence Screenshots

- `docs/phase_2_evidence/screenshots/Sprint2.14/01_sprint_2_14_android_model_loaded.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/02_sprint_2_14_normal_mode_A_prediction.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/03_sprint_2_14_normal_mode_payment_prediction.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/04_sprint_2_14_normal_mode_document_prediction.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/05_sprint_2_14_normal_mode_signature_prediction.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/06_sprint_2_14_normal_mode_atm_prediction.png`
- `docs/phase_2_evidence/screenshots/Sprint2.14/07_sprint_2_14_number_mode_filter_demo.png`

## Manual Run Command

```powershell
cd flutter_app
flutter run
```

Mobile live camera testing is not part of Sprint 2.14.

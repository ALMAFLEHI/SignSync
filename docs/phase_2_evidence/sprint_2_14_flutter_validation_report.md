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

## Validation Notes

- The local shell did not expose `python` on PATH, so validation used the bundled Python runtime to run `ml/src/export_flutter_test_features.py`.
- The Flutter prototype loads the TFLite model from app assets at runtime.
- Mobile live camera testing was not run because it belongs to Sprint 2.15.

## Manual Run Command

```powershell
cd flutter_app
flutter run
```

Mobile live camera testing is not part of Sprint 2.14.

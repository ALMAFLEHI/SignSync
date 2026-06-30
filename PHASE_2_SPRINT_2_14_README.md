# Phase 2, Sprint 2.14: Flutter TFLite Model Integration Prototype

## Sprint Goal

Integrate the Sprint 2.13 TensorFlow Lite model assets into the Flutter app and prove that the app can load metadata, load the model, and run offline prediction from prepared 756-feature test samples.

## What This Sprint Does

- Creates a valid Flutter project in `flutter_app`.
- Copies Sprint 2.13 TFLite model assets into Flutter assets.
- Exports fixed test feature samples for Flutter inference.
- Loads labels, label mapping, label groups, and model metadata in Flutter.
- Loads the dynamic range TFLite model by default.
- Runs local prediction on exported test feature JSON files.
- Supports Normal Mode and Number Mode output filtering.
- Displays prediction label, confidence, correctness, and top predictions.

## What This Sprint Does Not Do

- No live camera recognition.
- No MediaPipe/mobile landmark capture.
- No new video recording.
- No raw video changes.
- No model retraining.
- No model reconversion.
- No Flutter production banking workflow.
- No Sprint 2.15 work.

## Model Contract

- Input shape: `[1, 756]`
- Input dtype: `float32`
- Output shape: `[1, 86]`
- Output dtype: `float32`
- Output meaning: softmax probabilities over 86 labels

Feature order:

1. Mean of 126 landmark dimensions
2. Standard deviation of 126 landmark dimensions
3. Minimum of 126 landmark dimensions
4. Maximum of 126 landmark dimensions
5. First frame values
6. Last frame values

Total feature width: `126 x 6 = 756`.

## Asset Paths

Flutter model assets:

- `flutter_app/assets/models/model_float32.tflite`
- `flutter_app/assets/models/model_dynamic_range.tflite`

Flutter metadata assets:

- `flutter_app/assets/metadata/labels.txt`
- `flutter_app/assets/metadata/label_mapping.json`
- `flutter_app/assets/metadata/label_groups.json`
- `flutter_app/assets/metadata/tflite_model_metadata.json`

Flutter test feature assets:

- `flutter_app/assets/test_features/P02_A_R01.json`
- `flutter_app/assets/test_features/P02_payment_R01.json`
- `flutter_app/assets/test_features/P02_document_R01.json`
- `flutter_app/assets/test_features/P02_signature_R01.json`
- `flutter_app/assets/test_features/P02_atm_R01.json`

## Commands

From the project root:

```powershell
python ml/src/export_flutter_test_features.py
```

From the Flutter app folder:

```powershell
cd flutter_app
flutter pub get
flutter analyze
flutter test
flutter run
```

## Evidence Screenshots

- `01_sprint_2_14_flutter_pub_get.png`
- `02_sprint_2_14_flutter_analyze_passed.png`
- `03_sprint_2_14_test_features_exported.png`
- `04_sprint_2_14_app_home_model_loaded.png`
- `05_sprint_2_14_normal_mode_A_prediction.png`
- `06_sprint_2_14_normal_mode_payment_prediction.png`
- `07_sprint_2_14_normal_mode_document_prediction.png`
- `08_sprint_2_14_normal_mode_signature_prediction.png`
- `09_sprint_2_14_normal_mode_atm_prediction.png`
- `10_sprint_2_14_number_mode_filter_demo.png`

## Acceptance Criteria

- Flutter project exists and opens.
- Sprint 2.13 model assets are copied into Flutter assets.
- `pubspec.yaml` includes model, metadata, and test feature assets.
- `flutter pub get` passes.
- `flutter analyze` passes or has only justified non-blocking warnings.
- App loads label metadata successfully.
- App loads TFLite model successfully.
- App can run prediction on exported test feature samples.
- Normal Mode and Number Mode filtering are implemented.
- No live camera recognition is falsely claimed.
- Sprint 2.15 is not started.

## Next Sprint

Sprint 2.15 should handle live camera capture, mobile MediaPipe landmark collection, feature computation from live landmarks, and mobile testing preparation.

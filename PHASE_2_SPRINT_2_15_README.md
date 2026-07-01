# Phase 2, Sprint 2.15: Live Camera + Mobile MediaPipe Landmark Capture Prototype

## Sprint Status

Completed for live pipeline implementation and limited real-phone validation.

Sprint 2.15 does not claim perfect accuracy. Only a small representative set of labels was tested on a Samsung Android phone, and some weak/confusing labels were discovered.

## What This Sprint Adds

Sprint 2.15 adds the first Android live-camera prototype for SignSync. The app can open a live camera page, request camera permission, use Android CameraX and MediaPipe HandLandmarker, stream landmark frames to Flutter, collect 60 valid frames, compute a 756-feature vector, and pass it to the existing Sprint 2.13 TFLite classifier.

## Recognition Modes

The app now has three final recognition modes:

- Alphabet Mode: A-Z only
- Number Mode: 0-9 only
- Banking Intent Mode: banking intent labels only

Banking Intent Mode blocks alphabet labels such as `Z` from being shown as the final banking prediction. Raw top predictions remain available for debugging.

## Main Files

- `flutter_app/lib/ui/live_camera_page.dart`
- `flutter_app/lib/services/live_landmark_service.dart`
- `flutter_app/lib/services/live_recognition_service.dart`
- `flutter_app/lib/services/landmark_buffer.dart`
- `flutter_app/lib/models/live_landmark_frame.dart`
- `flutter_app/lib/models/live_prediction_session.dart`
- `flutter_app/lib/models/prediction_source.dart`
- `flutter_app/android/app/src/main/kotlin/com/example/flutter_app/MainActivity.kt`
- `flutter_app/android/app/src/main/AndroidManifest.xml`
- `flutter_app/android/app/build.gradle.kts`

## Model And Feature Contract

- live buffer: 60 frames
- frame width: 126 values
- feature vector: 756 values
- feature order: mean, std, min, max, first frame, last frame
- model input shape: `[1, 756]`
- model output shape: `[1, 86]`

## Phone Test Summary

- `A`: correct, 77.92% confidence
- `7`: correct, 60.14% confidence
- `deposit`: correct, 91.75% confidence
- `payment`: correct, 99.44% confidence, but needed retry
- `balance`: correct, 81.35% confidence
- `transfer`: failed 3 attempts, often predicted `Z`
- `address_change`: mixed result, correct once and failed other attempts
- `document`: failed
- `signature`: mixed result, correct once and failed other attempts
- `atm`: failed

Weak labels identified:

- `transfer`
- `address_change`
- `document`
- `signature`
- `atm`

## MediaPipe Asset Paths

- Flutter asset: `flutter_app/assets/mediapipe/hand_landmarker.task`
- Android asset: `flutter_app/android/app/src/main/assets/hand_landmarker.task`

The original file `ml/models/hand_landmarker.task` was not modified.

## How To Validate

From the project root:

```powershell
cd flutter_app
flutter pub get
flutter analyze
flutter test
```

Optional Android run when a phone or emulator is connected:

```powershell
flutter devices
flutter run -d <android_device_id>
```

## Current Validation Result

Passed:

- `flutter pub get`
- `flutter analyze`
- `flutter test`
- Android phone live camera test
- live landmark capture
- 60-frame buffer
- 756-feature generation
- TFLite live prediction

## Sprint Boundary

This sprint did not retrain the model, reconvert TFLite files, collect a new formal dataset, modify raw videos, add cloud processing, test all banking intents, claim 100% accuracy, or start Sprint 2.16.

## Next Sprint Note Only

Sprint 2.16 should focus on phone-camera dataset expansion and accuracy improvement:

- record 20 phone-camera samples for `transfer`, `address_change`, `document`, `signature`, and `atm`
- retrain and export updated TFLite
- test the live demo again
- if improvement is clear, continue phone-camera samples for remaining banking intents

# Sprint 2.15 MediaPipe Android Setup Report

## Approach

Sprint 2.15 uses a minimal Android native bridge. The Flutter app owns the UI, mode filtering, buffering, feature computation, and TFLite prediction. Android native code owns CameraX preview and MediaPipe HandLandmarker processing.

## Android Dependencies

Added in `flutter_app/android/app/build.gradle.kts`:

- `androidx.core:core-ktx:1.16.0`
- `androidx.camera:camera-core:1.6.1`
- `androidx.camera:camera-camera2:1.6.1`
- `androidx.camera:camera-lifecycle:1.6.1`
- `androidx.camera:camera-view:1.6.1`
- `com.google.mediapipe:tasks-vision:0.10.35`

MediaPipe Tasks Vision version `0.10.35` was chosen to align with the Python MediaPipe setup used in earlier Sprint 2 work.

## MediaPipe Task Asset

Original asset:

- `ml/models/hand_landmarker.task`

Copied Flutter asset:

- `flutter_app/assets/mediapipe/hand_landmarker.task`

Copied Android native asset:

- `flutter_app/android/app/src/main/assets/hand_landmarker.task`

The original model asset under `ml/models` was not moved or modified.

## Native Bridge

Android bridge file:

- `flutter_app/android/app/src/main/kotlin/com/example/flutter_app/MainActivity.kt`

Bridge APIs:

- Platform view: `signsync/live_camera_view`
- Method channel: `signsync/live_landmarks`
- Methods: `startCamera`, `stopCamera`, `startCapture`, `resetCapture`
- Events: `cameraStarted`, `cameraStopped`, `cameraError`, `mediapipeError`, `liveFrame`

## Camera Permission

Added in `flutter_app/android/app/src/main/AndroidManifest.xml`:

- `android.permission.CAMERA`
- optional camera hardware feature declaration

Flutter requests runtime camera permission using `permission_handler`.

## Hand Ordering

The Android bridge returns a fixed 126-value frame:

- values `0-62`: left hand
- values `63-125`: right hand

MediaPipe handedness is used first. If handedness is missing or ambiguous, detections are sorted by average normalized x-coordinate, matching the earlier Python fallback strategy as closely as possible.

## Phone Validation

Confirmed on a Samsung Android phone:

- camera opens
- MediaPipe HandLandmarker runs
- live landmarks are captured
- 60 valid frames can be collected
- live prediction can run from the generated 756-feature vector

## Verification

Completed:

- `flutter pub get` passed.
- `flutter analyze` passed.
- `flutter test` passed.
- `flutter build apk --debug` passed.

## Limitation

The Android MediaPipe setup works for the live prototype, but Sprint 2.15 is not an accuracy-improvement sprint. Some labels were weak in live testing and require Sprint 2.16 phone-camera data expansion and retraining.

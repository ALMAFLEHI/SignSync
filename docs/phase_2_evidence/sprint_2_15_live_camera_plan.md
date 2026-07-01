# Sprint 2.15 Live Camera Plan

## Project

SignSync - A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions.

## Sprint Goal

Phase 2, Sprint 2.15 adds the first Android live-camera recognition prototype. The goal is to connect Android camera frames to MediaPipe hand landmarks, collect 60 valid landmark frames, compute the same 756 statistical features used by the Sprint 2.13 TFLite model, and run local Flutter TFLite inference.

## Scope

- Add Android camera permission and camera preview.
- Add MediaPipe Tasks Vision HandLandmarker integration on Android.
- Stream fixed-width landmark frames from Android native code to Flutter.
- Use 126 values per valid frame: 2 hands x 21 landmarks x 3 coordinates.
- Collect 60 valid frames in a Flutter buffer.
- Compute 756 features in the existing Flutter feature format: mean, std, min, max, first frame, last frame.
- Reuse the existing Sprint 2.14 TFLite classifier and metadata assets.
- Finalize Alphabet Mode, Number Mode, and Banking Intent Mode filtering.
- Show runtime metrics for capture, feature computation, and inference.

## Out Of Scope

- No model retraining.
- No TFLite reconversion.
- No raw video changes.
- No new formal dataset collection.
- No cloud or server processing.
- No banking backend integration.
- No Sprint 2.16 work.

## Android Target

Android/mobile remains the primary target. Windows desktop remains a development target only and is not used for live MediaPipe camera recognition.

## Expected Pipeline

1. User opens the live camera page.
2. App requests Android camera permission.
3. CameraX opens the preview.
4. MediaPipe HandLandmarker processes camera frames locally.
5. Android bridge sends live landmark frames to Flutter.
6. Flutter accepts only valid 126-value frames.
7. Flutter collects 60 valid frames.
8. Feature engine computes 756 features.
9. Existing TFLite classifier runs offline inference.
10. UI displays prediction, confidence, top predictions, mode, and runtime metrics.

## Validation Status

Implementation, analysis, tests, Android debug APK build, and limited Samsung Android phone validation passed. Sprint 2.15 proves the live pipeline but does not claim perfect accuracy.

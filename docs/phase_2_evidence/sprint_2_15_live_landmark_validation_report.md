# Sprint 2.15 Live Landmark Validation Report

## Implementation Validation

The live landmark implementation is present in the Flutter app and Android native bridge.

Expected live frame contract:

- frame count: 60 valid frames
- frame width: 126 values
- per hand: 21 landmarks x 3 coordinates
- missing hand: zero-filled slot
- no hand detected: frame is not added to the buffer

## Android Phone Validation

A real Samsung Android phone was connected and tested.

Confirmed on phone:

- camera opens
- MediaPipe live landmark capture works
- valid hand landmark frames are captured
- 60-frame capture completes
- captured frames produce a 756-feature vector
- the existing TFLite model runs live prediction
- the app remains on-device with no video upload

## Recognition Mode Validation

The app now provides three explicit recognition modes:

- Alphabet Mode: A-Z only
- Number Mode: 0-9 only
- Banking Intent Mode: banking intent labels only

Banking Intent Mode filters out alphabet labels such as `Z`, so they cannot be displayed as the final banking prediction even if the raw model output gives them a high score.

## Build Validation

Android debug APK build passed:

```powershell
flutter build apk --debug
```

Output:

```text
Built build\app\outputs\flutter-apk\app-debug.apk
```

## Flutter Validation

Passed:

```powershell
flutter pub get
flutter analyze
flutter test
```

## Limitation

Sprint 2.15 validates the live camera to MediaPipe to feature vector to TFLite pipeline. It does not claim perfect recognition accuracy. Only a small representative set of labels was tested on the phone, and some labels were weak or confusing.

Accuracy improvement is moved to Sprint 2.16.

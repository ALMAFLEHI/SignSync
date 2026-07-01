# Sprint 2.15 Live Camera Checklist

## Completed

- [x] Inspected Sprint 2.13 Python feature utilities.
- [x] Confirmed feature order: mean, std, min, max, first frame, last frame.
- [x] Confirmed live input contract: 60 frames x 126 values.
- [x] Copied `hand_landmarker.task` into Flutter assets.
- [x] Copied `hand_landmarker.task` into Android assets.
- [x] Added Android camera permission.
- [x] Added CameraX dependencies.
- [x] Added MediaPipe Tasks Vision dependency.
- [x] Added Android native CameraX preview bridge.
- [x] Added Android native MediaPipe HandLandmarker bridge.
- [x] Added fixed left/right hand landmark frame layout.
- [x] Added Flutter live landmark service.
- [x] Added Flutter 60-frame landmark buffer.
- [x] Added live recognition service using the existing feature engine.
- [x] Added live camera UI page.
- [x] Added Alphabet Mode, Number Mode, and Banking Intent Mode.
- [x] Updated filtering so each mode only shows predictions from its own label group.
- [x] Preserved Sprint 2.14 offline test-feature inference.
- [x] Added landmark buffer tests.
- [x] Added mode-filtering tests.
- [x] `flutter pub get` passed.
- [x] `flutter analyze` passed.
- [x] `flutter test` passed.
- [x] Android debug APK build passed.

## Real Phone Validation

- [x] Samsung Android phone connected and tested.
- [x] Camera opened on phone.
- [x] MediaPipe live landmark capture worked.
- [x] 60-frame capture worked.
- [x] 756-feature vector generation worked.
- [x] TFLite live prediction worked.
- [x] Normal debug/top prediction information remained available.

## Limited Recognition Results

- [x] `A` predicted correctly with 77.92% confidence.
- [x] `7` predicted correctly with 60.14% confidence.
- [x] `deposit` predicted correctly with 91.75% confidence.
- [x] `payment` predicted correctly with 99.44% confidence after retry.
- [x] `balance` predicted correctly with 81.35% confidence.
- [x] Weak/confusing labels identified: `transfer`, `address_change`, `document`, `signature`, `atm`.

## Accuracy Limitation

- [x] Sprint 2.15 proves the live pipeline, not perfect accuracy.
- [x] Only a small representative set of labels was tested.
- [x] Full banking intent testing was not completed in this sprint.
- [x] High-confidence wrong predictions were observed.
- [x] Accuracy improvement is deferred to Sprint 2.16.

## Next Sprint Note Only

Sprint 2.16 should focus on phone-camera dataset expansion and accuracy improvement. Suggested first step: record 20 phone-camera samples for the weak labels `transfer`, `address_change`, `document`, `signature`, and `atm`, then retrain/export TFLite and test the live demo again.

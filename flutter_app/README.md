# SignSync Flutter Prototype

Flutter prototype for Phase 2, Sprint 2.14 of SignSync.

This app loads the Sprint 2.13 TensorFlow Lite model assets, validates label metadata, and runs offline inference from prepared 756-feature test samples.

## Sprint Boundary

- This sprint uses prepared test feature JSON files.
- The app does not perform live camera recognition yet.
- MediaPipe landmark capture and mobile testing belong to Sprint 2.15.

## Commands

```powershell
flutter pub get
flutter analyze
flutter test
flutter run
```

## Windows Desktop Runtime

For Windows desktop only, `tflite_flutter` needs:

```text
blobs/libtensorflowlite_c-win.dll
```

When this DLL exists, `windows/CMakeLists.txt` copies it into the Windows build output. Without it, the app still opens and shows a clear runtime message. Android/mobile remains the main target for on-device inference.

# Sprint 2.14 Windows Runtime Fix Report

## Problem

Running the Flutter prototype on Windows desktop failed during TFLite setup with:

```text
Invalid argument(s): Failed to load dynamic library:
build\windows\x64\runner\Debug\blobs\libtensorflowlite_c-win.dll
The specified module could not be found. (error code: 126)
```

## Cause

The Sprint 2.14 Flutter app used `tflite_flutter`, which loads the TensorFlow Lite C runtime on Windows from:

```text
<Windows executable folder>/blobs/libtensorflowlite_c-win.dll
```

The Flutter model files were present, but the native Windows TensorFlow Lite C runtime DLL was not bundled. This is a Windows desktop runtime dependency issue, not a model conversion, model training, label, or dataset issue.

## Fix Applied

1. Added `flutter_app/blobs/README.md` to document the required Windows runtime DLL location.
2. Updated `flutter_app/windows/CMakeLists.txt` with a Windows install rule for `libtensorflowlite_c-win.dll`.
3. Kept the CMake rule conditional so the Windows app can still build and open when the optional desktop DLL has not been provided.
4. Updated `TfliteSignClassifier` to check for the DLL before calling `Interpreter.fromAsset` on Windows.
5. Updated the app initialization flow so label metadata can still load and the UI shows a clear Windows runtime message instead of exposing the raw FFI crash.

## Runtime DLL Requirement

Expected local file:

```text
flutter_app/blobs/libtensorflowlite_c-win.dll
```

Expected runtime copy path after Windows build:

```text
flutter_app/build/windows/x64/runner/Debug/blobs/libtensorflowlite_c-win.dll
```

If a valid DLL is present, CMake copies it automatically during `flutter run -d windows`.

If the DLL is missing, the app now opens and reports the missing Windows runtime clearly. Android/mobile remains the main Sprint 2.14 target.

## Checks Run

```powershell
flutter pub get
flutter analyze
flutter test
flutter run -d windows
```

## Results

| Check | Result | Notes |
|---|---|---|
| `flutter pub get` | PASS | Dependencies resolved. |
| `flutter analyze` | PASS | No issues found. |
| `flutter test` | PASS | 4 tests passed. |
| `flutter run -d windows` | PASS with runtime notice | Windows app built and opened. Raw DLL crash no longer occurs. |

## Windows Model Loading Status

Windows desktop model loading is ready in code but still requires a valid TensorFlow Lite C Windows runtime DLL at:

```text
flutter_app/blobs/libtensorflowlite_c-win.dll
```

Because no verified compatible DLL was available locally, no arbitrary DLL was copied into the project. The app now handles this safely and clearly.

## Sprint Boundary

This fix remains inside Sprint 2.14. It does not add live camera recognition, MediaPipe mobile capture, new recordings, model training, model conversion, or Sprint 2.15 work.

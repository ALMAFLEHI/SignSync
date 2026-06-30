# Windows TensorFlow Lite Runtime

This folder is used by the Windows desktop build of `tflite_flutter`.

`tflite_flutter` loads the native TensorFlow Lite C runtime from:

```text
<windows executable folder>/blobs/libtensorflowlite_c-win.dll
```

For Sprint 2.14, the app keeps Android/mobile as the main target. Windows desktop is a prototype validation target and needs this runtime DLL available locally before `flutter run -d windows` can load the TFLite model.

Expected file:

```text
flutter_app/blobs/libtensorflowlite_c-win.dll
```

The Windows CMake setup copies this file into the build output during `flutter run -d windows`.

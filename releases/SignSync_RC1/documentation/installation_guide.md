# SignSync Installation Guide

## Academic Demonstration APK

1. Use `releases/SignSync_RC1/app/app-release.apk` for release-mode academic demonstration, or `app-debug.apk` for development diagnostics.
2. Verify the APK against `releases/SignSync_RC1/app/APK_SHA256SUMS.txt`.
3. On an authorized Android device, install without clearing app storage:

```powershell
adb install -r releases/SignSync_RC1/app/app-release.apk
```

4. Launch SignSync and grant camera permission when live recognition is required.

## Requirements

- Android SDK 24 or newer.
- Camera access for live capture.
- Supported native ABIs: arm64-v8a, armeabi-v7a, x86_64.

The release-mode APK is signed with the Android debug certificate for academic demonstration. It is not a Play Store production-signed release. Do not uninstall or clear storage when preserving application-specific research samples.

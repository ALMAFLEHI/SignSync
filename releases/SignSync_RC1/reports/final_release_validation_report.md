# Sprint 2.21 Release Validation

Status: **PASS - SignSync RC1 academic release candidate**

## Acceptance

- Unresolved blockers: 0.
- Unresolved major defects: 0.
- Resolved major release findings: 2.
- Flutter analyze: PASS, no issues.
- Flutter tests: PASS, 108/108.
- Current authoritative Python tests: PASS, 92/92 after final packaging.
- Sprint 2.21 focused tests: PASS, 14/14.
- Debug APK: PASS, 216,851,907 bytes, SHA-256 `2F14ABCA6FB4CB0258A2AD87B26DC98416E9A5C04BF598C52851D818726AD75F`.
- Release-mode APK: PASS, 117,200,909 bytes, SHA-256 `65C7E9083A295AB1722DBD6CC2C8DC8003F4E758857318DB6AE668C6AA3C75BE`.
- Release signature: valid APK Signature Scheme v2, Android debug certificate; academic use only.
- Package: `com.example.flutter_app`, version `1.0.0` (`1`), min SDK 24, target SDK 36.
- ABIs: arm64-v8a, armeabi-v7a, x86_64.
- A55 validation: `adb install -r` succeeded; package version 1 launched on SM-A556E, Android 16. No recognition trial was required.

## Frozen Integrity

- Model: float32 `[1,756] -> [1,40]`.
- Confidence threshold: 0.80; minimum margin: 0.00.
- Dataset: 1,000 samples, 40 intents, 25 each.
- Query map: 40 intents and 160 local requests.
- Locked held-out result: accuracy 0.9550, macro F1 0.9542, 191/200 correct.
- Account-to-savings and savings-to-account confusion: 0.
- Every protected hash passed exactly.

## Release Corrections


| ID | Severity | Problem | Root cause | Correction | Regression evidence | Before / after |
|---|---|---|---|---|---|---|
| S221-F001 | Major, resolved | Final corrected Flutter TFLite assets were ignored, so a clean source archive could omit runtime models. | A global `*.tflite` rule only exempted legacy names. | Added exact exceptions for the two protected corrected-v2 assets. | Sprint 2.21 Flutter and Python release tests. | Ignored final assets / explicitly distributable final assets. |
| S221-F002 | Major, resolved | Transitive libraries added Internet, network-state, storage, and phone-state permissions unused by SignSync. | Media3, Google Data Transport, and LiteRT GPU manifests contributed permissions. | Added manifest-merger removals; retained camera and Android's app-scoped receiver permission. | Built merged manifests, `aapt dump badging`, tests. | Release advertised unused access / release has no Internet, network-state, storage, or phone-state permission. |


## Build Note

The first release build reported a Kotlin incremental-cache cross-drive warning involving the Pub cache on `C:` and project build cache on `D:`. Gradle completed successfully, and the final release rebuild completed successfully in 149.2 seconds. No production source workaround or dependency change was required.

## Commands


```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze --no-pub
flutter test --no-pub
python -m py_compile ml/src/validate_sprint_2_21_release_candidate.py ml/tests/test_sprint_2_21_release_candidate.py
python ml/src/validate_sprint_2_21_release_candidate.py --core-only
python -m unittest <84 current authoritative Sprint 2.17-2.20 tests>
flutter build apk --debug --no-pub
flutter build apk --release --no-pub
adb install -r flutter_app/build/app/outputs/flutter-apk/app-release.apk
python ml/src/validate_sprint_2_21_release_candidate.py
git diff --check
```


No retraining, TFLite reconversion, dataset edit, query redesign, threshold change, new feature, cloud service, new participant test, commit, push, or later sprint occurred.

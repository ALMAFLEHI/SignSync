# Sprint 2.21 Privacy and Offline Audit

Status: **PASS**. Scope: active Dart code, native Android code, manifests, resolved dependencies, local stores, logging, and built release metadata.

## Findings

- Recognition runs locally through CameraX, MediaPipe Hands, feature computation, and TensorFlow Lite.
- No production Dart or native recognition API call was found.
- Camera frames, landmarks, and feature vectors are not uploaded.
- Normal banking interaction state is held in memory and cleared by Try Again, Cancel, Start Over, New Interaction, Clear Session, and restart behavior.
- Account/card values are masked where configured; customer request data is not written as interaction history.
- Theme preference may persist through SharedPreferences.
- Developer-only technical-evaluation metadata and phone-sample tools remain separated from the normal user workflow.
- No Firebase, remote database, analytics, advertising, crash-reporting, or telemetry SDK was added.
- The application does not authenticate users, connect to bank systems, authorize or execute transactions, or replace bank staff.

## Permission Audit

| Permission | Release state | Reason |
|---|---|---|
| `android.permission.CAMERA` | Required | Live hand-landmark capture. |
| `com.example.flutter_app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Automatically included | AndroidX app-scoped receiver protection; not a sensitive platform capability. |
| `android.permission.INTERNET` | Removed from release | Transitive Google Data Transport declaration; unused by SignSync. Debug retains Flutter development access. |
| `android.permission.ACCESS_NETWORK_STATE` | Removed | Transitive Media3 declaration; unused. |
| Storage and phone-state permissions | Removed | Legacy/transitive LiteRT declarations; unused. |

The audit does not infer privacy solely from the absence of one permission. It combines source, dependency, manifest, storage, logging, test, and APK inspection. The release APK declares no Internet permission.

# SignSync Developer Handover

## Frozen Production Contract

- Android package: `com.example.flutter_app`; iOS bundle: `com.example.flutterApp`.
- App version: `1.0.0+1`.
- Active scope: 40 banking intents in `ml/models/sprint_2_17_final_40class_account_corrected_v2/metadata/labels_40.json`.
- Input/output: float32 `[1,756]` to `[1,40]`.
- Temporal/landmark shape: 60 frames x 126 values.
- Confidence threshold/margin: 0.80 / 0.00.
- Local query asset: `flutter_app/assets/content/banking_queries.json`.

## Validation

Run `python ml/src/validate_sprint_2_21_release_candidate.py` from the project root. The validator fails on a protected hash, dataset distribution, model/query contract, release manifest, checksum, document, figure, or archive mismatch.

Flutter commands run from `flutter_app`: `flutter pub get`, Dart format check, `flutter analyze`, `flutter test`, and debug/release APK builds.

## Preservation

Do not retrain or reconvert under the Sprint 2.21 identity. Do not reorder labels, edit the threshold, redesign the frozen queries, restore invalid account samples, overwrite the canonical dataset backup, or change package identifiers. The release-mode APK is academic debug-signed and needs a separately governed signing process for any future store distribution.

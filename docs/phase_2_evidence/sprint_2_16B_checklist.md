# Sprint 2.16B Checklist

## Workflow Preparation Completed

- [x] Preserved all existing 100 Sprint 2.16A phone JSON samples.
- [x] Added exact versioned 36-label Python and Dart constants.
- [x] Verified 36 remaining plus 4 pilot equals the active V3 40 intents.
- [x] Excluded pilot, removed, alphabet, and digit labels from new collection.
- [x] Set the target to 25 samples per label and 900 new samples.
- [x] Updated the Android collection page for searchable 36-label progress.
- [x] Added first-missing repetition selection and restart-safe disk counters.
- [x] Added capture blocking after 25/25 and non-overwrite checks.
- [x] Preserved the 60x126 left/right hand-slot contract.
- [x] Added safe, confirmed deletion of only the selected label's last sample.
- [x] Protected Sprint 2.16A pilot files from collection and deletion.
- [x] Added the partial-progress PC checker and MD/CSV/JSON evidence.
- [x] Documented hash-safe ADB pull and post-PASS backup workflow.
- [x] Added scope, storage, repetition, correction, and hand-slot tests.

## Manual Collection Pending

- [ ] Record 25 fresh A55 samples for each of the 36 remaining labels.
- [ ] Confirm 900/900 new samples in the collection page.
- [ ] Pull the Android folder with the documented staging workflow.
- [ ] Run the Sprint 2.16B checker after each pull.
- [ ] Resolve any invalid, duplicate, or missing repetition finding.
- [ ] Reach 1,000/1,000 valid banking phone samples.
- [ ] Create `sprint_2_16B_banking_phone_samples_1000_backup.zip` only after PASS.
- [ ] Review final evidence before any future split or training work.

## Scope Guards

- [x] No existing phone, laptop, video, landmark, dataset, model, or evidence file deleted.
- [x] No Android application uninstall or storage clearing performed.
- [x] No automatic multi-repetition recording added.
- [x] No model retraining or augmentation performed.
- [x] No Experiment B Flutter model asset replaced.
- [x] No final 1,000-sample backup fabricated early.
- [x] No commit or push performed.
- [x] Sprint 2.16C not started.

## Automated Validation

- [x] Python syntax checks passed for the Sprint 2.16B scripts.
- [x] Active V3 scope check passed: 26 alphabet, 10 digits, 40 banking intents, 76 total labels.
- [x] Sprint 2.16A pilot integrity checks passed for all 100 protected samples.
- [x] Sprint 2.16B partial-progress checker returned the expected `PENDING` status at 0/900 new samples, with zero invalid or duplicate samples.
- [x] `flutter pub get` completed successfully.
- [x] `flutter analyze` passed with no issues.
- [x] `flutter test` passed all 39 tests.
- [x] Android debug APK built successfully at `flutter_app/build/app/outputs/flutter-apk/app-debug.apk`.
- [x] The APK contains both TFLite models and all configured metadata assets.

# Sprint 2.16A Checklist

## Completed

- [x] 40-intent scope approved.
- [x] 10 removed labels documented.
- [x] Historical data and 86-class model assets preserved.
- [x] 76-class future scope configured.
- [x] Flutter active Banking Intent Mode filtering updated.
- [x] Raw 86-class predictions preserved for debugging.
- [x] Phone pilot revised to four labels.
- [x] Collection UI revised.
- [x] Python validation and dataset scripts revised.
- [x] Tests passed.
- [x] Recorded 25 `transfer` phone landmark samples.
- [x] Recorded 25 `document` phone landmark samples.
- [x] Recorded 25 `signature` phone landmark samples.
- [x] Recorded 25 `atm` phone landmark samples.
- [x] Pulled and independently validated 100 phone samples.
- [x] Created the leakage-safe 60/20/20 phone split.
- [x] Created the 805-sample mixed real 76-class dataset.
- [x] Evaluated the unchanged historical 86-class baseline.
- [x] Trained Experiment A without augmentation.
- [x] Trained Experiment B with conservative training-only augmentation.
- [x] Exported and verified both 76-class TFLite model variants.
- [x] Produced controlled comparison and validation reports.
- [x] Reviewed and approved Experiment B as the deployment candidate.
- [x] Backed up the previous 86-class Flutter model and metadata.
- [x] Deployed the matched Experiment B model and 76-class metadata.
- [x] Verified Alphabet 26 / Number 10 / Banking Intent 40 mode filtering.
- [x] Added model contract, feature parity, zero-slot, fixture, and ambiguity tests.
- [x] Built the Android debug APK successfully.
- [x] Created the controlled live A55 test plan and empty results CSV.

## Pending

- [ ] Perform the controlled live Samsung Galaxy A55 retest.
- [ ] Review all 65 fresh live attempts and decide whether Sprint 2.16A passes.

## Scope Guard

- [x] No historical files deleted or overwritten.
- [x] No original phone JSON files modified.
- [x] No fake phone samples generated.
- [x] Synthetic derivatives were limited to the training split.
- [x] Existing Flutter model and metadata assets were not replaced.
- [x] Investigation Report files not edited.
- [x] No commit or push performed.
- [x] Sprint 2.16B and Sprint 2.17 not started.

Sprint 2.16A remains open until the 65-attempt live A55 retest is completed and reviewed.

# Sprint 2.9 Full Landmark Extraction Plan

## Goal
Extract two-hand MediaPipe Tasks landmarks from the current full SignSync raw video dataset without changing the raw videos.

## Input Scope
- Current scoped labels: 56.
- Trial labels: 11 labels x 5 repetitions = 55 videos.
- Full collection labels: 45 labels x 10 repetitions = 450 videos.
- Expected raw videos: 505.
- Participant: P02.
- Replacement rule: `payment` is expected and `receipt` is excluded.

## Landmark Output Format
- Detector: local MediaPipe Tasks HandLandmarker model at `ml/models/hand_landmarker.task`.
- Maximum hands: 2.
- Landmarks per hand: 21.
- Coordinates per landmark: x, y, z.
- Landmark row dimension: 126.
- Hand-mask row dimension: 2.
- Missing hands: zero-filled landmark slots with a zero mask value.
- Output paths: `ml/data_processed/landmarks/[label]/`.

## Workflow
1. Run syntax checks.
2. Run the full extraction dry-run and review the expected 505 samples.
3. Run normal extraction only after confirmation.
4. Verify all raw video, landmark, mask, and metadata records.
5. Preview representative samples such as `A`, `payment`, and `7`.

## Safety Boundaries
- Raw videos are read only and never modified or deleted.
- Existing complete landmark and mask pairs are skipped unless `--overwrite` is supplied.
- The extraction workflow does not retrain a model, prepare an `.npz` dataset, create TFLite files, create Flutter files, or start Sprint 2.10.

## Acceptance Criteria
- [x] Full-dataset extraction configuration exists.
- [x] Tasks API full extractor exists.
- [x] Full landmark verifier exists.
- [x] Processed landmark preview helper exists.
- [x] Sprint 2.9 README and checklist exist.
- [ ] Full extraction completed for 505 videos.
- [ ] Full landmark verification passed.
- [ ] Evidence screenshots saved.

# Sprint 2.4 MediaPipe Landmark Plan

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.4: MediaPipe Landmark Extraction on Trial Dataset

## Sprint Goal
Confirm that MediaPipe can detect the hand gestures in the Sprint 2.3 trial videos before dataset cleaning or model training begins.

## Input Dataset
- Source videos: `ml/data_raw/videos/[label]/`
- Participant: `P02`
- Trial labels: `A`, `B`, `C`, `0`, `1`, `2`, `deposit`, `withdraw`, `balance`, `help`, `confirm`
- Repetitions: 5 per label
- Expected videos: 55

## Expected Outputs
- Landmark arrays under `ml/data_processed/landmarks/[label]/`
- Detection masks under `ml/data_processed/landmarks/[label]/`
- Extraction CSV report
- Extraction Markdown report
- Updated `ml/metadata.csv`

## MediaPipe Purpose
MediaPipe Hands detects up to two hands per video frame and provides normalized hand landmark coordinates. This sprint checks whether those detections are reliable enough for future dataset cleaning and model training. The workflow supports both one-hand and two-hand signs.

## Landmark Format
Each frame stores two hand slots. Each hand has 21 landmarks, and each landmark has `x`, `y`, and `z` values.

```text
2 hands x 21 landmarks x 3 values = 126 values per frame
```

Each saved landmark file should have this shape:

```text
number_of_frames x 126
```

The fixed landmark layout is:

- Columns `0-62`: left hand landmarks
- Columns `63-125`: right hand landmarks

Each detection mask has this shape:

```text
number_of_frames x 2
```

The mask uses:

- `mask[frame, 0] = 1` when the left hand is detected
- `mask[frame, 1] = 1` when the right hand is detected

## Detection Rate Rule
Sprint 2.4 uses any-hand detection rate for pass/fail, because some labels naturally use one hand while banking-intent signs may use two hands. A sample passes when:

```text
any_hand_detected_frames / total_frames >= 0.80
```

The extraction report also records two-hand detection rate for quality review.

Samples below the any-hand threshold of `0.80` are marked as `landmark_detection_failed`.

## Metadata Update Rule
Before updating metadata, a backup is saved to:

```text
docs/phase_2_evidence/metadata_backup_before_sprint_2_4_landmarks.csv
```

Successful samples are updated with:

- `landmark_path`: relative path to the landmark `.npy` file
- `status`: `landmarks_extracted`

Failed detection samples are updated with:

- `status`: `landmark_detection_failed`

## Acceptance Criteria
- [ ] MediaPipe setup check passes.
- [ ] 55 trial videos are processed.
- [ ] Two-hand landmark `.npy` files are generated with shape `frames x 126`.
- [ ] Two-column mask `.npy` files are generated with shape `frames x 2`.
- [ ] Extraction report is generated.
- [ ] Metadata is updated.
- [ ] Verification script passes.
- [ ] At least one visual landmark preview is checked.
- [ ] No model training is created.
- [ ] No Flutter integration is created.

## What This Sprint Does Not Include
- Model training
- TensorFlow Lite conversion
- Flutter integration
- Full dataset collection
- Dataset cleaning decisions beyond detection reporting

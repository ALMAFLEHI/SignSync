# Phase 2 Sprint 2.9 README

## Sprint Goal
Sprint 2.9 extracts two-hand MediaPipe Tasks landmarks from the current full SignSync raw video dataset and verifies the processed outputs.

## What This Sprint Does
- Reads the 505 expected P02 raw videos.
- Uses the local `ml/models/hand_landmarker.task` MediaPipe Tasks model.
- Writes landmarks as `frames x 126` arrays and hand masks as `frames x 2` arrays.
- Supports one-hand and two-hand signs by zero-filling missing hand slots.
- Skips complete existing landmark/mask pairs by default.
- Provides verification and visual preview tools.

## What This Sprint Does Not Do
This sprint does not record videos, modify or delete raw videos, train a model, prepare a final `.npz` dataset, create TensorFlow Lite files, create Flutter integration, or start Sprint 2.10.

## Expected Scope
- Expected input videos: 505.
- Expected landmark outputs: 505.
- Participant: P02.
- Labels: 56 total.
- `payment` is included.
- `receipt` is excluded.

## Commands

1. Syntax checks:
```powershell
python -m py_compile ml/src/full_landmark_extraction_config.py ml/src/extract_full_landmarks.py ml/src/check_full_landmark_dataset.py ml/src/preview_full_landmarks.py
```

2. Extraction dry-run:
```powershell
python ml/src/extract_full_landmarks.py --participant P02 --dry-run
```

3. Full extraction, only after confirmation:
```powershell
python ml/src/extract_full_landmarks.py --participant P02
```

4. Full verification:
```powershell
python ml/src/check_full_landmark_dataset.py --participant P02
```

5. Preview representative processed samples:
```powershell
python ml/src/preview_full_landmarks.py --participant P02 --label A --repetition 1
python ml/src/preview_full_landmarks.py --participant P02 --label payment --repetition 1
python ml/src/preview_full_landmarks.py --participant P02 --label 7 --repetition 1
```

## Evidence Screenshots To Capture
- Sprint 2.9 syntax check output.
- Full extraction dry-run summary.
- Full extraction progress or completion summary.
- Full landmark verification pass output.
- Processed landmark folder evidence.
- Landmark preview for `A`, `payment`, and `7`.

## Next Sprint
The next planned stage is Sprint 2.10 dataset preparation and training. It is not part of Sprint 2.9 and has not been started.

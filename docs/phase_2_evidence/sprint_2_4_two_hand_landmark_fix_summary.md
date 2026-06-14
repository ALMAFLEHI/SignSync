# Sprint 2.4 Two-Hand Landmark Fix Summary

## Problem
The first Sprint 2.4 landmark extraction supported only one hand per frame:

```text
1 hand x 21 landmarks x 3 values = 63 values per frame
```

This was not enough for ASL banking-intent signs because some signs may naturally use both hands. A preview test for `deposit` showed only one hand being drawn even when both hands were visible.

## Why This Matters
Future dataset cleaning and model training need a consistent feature format that can represent one-hand and two-hand gestures. If only one hand is extracted, important motion and hand-shape information may be lost for banking-intent signs.

## Fix Applied
Sprint 2.4 extraction and preview now support two hands:

- MediaPipe legacy API uses `max_num_hands=2`.
- MediaPipe Tasks API uses `num_hands=2`.
- Each frame is saved as a fixed 126-value vector.
- Missing hands are filled with zeros.
- Hand ordering is consistent: left hand first, right hand second.
- MediaPipe handedness is used when available.
- If handedness is unavailable or duplicated, image-space x-position is used as a fallback: smaller average x goes to the left slot and larger average x goes to the right slot.

## New Landmark Format
```text
number_of_frames x 126
```

Layout:

```text
columns 0-62   = left hand landmarks
columns 63-125 = right hand landmarks
```

## New Mask Format
```text
number_of_frames x 2
```

Meaning:

```text
mask[frame, 0] = 1 if left hand detected, else 0
mask[frame, 1] = 1 if right hand detected, else 0
```

## Pass/Fail Rule
Sprint 2.4 uses any-hand detection rate for pass/fail:

```text
any_hand_detected_frames / total_frames >= 0.80
```

Two-hand detection rate is still reported for quality review, especially for banking intent signs.

## Commands Used To Verify The Fix
```powershell
python -m py_compile ml/src/check_mediapipe_setup.py ml/src/extract_landmarks.py ml/src/check_landmark_dataset.py ml/src/preview_landmarks.py
python ml/src/check_mediapipe_setup.py
python ml/src/extract_landmarks.py --participant P02 --dry-run
```

## Next Manual Commands
Regenerate Sprint 2.4 landmarks with overwrite:

```powershell
python ml/src/extract_landmarks.py --participant P02 --overwrite
```

Then verify:

```powershell
python ml/src/check_landmark_dataset.py --participant P02
```

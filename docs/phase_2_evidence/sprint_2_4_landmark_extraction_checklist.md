# Sprint 2.4 Landmark Extraction Checklist

## Setup
- [ ] MediaPipe installed.
- [ ] OpenCV installed.
- [ ] NumPy installed.
- [ ] Pandas installed.
- [ ] Setup check passed.

## Extraction
- [ ] Dry-run completed.
- [ ] Real landmark extraction completed.
- [ ] Two-hand landmark `.npy` files generated with shape `frames x 126`.
- [ ] Detection mask `.npy` files generated with shape `frames x 2`.
- [ ] Landmark extraction report generated.
- [ ] Metadata updated.

## Verification
- [ ] Landmark dataset verification passed.
- [ ] Landmark preview checked on at least one alphabet label.
- [ ] Landmark preview checked on at least one banking intent label.
- [ ] Two-hand preview checked on a banking intent sign when both hands are visible.
- [ ] Evidence screenshots saved.

## Evidence Screenshots To Capture
- [ ] MediaPipe setup check output.
- [ ] `extract_landmarks.py --dry-run` output.
- [ ] Landmark extraction summary output.
- [ ] Landmark extraction report Markdown.
- [ ] `check_landmark_dataset.py` pass output.
- [ ] `preview_landmarks.py` showing hand landmarks on at least one video.
- [ ] Landmark output folder showing `.npy` files.
- [ ] Verification report showing expected landmark dimension `126` and mask dimension `2`.

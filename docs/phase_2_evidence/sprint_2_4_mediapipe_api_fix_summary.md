# Sprint 2.4 MediaPipe API Fix Summary

## Error Encountered
Real landmark extraction failed before processing videos with:

```text
AttributeError: module 'mediapipe' has no attribute 'solutions'
```

The failure occurred at:

```python
hands_solution = mediapipe.solutions.hands
```

## Cause
The installed MediaPipe package is `0.10.35` on Python `3.14.3`. In this environment, MediaPipe exposes the newer Tasks API, but it does not expose the legacy `mp.solutions.hands` API.

## Fix Applied
The Sprint 2.4 scripts now support both MediaPipe API styles:

- If `mp.solutions.hands` exists, the legacy Hands API is used.
- If `mp.solutions.hands` is unavailable, the scripts use `mediapipe.tasks.python.vision.HandLandmarker`.
- The default Tasks model path is `ml/models/hand_landmarker.task`.
- Landmark extraction still writes `number_of_frames x 63` arrays and detection masks as planned.
- Preview drawing no longer depends on missing `drawing_utils`; it draws landmarks and hand connections with OpenCV.

## Commands Used To Verify The Fix
```powershell
python -m py_compile ml/src/check_mediapipe_setup.py ml/src/extract_landmarks.py ml/src/check_landmark_dataset.py ml/src/preview_landmarks.py
python ml/src/check_mediapipe_setup.py
python ml/src/extract_landmarks.py --participant P02 --dry-run
```

## Next Manual Command
After the setup/API check passes, run:

```powershell
python ml/src/extract_landmarks.py --participant P02
```

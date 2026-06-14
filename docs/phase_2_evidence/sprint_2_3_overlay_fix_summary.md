# Sprint 2.3 Overlay Fix Summary

## Problem
During Sprint 2.3 trial recording, the raw `.mp4` dataset videos contained webcam preview overlay text such as `Recording`, participant ID, label, repetition, frame count, and `Press Q to cancel`.

This is incorrect for the machine learning dataset because raw training videos should contain only the camera image of the person or hand gesture.

## Fix
`ml/src/collect_video.py` now separates the clean saved frame from the preview frame:

- `clean_frame` is resized/prepared from the camera frame.
- `preview_frame = clean_frame.copy()` is created for the live preview window.
- Overlay text is added only to `preview_frame`.
- `cv2.imshow()` displays `preview_frame`.
- `writer.write(clean_frame)` saves only the clean camera frame.

Countdown text is also shown only in the preview window and is not written to the saved video file.

## Expected Result
- The preview window still shows helpful recording text.
- The saved `.mp4` file is clean and contains no overlay text.
- Raw dataset videos remain suitable for later landmark extraction and model training.

## Manual Test Command
```powershell
python ml/src/collect_video.py --participant P02 --label A --repetition 1 --camera-index 1 --notes "overlay fix test" --overwrite
```

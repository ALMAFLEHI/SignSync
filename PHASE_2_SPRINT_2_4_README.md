# Phase 2 Sprint 2.4 README

## What This Sprint Does
Sprint 2.4 checks MediaPipe support and extracts two-hand landmarks from the 55 Sprint 2.3 trial videos. It saves landmark arrays, detection masks, extraction reports, and metadata updates.

The landmark format is now:

```text
number_of_frames x 126
```

Columns `0-62` store left hand landmarks and columns `63-125` store right hand landmarks. The mask format is:

```text
number_of_frames x 2
```

Mask column `0` means left hand detected and mask column `1` means right hand detected.

## What This Sprint Does Not Do
This sprint does not create model training code, TensorFlow Lite code, Flutter integration, or Sprint 2.5 work.

## Install Or Check MediaPipe
Install Sprint 2.4 requirements if needed:

```powershell
python -m pip install -r requirements_sprint_2_4.txt
```

Check the setup:

```powershell
python ml/src/check_mediapipe_setup.py
```

This project supports the newer MediaPipe Tasks API. When `mp.solutions.hands` is not available, the scripts use:

```text
ml/models/hand_landmarker.task
```

as the default HandLandmarker model path.

## Syntax Checks
```powershell
python -m py_compile ml/src/check_mediapipe_setup.py
python -m py_compile ml/src/extract_landmarks.py
python -m py_compile ml/src/check_landmark_dataset.py
python -m py_compile ml/src/preview_landmarks.py
```

## Dry-Run Extraction
This prints expected input and output paths only. It does not process videos or update metadata.

```powershell
python ml/src/extract_landmarks.py --participant P02 --dry-run
```

## Real Landmark Extraction
Run this only when ready to process the 55 local trial videos:

```powershell
python ml/src/extract_landmarks.py --participant P02
```

If one-hand `63`-dimension landmark files already exist from the first Sprint 2.4 attempt, regenerate them with:

```powershell
python ml/src/extract_landmarks.py --participant P02 --overwrite
```

## Verify Landmark Outputs
After extraction, run:

```powershell
python ml/src/check_landmark_dataset.py --participant P02
```

## Preview Landmarks Visually
Preview an alphabet sample:

```powershell
python ml/src/preview_landmarks.py --participant P02 --label A --repetition 1
```

Preview a banking intent sample:

```powershell
python ml/src/preview_landmarks.py --participant P02 --label deposit --repetition 1
```

If you need to use a different HandLandmarker model path, pass `--model-path` to `extract_landmarks.py` or `preview_landmarks.py`.

Optionally save an annotated evidence preview:

```powershell
python ml/src/preview_landmarks.py --participant P02 --label A --repetition 1 --save-preview
```

The preview video is evidence only. It must not replace or modify raw dataset videos.

## Manual Commands To Run
```powershell
python -m pip install -r requirements_sprint_2_4.txt
python ml/src/check_mediapipe_setup.py
python -m py_compile ml/src/check_mediapipe_setup.py
python -m py_compile ml/src/extract_landmarks.py
python -m py_compile ml/src/check_landmark_dataset.py
python -m py_compile ml/src/preview_landmarks.py
python ml/src/extract_landmarks.py --participant P02 --dry-run
python ml/src/extract_landmarks.py --participant P02
python ml/src/extract_landmarks.py --participant P02 --overwrite
python ml/src/check_landmark_dataset.py --participant P02
python ml/src/preview_landmarks.py --participant P02 --label A --repetition 1
python ml/src/preview_landmarks.py --participant P02 --label deposit --repetition 1
```

## Evidence To Save
- MediaPipe setup check output.
- Dry-run extraction output.
- Landmark extraction summary output.
- Landmark extraction report Markdown.
- Landmark dataset verification pass output.
- Visual landmark preview screenshot.
- Landmark output folder showing `.npy` files.

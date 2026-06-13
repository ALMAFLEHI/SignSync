# Phase 2 Sprint 2.2 README

## What This Sprint Does
Sprint 2.2 adds the SignSync raw video collection tool. The tool records one webcam video sample at a time, saves it under the selected label folder, and appends a metadata row after successful recording.

This sprint does not include landmark extraction, model training, or Flutter integration.

## Install OpenCV If Needed
If OpenCV is not installed, run:

```powershell
pip install opencv-python
```

## How To Run The Collection Tool
Run commands from the project root:

```powershell
python ml/src/collect_video.py --participant P01 --label deposit --repetition 1
```

Examples:

```powershell
python ml/src/collect_video.py --participant P01 --label deposit --repetition 1
python ml/src/collect_video.py --participant P01 --label A --repetition 1
python ml/src/collect_video.py --participant P01 --label 0 --repetition 1
```

Optional settings:

```powershell
python ml/src/collect_video.py --participant P01 --label deposit --repetition 1 --frames 60 --fps 20 --width 640 --height 480 --notes "clear lighting"
```

Use `--overwrite` only when you intentionally want to replace an existing video for the same participant, label, and repetition.

## How To Cancel
Press `Q` while the webcam window is open. If recording is cancelled before completion, incomplete video output is removed and metadata is not updated.

## Where Videos Are Saved
Videos are saved under:

```text
ml/data_raw/videos/[label]/
```

Example:

```text
ml/data_raw/videos/deposit/P01_deposit_R01.mp4
```

## How Metadata Is Updated
After a successful recording, one row is appended to:

```text
ml/metadata.csv
```

The `landmark_path` field remains empty in Sprint 2.2 because landmark extraction belongs to a later sprint.

## FYP Evidence Screenshots
Save screenshots of:

- The terminal command used to run the script.
- The webcam preview window titled `SignSync Data Collection`.
- The countdown screen.
- The terminal success summary.
- The saved video file inside the correct label folder.
- The updated `ml/metadata.csv` row.
- The syntax check command and result.

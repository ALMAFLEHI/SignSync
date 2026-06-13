# SignSync Sprint 2.2 Collection Tool Summary

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.2: Data Collection Tool

## Sprint Goal
Create a reliable camera-based data collection tool that records raw ASL gesture videos and stores metadata for each sample.

## What collect_video.py Does
- Accepts participant ID, label, and repetition from the command line.
- Validates labels against the Sprint 2.1 vocabulary in `ml/src/labels.py`.
- Validates participant IDs such as `P01`, `P02`, and `P03`.
- Validates repetition and recording settings as positive integers.
- Opens a webcam with OpenCV and displays a live preview.
- Shows a countdown before recording starts.
- Records raw gesture videos into the matching label folder.
- Appends metadata only after a successful complete recording.
- Cancels safely with `Q` without saving incomplete metadata.

## Command Example
```powershell
python ml/src/collect_video.py --participant P01 --label deposit --repetition 1
```

## Output File Naming Standard
Videos are saved as `.mp4` files under:

```text
ml/data_raw/videos/[label]/
```

Example:

```text
ml/data_raw/videos/deposit/P01_deposit_R01.mp4
```

## Metadata Fields
`ml/metadata.csv` uses these headers:

```text
sample_id,participant_id,label,repetition,video_path,landmark_path,status,notes
```

Sprint 2.2 metadata rows use:
- `sample_id`: sample identifier such as `P01_deposit_R01`
- `participant_id`: participant identifier such as `P01`
- `label`: selected dataset label
- `repetition`: numeric repetition value
- `video_path`: relative path to the saved video
- `landmark_path`: left empty for Sprint 2.2
- `status`: `raw_recorded`
- `notes`: user notes and recording details

## Acceptance Checklist
- [x] `collect_video.py` exists in `ml/src/`.
- [x] Script uses `argparse` for command-line arguments.
- [x] Script uses `pathlib` for project paths.
- [x] Script uses `csv` for metadata logging.
- [x] Script validates labels using `ml/src/labels.py`.
- [x] Script validates participant ID format.
- [x] Script validates repetition as a positive integer.
- [x] Script records videos with OpenCV.
- [x] Script saves `.mp4` files using the required naming standard.
- [x] Script prevents accidental overwrite unless `--overwrite` is used.
- [x] Script appends metadata after successful recording only.
- [x] Script cancels safely with `Q`.
- [x] No landmark extraction, model training, or Flutter integration is included.

## Evidence Screenshots To Capture
- Terminal command used to run `collect_video.py`.
- Webcam preview window titled `SignSync Data Collection`.
- Countdown display before recording.
- Terminal success summary after recording.
- Saved `.mp4` file in the correct label folder.
- Updated `ml/metadata.csv` row.
- Syntax check result for `collect_video.py`.

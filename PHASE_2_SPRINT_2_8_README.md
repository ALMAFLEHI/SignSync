# Phase 2 Sprint 2.8 README

## What This Sprint Does
Sprint 2.8 prepares the manual full dataset collection workflow for the 45 labels not included in the Sprint 2.3 trial dataset. It provides a stable configuration, 450 generated commands, an interactive recording runner, and a post-collection verification script.

## What This Sprint Does Not Do
This sprint does not automatically record videos, modify raw trial videos, modify the Sprint 2.5 dataset, retrain the Sprint 2.6 model, create TensorFlow Lite files, create Flutter integration, or start Sprint 2.9.

## Scope
- Remaining labels: 45.
- Repetitions per label: 10.
- Expected recordings: 450.
- Participant: P02.
- Camera index: 1.
- Notes: `Sprint 2.8 full dataset collection`.

## Syntax Check Commands
```powershell
python -m py_compile ml/src/full_collection_config.py ml/src/generate_full_collection_commands.py ml/src/run_full_collection.py ml/src/check_full_collection_dataset.py
```

## Generate Commands
```powershell
python ml/src/generate_full_collection_commands.py
```

## Dry-Run Collection
This prints the 450 commands only. It does not open the camera or record videos.

```powershell
python ml/src/run_full_collection.py --dry-run
```

## Start Real Collection
Run this only when you are ready to record manually with camera index 1. The runner prompts before every recording.

```powershell
python ml/src/run_full_collection.py --participant P02 --camera-index 1
```

To resume from a label and repetition:

```powershell
python ml/src/run_full_collection.py --participant P02 --camera-index 1 --start-label D --start-repetition 1
```

## Verify Collection
Run only after the manual collection is complete:

```powershell
python ml/src/check_full_collection_dataset.py --participant P02
```

The verification reports are written to:

```text
docs/phase_2_evidence/sprint_2_8_full_collection_check.csv
docs/phase_2_evidence/sprint_2_8_full_collection_check.md
```

## Required Manual Commands
```powershell
python -m py_compile ml/src/full_collection_config.py ml/src/generate_full_collection_commands.py ml/src/run_full_collection.py ml/src/check_full_collection_dataset.py
python ml/src/generate_full_collection_commands.py
python ml/src/run_full_collection.py --dry-run
python ml/src/run_full_collection.py --participant P02 --camera-index 1
python ml/src/check_full_collection_dataset.py --participant P02
```

## Evidence Screenshots To Capture
- Sprint 2.8 syntax check output.
- Full command generation summary.
- Dry-run output.
- Interactive collection prompt and recording preview.
- Raw folders after collection.
- `metadata.csv` rows for the new recordings.
- Verification pass summary and reports.

## Sprint 2.8 Rework: Redo 7 and Replace receipt with payment
The rework removes `receipt` from the dataset vocabulary and adds `payment` in its place, keeping 56 total labels, 45 remaining collection labels, and 450 expected Sprint 2.8 recordings. It also prepares digit `7` for a complete re-recording from R01 to R10.

Run the cleanup dry-run first. It only reports planned backups and scoped metadata cleanup:

```powershell
python -m py_compile ml/src/labels.py ml/src/full_collection_config.py ml/src/check_full_collection_dataset.py ml/src/sprint_2_8_rework_labels.py ml/src/generate_rework_recording_commands.py ml/src/run_rework_recordings.py

python ml/src/sprint_2_8_rework_labels.py --dry-run
python ml/src/sprint_2_8_rework_labels.py --apply

python ml/src/generate_rework_recording_commands.py

python ml/src/run_rework_recordings.py --dry-run
python ml/src/run_rework_recordings.py --participant P02 --camera-index 1

python ml/src/check_full_collection_dataset.py --participant P02
```

`--apply` creates a metadata backup, moves only P02 digit-7 and P02 receipt videos into the rework backup folder, and removes only their scoped metadata rows. Do not use it until the dry-run report is reviewed.

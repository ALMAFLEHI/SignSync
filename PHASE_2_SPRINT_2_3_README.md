# Phase 2 Sprint 2.3 README

## What This Sprint Does
Sprint 2.3 creates a controlled trial dataset workflow before full dataset collection. It provides configuration, command generation, an interactive collection runner, verification scripts, and documentation for recording 55 trial videos.

## What This Sprint Does Not Do
This sprint does not create landmark extraction, model training, Flutter integration, or full dataset collection.

## Trial Scope
- Participant ID: `P02`
- Camera index: `1`
- Labels: `A`, `B`, `C`, `0`, `1`, `2`, `deposit`, `withdraw`, `balance`, `help`, `confirm`
- Repetitions: 5 per label
- Expected videos: 55

## Syntax Checks
Run these commands from the project root:

```powershell
python -m py_compile ml/src/trial_config.py
python -m py_compile ml/src/generate_trial_commands.py
python -m py_compile ml/src/run_trial_collection.py
python -m py_compile ml/src/check_trial_dataset.py
```

## Generate Trial Commands
```powershell
python ml/src/generate_trial_commands.py
```

Generated files:

```text
docs/phase_2_evidence/sprint_2_3_trial_commands.ps1
docs/phase_2_evidence/sprint_2_3_trial_commands.md
```

## Run Dry-Run Collection
This prints the commands only and does not record videos:

```powershell
python ml/src/run_trial_collection.py --dry-run
```

## Start Real Trial Collection
Run this only when ready to record with the webcam:

```powershell
python ml/src/run_trial_collection.py --participant P02 --camera-index 1
```

You will be prompted before every sample:

```text
Prepare sign [label], repetition [RXX]. Press Enter to record or type skip.
```

## Verify Trial Dataset
After recording all trial samples, run:

```powershell
python ml/src/check_trial_dataset.py --participant P02
```

Verification reports are saved to:

```text
docs/phase_2_evidence/sprint_2_3_trial_dataset_check.csv
docs/phase_2_evidence/sprint_2_3_trial_dataset_check.md
```

## Troubleshooting
If overlay text appears in saved videos, the saved frame must be clean and only the preview window should contain overlays. The recording script should write clean camera frames to the `.mp4` file and use a copied preview frame for `cv2.putText()` display text.

## Manual Commands To Run
```powershell
python -m py_compile ml/src/trial_config.py
python -m py_compile ml/src/generate_trial_commands.py
python -m py_compile ml/src/run_trial_collection.py
python -m py_compile ml/src/check_trial_dataset.py
python ml/src/generate_trial_commands.py
python ml/src/run_trial_collection.py --dry-run
python ml/src/run_trial_collection.py --participant P02 --camera-index 1
python ml/src/check_trial_dataset.py --participant P02
```

## Evidence To Save
- Dry-run output.
- Webcam recording with clear hand visible.
- Raw video folders after recording.
- `metadata.csv` after trial recording.
- Trial dataset verification pass output.
- `sprint_2_3_trial_dataset_check.md` report.

# Phase 2 Sprint 2.5 README

## What This Sprint Does
Sprint 2.5 prepares the extracted Sprint 2.4 two-hand landmark data into a clean machine-learning-ready dataset. It checks landmark quality, standardizes sequence length, creates label mappings, defines train/validation/test splits, and provides verification reports.

## What This Sprint Does Not Do
This sprint does not train a model, create TensorFlow Lite output, create Flutter integration, record new videos, or start Sprint 2.6.

## Dataset Input
- Metadata: `ml/metadata.csv`
- Landmark files: `ml/data_processed/landmarks/[label]/[sample_id]_landmarks.npy`
- Mask files: `ml/data_processed/landmarks/[label]/[sample_id]_mask.npy`
- Participant: `P02`
- Expected samples: `55`

## Dataset Output
When the real preparation command is run, outputs are saved to:

```text
ml/data_processed/datasets/
```

Expected output files:

```text
signsync_trial_v1_2hand_60f.npz
signsync_trial_v1_label_mapping.json
signsync_trial_v1_splits.csv
```

## Landmark Quality Check Command
```powershell
python ml/src/analyze_landmark_quality.py --participant P02
```

## Dataset Preparation Dry-Run Command
```powershell
python ml/src/prepare_training_dataset.py --participant P02 --dry-run
```

## Real Dataset Preparation Command
Run this only after reviewing the dry-run output:

```powershell
python ml/src/prepare_training_dataset.py --participant P02
```

If the dataset already exists and should be replaced:

```powershell
python ml/src/prepare_training_dataset.py --participant P02 --overwrite
```

## Training Dataset Verification Command
```powershell
python ml/src/check_training_dataset.py
```

## Exact Manual Commands To Run
```powershell
python -m py_compile ml/src/dataset_config.py ml/src/analyze_landmark_quality.py ml/src/prepare_training_dataset.py ml/src/check_training_dataset.py
python ml/src/analyze_landmark_quality.py --participant P02
python ml/src/prepare_training_dataset.py --participant P02 --dry-run
python ml/src/prepare_training_dataset.py --participant P02
python ml/src/prepare_training_dataset.py --participant P02 --overwrite
python ml/src/check_training_dataset.py
dir ml\data_processed\datasets
```

## Evidence To Save
- Landmark quality check output.
- Dataset preparation dry-run output.
- Dataset preparation summary output.
- Training dataset verification pass output.
- Training dataset check Markdown report.
- Dataset output folder showing `.npz`, label mapping JSON, and split CSV.

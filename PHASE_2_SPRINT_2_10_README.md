# Phase 2 Sprint 2.10 README

## Sprint Goal
Sprint 2.10 prepares the full 505-sample SignSync landmark dataset for training and defines a current scikit-learn baseline training, evaluation, and prediction workflow.

## What This Sprint Does
- Validates the full landmark/mask quality.
- Prepares `X = 505 x 60 x 126`, `mask = 505 x 60 x 2`, and `y = 505`.
- Uses repetition-based train/validation/test splits: 348/56/101.
- Saves Normal Mode, Number Mode, and all-label metadata for later integration.
- Defines Logistic Regression, Random Forest, and Extra Trees baseline candidates.

## What This Sprint Does Not Do
This sprint does not record or alter raw videos, re-extract landmarks, add 30 extra banking intents, create TensorFlow or TFLite files, create Flutter integration, or start Sprint 2.11.

## Dataset Scope
- Labels: 56.
- Samples: 505.
- `payment`: included.
- `receipt`: excluded.
- Target frames: 60.
- Landmark dimension: 126.
- Mask dimension: 2.

## Commands

1. Syntax check:
```powershell
python -m py_compile ml/src/full_dataset_config.py ml/src/analyze_full_landmark_quality.py ml/src/prepare_full_training_dataset.py ml/src/check_full_training_dataset.py ml/src/full_model_feature_utils.py ml/src/train_full_baseline_model.py ml/src/evaluate_full_baseline_model.py ml/src/predict_full_sample.py
```

2. Landmark quality analysis:
```powershell
python ml/src/analyze_full_landmark_quality.py --participant P02
```

3. Dataset preparation dry-run:
```powershell
python ml/src/prepare_full_training_dataset.py --participant P02 --dry-run
```

4. Full dataset preparation, only after confirmation:
```powershell
python ml/src/prepare_full_training_dataset.py --participant P02
```

5. Dataset verification:
```powershell
python ml/src/check_full_training_dataset.py --participant P02
```

6. Baseline training dry-run, only after preparation:
```powershell
python ml/src/train_full_baseline_model.py --dry-run
```

7. Training, evaluation, and sample predictions, only after confirmation:
```powershell
python ml/src/train_full_baseline_model.py --overwrite
python ml/src/evaluate_full_baseline_model.py
python ml/src/predict_full_sample.py --sample-id P02_A_R01
python ml/src/predict_full_sample.py --sample-id P02_payment_R01
python ml/src/predict_full_sample.py --sample-id P02_7_R01
```

## Evidence Screenshots To Capture
- Sprint 2.10 syntax check output.
- Full landmark quality report output.
- Dataset preparation dry-run and final summary.
- Training dry-run and training summary.
- Evaluation summary and confusion matrix.
- Predictions for `A`, `payment`, and `7`.

## Acceptance Criteria
- Full landmark quality report is valid for 505 samples.
- Full dataset has expected X/mask/y shapes.
- Repetition-based split counts are 348/56/101.
- Label groups include Normal Mode, Number Mode, and all labels.
- Training selection uses validation only and evaluates test only.
- Reports include the single-participant controlled-dataset limitation.

## Next Sprint
Sprint 2.11 will add 30 extra banking intents. It has not been started.

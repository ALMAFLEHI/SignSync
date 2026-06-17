# Phase 2 Sprint 2.6 README

## What This Sprint Does
Sprint 2.6 trains the first baseline SignSync recognition model using the Sprint 2.5 prepared trial dataset. It uses scikit-learn models, generates training/evaluation reports, saves the best model artifact, and supports a single-sample prediction test.

This is a trial baseline using only 55 samples. The goal is pipeline validation, not final production accuracy.

## What This Sprint Does Not Do
This sprint does not create TensorFlow Lite code, Flutter integration, full dataset collection, or Sprint 2.7 work.

## Dataset Input
```text
ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz
```

Expected shape:

```text
X = 55 x 60 x 126
y = 55
```

## Model Outputs
```text
ml/models/sprint_2_6/signsync_trial_baseline_model.joblib
ml/models/sprint_2_6/signsync_trial_baseline_scaler.joblib
ml/models/sprint_2_6/signsync_trial_label_names.json
```

## Setup Command
```powershell
python -m pip install -r requirements_sprint_2_6.txt
```

## Setup Check Command
```powershell
python ml/src/check_model_training_setup.py
```

## Training Dry-Run Command
```powershell
python ml/src/train_baseline_model.py --dry-run
```

## Real Training Command
Run only when ready to train:

```powershell
python ml/src/train_baseline_model.py
```

If model output already exists:

```powershell
python ml/src/train_baseline_model.py --overwrite
```

## Evaluation Command
```powershell
python ml/src/evaluate_baseline_model.py
```

## Prediction Sample Command
```powershell
python ml/src/predict_sample.py --sample-id P02_A_R01
```

## Exact Manual Commands To Run
```powershell
python -m pip install -r requirements_sprint_2_6.txt
python ml/src/check_model_training_setup.py
python -m py_compile ml/src/model_config.py ml/src/check_model_training_setup.py ml/src/train_baseline_model.py ml/src/evaluate_baseline_model.py ml/src/predict_sample.py
python ml/src/train_baseline_model.py --dry-run
python ml/src/train_baseline_model.py
python ml/src/train_baseline_model.py --overwrite
python ml/src/evaluate_baseline_model.py
python ml/src/predict_sample.py --sample-id P02_A_R01
dir ml\models\sprint_2_6
dir docs\phase_2_evidence
```

## Evidence To Save
- Model training setup check output.
- Training dry-run output.
- Training summary output.
- Evaluation summary output.
- Confusion matrix file/folder evidence.
- Prediction sample output.
- Model output folder showing saved `.joblib` files.

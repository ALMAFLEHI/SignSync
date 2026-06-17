# Sprint 2.6 Training Report

## Dataset
- Dataset path: ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz
- X shape: (55, 60, 126)
- Feature mode: stats
- Feature shape: (55, 756)
- Number of labels: 11
- Train samples: 33
- Validation samples: 11

## Tested Models
- LogisticRegression: validation accuracy 0.9091
- RandomForestClassifier: validation accuracy 1.0000

## Selected Best Model
- Model: RandomForestClassifier
- Validation accuracy: 1.0000
- Model output path: ml/models/sprint_2_6/signsync_trial_baseline_model.joblib

## Important Note
This is a trial baseline model trained on only 55 samples. It validates the machine learning pipeline but does not represent final production performance.

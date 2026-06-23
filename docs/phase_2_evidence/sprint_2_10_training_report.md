# Sprint 2.10 Full Baseline Training Report

## Dataset
- Dataset path: ml/data_processed/datasets/signsync_full_v1_2hand_60f.npz
- X shape: (505, 60, 126)
- Feature mode: stats
- Feature shape: (505, 756)
- Labels: 56
- Train/validation/test: 348/56/101

## Candidate Models
- LogisticRegression: validation accuracy 0.9107, macro F1 0.8810
- RandomForestClassifier: validation accuracy 0.9643, macro F1 0.9524
- ExtraTreesClassifier: validation accuracy 0.9821, macro F1 0.9762

## Selected Model
- Model: ExtraTreesClassifier
- Validation accuracy: 0.9821
- Validation macro F1: 0.9762
- Model output: ml/models/sprint_2_10/signsync_full_v1_baseline_model.joblib

## Scope Note
This is a single-participant controlled dataset baseline. It validates the current pipeline and scoped dataset, not real-world production accuracy.

# Sprint 2.12 Expanded Baseline Training Report

## Dataset
- Dataset path: ml/data_processed/datasets/signsync_expanded_v2_2hand_60f.npz
- X shape: (805, 60, 126)
- Feature mode: stats
- Feature shape: (805, 756)
- Labels: 86
- Train/validation/test: 558/86/161

## Candidate Models
- LogisticRegression: validation accuracy 0.9186, macro F1 0.8915
- RandomForestClassifier: validation accuracy 0.9419, macro F1 0.9244
- ExtraTreesClassifier: validation accuracy 0.9535, macro F1 0.9419

## Selected Model
- Model: ExtraTreesClassifier
- Validation accuracy: 0.9535
- Validation macro F1: 0.9419
- Model output: ml/models/sprint_2_12/signsync_expanded_v2_baseline_model.joblib

## Scope Note
This is a single-participant controlled dataset baseline. It measures the expanded V2 pipeline, not production accuracy.

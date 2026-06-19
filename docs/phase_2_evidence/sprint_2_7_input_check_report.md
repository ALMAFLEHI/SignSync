# Sprint 2.7 Input Check Report

## Result
| Check | Status | Detail |
| --- | --- | --- |
| Sprint 2.5 dataset | PASS | ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz |
| Sprint 2.6 model | PASS | ml/models/sprint_2_6/signsync_trial_baseline_model.joblib |
| Sprint 2.6 label names | PASS | ml/models/sprint_2_6/signsync_trial_label_names.json |
| Sprint 2.5 split CSV | PASS | ml/data_processed/datasets/signsync_trial_v1_splits.csv |
| Sprint 2.5 label mapping | PASS | ml/data_processed/datasets/signsync_trial_v1_label_mapping.json |
| Sprint 2.6 training report | PASS | docs/phase_2_evidence/sprint_2_6_training_report.md |
| Sprint 2.6 evaluation report | PASS | docs/phase_2_evidence/sprint_2_6_evaluation_report.md |
| Sprint 2.6 confusion matrix | PASS | docs/phase_2_evidence/sprint_2_6_confusion_matrix.png |
| Sprint 2.5 dataset contents | PASS | {'x_shape': [55, 60, 126], 'y_shape': [55], 'label_count': 11, 'split_counts': {np.str_('train'): 33, np.str_('val'): 11, np.str_('test'): 11}, 'stats_feature_shape': [55, 756]} |
| Saved model feature shape | PASS | RandomForestClassifier; n_features_in_=756; expected=756 |
| Saved label names | PASS | label names count=11 |

## Dataset Summary
- X shape: [55, 60, 126]
- y shape: [55]
- Number of labels: 11
- Train/validation/test counts: {np.str_('train'): 33, np.str_('val'): 11, np.str_('test'): 11}
- Stats feature shape: [55, 756]

## Scope
This check only reads the prepared dataset and saved model artifacts. It does not retrain a model or modify the dataset.

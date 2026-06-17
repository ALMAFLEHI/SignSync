# SignSync Sprint 2.6 Model Training Plan

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.6: First Model Training Using Trial Dataset

## Sprint Goal
Train and validate the first baseline recognition model using the Sprint 2.5 prepared landmark dataset.

This sprint validates the machine learning pipeline from prepared dataset to trained model, evaluation metrics, confusion matrix, and saved model artifact.

## Input Dataset
```text
ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz
```

Expected dataset:
- `X` shape: `55 x 60 x 126`
- `y` shape: `55`
- Labels: `11`
- Train samples: `33`
- Validation samples: `11`
- Test samples: `11`

## Model Approach
Use scikit-learn baseline models:
- Logistic Regression
- Random Forest Classifier

The best model is selected using validation accuracy.

## Feature Extraction Approach
Default feature mode: `stats`

For each `60 x 126` sample, statistical features are created by concatenating:
- mean over frames
- standard deviation over frames
- minimum over frames
- maximum over frames
- first frame
- last frame

Final stats feature size:

```text
126 x 6 = 756
```

Optional feature mode: `flatten`

```text
60 x 126 = 7560
```

## Train/Validation/Test Usage
- Training split trains each baseline model.
- Validation split selects the best baseline model.
- Test split is used only by the evaluation script after training.

## Output Files
Model outputs:

```text
ml/models/sprint_2_6/signsync_trial_baseline_model.joblib
ml/models/sprint_2_6/signsync_trial_baseline_scaler.joblib
ml/models/sprint_2_6/signsync_trial_label_names.json
```

Evidence outputs:

```text
docs/phase_2_evidence/sprint_2_6_training_report.csv
docs/phase_2_evidence/sprint_2_6_training_report.md
docs/phase_2_evidence/sprint_2_6_evaluation_report.csv
docs/phase_2_evidence/sprint_2_6_evaluation_report.md
docs/phase_2_evidence/sprint_2_6_confusion_matrix.png
docs/phase_2_evidence/sprint_2_6_metrics_summary.json
```

## Evaluation Metrics
- Accuracy
- Macro precision
- Macro recall
- Macro F1-score
- Weighted precision
- Weighted recall
- Weighted F1-score
- Per-class classification report
- Confusion matrix

## Acceptance Criteria
- [ ] Model training setup check passes.
- [ ] Training dry-run passes.
- [ ] Baseline model is trained.
- [ ] Best model is saved.
- [ ] Evaluation on test split is completed.
- [ ] Accuracy, precision, recall, and F1 are reported.
- [ ] Confusion matrix is generated.
- [ ] Prediction test works for at least one sample.
- [ ] Reports are generated.
- [ ] No TFLite conversion is created.
- [ ] No Flutter integration is created.

## What This Sprint Does Not Include
- No full dataset recording.
- No TensorFlow Lite conversion.
- No Flutter integration.
- No production accuracy claim.
- No Sprint 2.7 work.

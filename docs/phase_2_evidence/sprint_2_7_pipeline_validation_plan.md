# Sprint 2.7 Pipeline Validation Plan

## Project
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions.

## Sprint
Phase 2, Sprint 2.7: Pipeline Validation, Limitation Analysis, and Full Dataset Recording Plan.

## Goal
Validate the saved Sprint 2.6 model pipeline, document why the 100% trial result is not final production performance, and prepare a controlled plan for completing the remaining dataset labels.

## Why This Sprint Is Needed
Sprint 2.6 confirmed that a baseline model can train and predict on the small trial dataset. Sprint 2.7 confirms that the saved artifact can be loaded and used again, then records the dataset limitations before moving to larger-scale collection.

## Inputs
- Sprint 2.5 prepared dataset and label mapping.
- Sprint 2.5 split CSV.
- Sprint 2.6 saved model and label names JSON.
- Sprint 2.6 training report, evaluation report, and confusion matrix.
- Sprint 2.1 complete 56-label vocabulary.

## Scripts Created
- `ml/src/pipeline_validation_config.py`
- `ml/src/check_sprint_2_7_inputs.py`
- `ml/src/validate_saved_model_pipeline.py`
- `ml/src/analyze_trial_dataset_limitations.py`
- `ml/src/generate_full_dataset_recording_plan.py`

## Reports Generated
- Input check report.
- Saved-model metric and prediction reports.
- Trial dataset limitation report in Markdown and JSON.
- Remaining labels CSV.
- Full dataset recording plan in Markdown and CSV.
- Readiness decision report.

## Validation Checks
- Confirm all required Sprint 2.5 and Sprint 2.6 artifacts exist.
- Confirm the dataset shape, label count, and split counts.
- Confirm the saved model loads and expects 756 stats features.
- Run predictions over train, validation, test, and all samples without retraining.
- Save per-sample prediction results with confidence when available.

## Dataset Limitation Analysis
The analysis documents the small sample size, the single participant, one test sample per class, limited environmental variation, limited lighting/background variation, no cross-participant test, trial-only vocabulary, and incomplete full-label coverage.

## Full Dataset Recording Plan
The plan identifies the 11 trial labels already represented and the 45 remaining labels. It recommends five initial P02 repetitions per remaining label using camera index 1, then additional repetitions and participants when possible.

## Acceptance Criteria
- [x] Sprint 2.7 input check passes.
- [x] Saved model loads successfully.
- [x] Saved model can predict samples.
- [x] Train, validation, test, and all-sample metrics are generated.
- [x] Prediction check report is generated.
- [x] Dataset limitation report is generated.
- [x] Remaining labels list is generated.
- [x] Full dataset recording plan is generated.
- [x] Readiness decision report is generated.
- [x] No model retraining was performed.
- [x] No raw videos were recorded.
- [x] No TensorFlow Lite files were created.
- [x] No Flutter integration was created.

## Out of Scope
Sprint 2.7 does not retrain the model, modify the Sprint 2.5 dataset, modify landmarks, record videos, create TensorFlow Lite files, create Flutter integration, or start Sprint 2.8.

# Phase 2 Sprint 2.7 README

## What This Sprint Does
Sprint 2.7 validates the saved Sprint 2.6 model pipeline, checks the required inputs, writes train/validation/test/all prediction metrics, documents the limitations of the small trial dataset, and prepares the plan for recording the remaining labels.

## What This Sprint Does Not Do
This sprint does not retrain a model, modify the Sprint 2.5 dataset, modify raw videos or landmarks, record new videos, create TensorFlow Lite files, create Flutter integration, or start Sprint 2.8.

## Required Sprint 2.6 Inputs
```text
ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz
ml/data_processed/datasets/signsync_trial_v1_label_mapping.json
ml/data_processed/datasets/signsync_trial_v1_splits.csv
ml/models/sprint_2_6/signsync_trial_baseline_model.joblib
ml/models/sprint_2_6/signsync_trial_label_names.json
docs/phase_2_evidence/sprint_2_6_training_report.md
docs/phase_2_evidence/sprint_2_6_evaluation_report.md
docs/phase_2_evidence/sprint_2_6_confusion_matrix.png
```

## Scripts Created
```text
ml/src/pipeline_validation_config.py
ml/src/check_sprint_2_7_inputs.py
ml/src/validate_saved_model_pipeline.py
ml/src/analyze_trial_dataset_limitations.py
ml/src/generate_full_dataset_recording_plan.py
```

## Reports Created
```text
docs/phase_2_evidence/sprint_2_7_input_check_report.md
docs/phase_2_evidence/sprint_2_7_pipeline_validation_report.csv
docs/phase_2_evidence/sprint_2_7_pipeline_validation_report.md
docs/phase_2_evidence/sprint_2_7_prediction_check_report.csv
docs/phase_2_evidence/sprint_2_7_prediction_check_report.md
docs/phase_2_evidence/sprint_2_7_dataset_limitation_report.md
docs/phase_2_evidence/sprint_2_7_dataset_limitation_report.json
docs/phase_2_evidence/sprint_2_7_remaining_labels.csv
docs/phase_2_evidence/sprint_2_7_full_dataset_recording_plan.csv
docs/phase_2_evidence/sprint_2_7_full_dataset_recording_plan.md
docs/phase_2_evidence/sprint_2_7_readiness_decision.md
```

## Exact Manual Commands To Run

1. Syntax checks:
```powershell
python -m py_compile ml/src/pipeline_validation_config.py ml/src/check_sprint_2_7_inputs.py ml/src/validate_saved_model_pipeline.py ml/src/analyze_trial_dataset_limitations.py ml/src/generate_full_dataset_recording_plan.py
```

2. Check Sprint 2.7 inputs:
```powershell
python ml/src/check_sprint_2_7_inputs.py
```

3. Validate saved model pipeline:
```powershell
python ml/src/validate_saved_model_pipeline.py
```

4. Analyze trial dataset limitations:
```powershell
python ml/src/analyze_trial_dataset_limitations.py
```

5. Generate full dataset recording plan:
```powershell
python ml/src/generate_full_dataset_recording_plan.py
```

6. Check generated evidence reports:
```powershell
dir docs\phase_2_evidence
```

## Evidence To Save
- Input check terminal output.
- Saved model pipeline validation output.
- Dataset limitation analysis output.
- Full dataset recording plan output.
- Remaining labels CSV or evidence folder view.
- Sprint 2.7 report folder view.

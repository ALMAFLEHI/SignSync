# Sprint 2.13 Keras Training Report

## Dataset
- Feature dataset: ml/data_processed/datasets/signsync_expanded_v2_stats_756f.npz
- Feature shape: (805, 756)
- Classes: 86
- Train/validation/test: 558/86/161

## Candidate Models
- small: units [256, 128], validation accuracy 0.9186, validation macro F1 0.8953, epochs 69
- medium: units [512, 256, 128], validation accuracy 0.9302, validation macro F1 0.9109, epochs 72
- large: units [1024, 512, 256], validation accuracy 0.9186, validation macro F1 0.8953, epochs 73

## Selected Model
- Candidate: medium
- Hidden units: [512, 256, 128]
- Validation accuracy: 0.9302
- Validation macro F1: 0.9109
- Keras model: ml/models/sprint_2_13/signsync_expanded_v2_keras_best.keras
- SavedModel export: ml/models/sprint_2_13/saved_model/signsync_expanded_v2_keras_best

## Scope Note
The test split is not used for model selection. Test evaluation is handled by `evaluate_tflite_keras_model.py`.

# Phase 2 Sprint 2.13: TFLite-Compatible Model Training and Export Preparation

## Sprint Goal

Sprint 2.13 prepares a mobile-compatible model path for SignSync by training a TensorFlow/Keras model on the expanded V2 dataset, converting it to TensorFlow Lite, testing the exported model, and preparing model metadata for later Flutter integration.

## What This Sprint Does

- Checks TensorFlow/TFLite environment readiness.
- Converts `(60, 126)` landmark sequences into 756 statistical features.
- Trains a TensorFlow/Keras MLP on the expanded V2 dataset.
- Evaluates the Keras model on the held-out test split.
- Converts the Keras model to float32 and dynamic-range TFLite formats.
- Tests exported TFLite models on the held-out test split.
- Creates model asset files for later Flutter integration.

## What This Sprint Does Not Do

- Record new videos.
- Modify or delete raw videos.
- Modify or overwrite Sprint 2.10 or Sprint 2.12 baseline artifacts.
- Create Flutter UI files.
- Start mobile testing.
- Start optional weak-label recording.
- Start Sprint 2.14.

## Environment Notes

TensorFlow compatibility depends on Python version and operating system. Use:

```powershell
python ml/src/check_tflite_environment.py
```

If TensorFlow is missing, create a separate compatible Python 3.11/3.12 environment, WSL environment, or Google Colab runtime. Do not install packages globally without confirmation.

## TFLite-Compatible Model Strategy

The Sprint 2.13 model uses the same statistical features as the Sprint 2.12 scikit-learn baseline. This keeps the later Flutter input pipeline simple and reproducible.

Feature order:

1. mean
2. std
3. min
4. max
5. first_frame
6. last_frame

Each group has 126 values, so the total input width is `126 x 6 = 756`.

## Model Contract

- Source sequence shape: `[60, 126]`
- TFLite input shape: `[1, 756]`
- TFLite input dtype: `float32`
- TFLite output shape: `[1, 86]`
- TFLite output dtype: `float32`
- Output labels: expanded V2 label order
- Normal Mode: 76 labels
- Number Mode: 10 labels

## Commands

Run these commands from the project root.

```powershell
python -m py_compile ml/src/check_tflite_environment.py ml/src/tflite_model_config.py ml/src/prepare_tflite_training_features.py ml/src/check_tflite_training_features.py ml/src/train_tflite_keras_model.py ml/src/evaluate_tflite_keras_model.py ml/src/convert_keras_to_tflite.py ml/src/test_tflite_model.py ml/src/predict_tflite_sample.py ml/src/create_flutter_model_assets.py

python ml/src/check_tflite_environment.py

python ml/src/prepare_tflite_training_features.py --dry-run

python ml/src/prepare_tflite_training_features.py --overwrite

python ml/src/check_tflite_training_features.py

python ml/src/train_tflite_keras_model.py --dry-run

python ml/src/train_tflite_keras_model.py --overwrite --epochs 200 --batch-size 32

python ml/src/evaluate_tflite_keras_model.py

python ml/src/convert_keras_to_tflite.py

python ml/src/test_tflite_model.py

python ml/src/predict_tflite_sample.py --sample-id P02_A_R01
python ml/src/predict_tflite_sample.py --sample-id P02_payment_R01
python ml/src/predict_tflite_sample.py --sample-id P02_document_R01
python ml/src/predict_tflite_sample.py --sample-id P02_signature_R01
python ml/src/predict_tflite_sample.py --sample-id P02_atm_R01

python ml/src/create_flutter_model_assets.py
```

## Evidence Screenshot Names

- `01_sprint_2_13_environment_check.png`
- `02_sprint_2_13_feature_preparation_dry_run.png`
- `03_sprint_2_13_feature_dataset_created.png`
- `04_sprint_2_13_feature_dataset_check_passed.png`
- `05_sprint_2_13_keras_training_dry_run.png`
- `06_sprint_2_13_keras_training_completed.png`
- `07_sprint_2_13_keras_evaluation_completed.png`
- `08_sprint_2_13_tflite_conversion_completed.png`
- `09_sprint_2_13_tflite_test_completed.png`
- `10_sprint_2_13_prediction_A.png`
- `11_sprint_2_13_prediction_payment.png`
- `12_sprint_2_13_prediction_document.png`
- `13_sprint_2_13_prediction_signature.png`
- `14_sprint_2_13_prediction_atm.png`
- `15_sprint_2_13_flutter_assets_created.png`

## Acceptance Criteria

- Environment check clearly reports TensorFlow/TFLite readiness or pending setup.
- Feature dataset has shape `(805, 756)`.
- Feature dataset split counts are 558 train, 86 validation, and 161 test.
- Keras model uses validation split only for model selection.
- Keras test evaluation is reported separately.
- Float32 TFLite model is exported.
- Dynamic range TFLite export is attempted and reported.
- TFLite test accuracy is close to Keras model accuracy.
- Flutter asset folder contains TFLite model, labels, label mapping, label groups, and metadata.

## Next Sprint

Sprint 2.14 should integrate the exported TFLite assets into Flutter. Do not start Flutter integration until Sprint 2.13 training, conversion, and TFLite testing are confirmed.

## Final Status

Sprint 2.13 was completed successfully. The TensorFlow/TFLite environment passed, the 756-feature dataset was created and verified, the Keras model was trained and evaluated, both float32 and dynamic range TFLite models were exported, TFLite testing passed, and Flutter model assets were staged for the next sprint. Sprint 2.14 has not started yet.

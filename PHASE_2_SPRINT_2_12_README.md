# Phase 2 Sprint 2.12: Expanded V2 Dataset, Baseline Training, and Accuracy Comparison

## Sprint Goal

Sprint 2.12 extracts landmarks for the completed Sprint 2.11 recordings, prepares the expanded 805-sample V2 dataset, trains and evaluates a scikit-learn baseline model, and reports whether accuracy changed after adding 30 more banking intents.

## What This Sprint Does

- Uses the completed V2 vocabulary with 86 labels.
- Extracts MediaPipe Tasks two-hand landmarks into the existing `ml/data_processed/landmarks` structure.
- Prepares `signsync_expanded_v2_2hand_60f.npz`.
- Trains LogisticRegression, RandomForestClassifier, and ExtraTreesClassifier baselines.
- Selects the best model using validation data only.
- Evaluates the selected model using the held-out test split only.
- Compares Sprint 2.12 accuracy with the Sprint 2.10 V1 baseline.
- Analyzes weak or confusing labels after evaluation.

## What This Sprint Does Not Do

- Record new videos.
- Modify or delete raw videos.
- Modify the V1 dataset or Sprint 2.10 model outputs.
- Convert to TensorFlow Lite.
- Create Flutter files.
- Start Sprint 2.13.

## Expanded Dataset Expected Shape

- Labels: 86
- Samples: 805
- `X`: `(805, 60, 126)`
- `mask`: `(805, 60, 2)`
- `y`: `(805,)`
- Normal Mode V2: 76 labels
- Number Mode: 10 labels

## Split Strategy

- Trial labels with 5 repetitions: R01-R03 train, R04 validation, R05 test
- Ten-repetition labels: R01-R07 train, R08 validation, R09-R10 test
- Expected train samples: 558
- Expected validation samples: 86
- Expected test samples: 161

## Label Rules

- `payment` included
- `receipt` excluded
- `document` included
- `signature` included
- `transaction_history` excluded
- `dispute_transaction` excluded

## Commands

Run these commands from the project root.

```powershell
python -m py_compile ml/src/expanded_dataset_config.py ml/src/extract_expanded_landmarks.py ml/src/check_expanded_landmark_dataset.py ml/src/analyze_expanded_landmark_quality.py ml/src/prepare_expanded_training_dataset.py ml/src/check_expanded_training_dataset.py ml/src/expanded_model_feature_utils.py ml/src/train_expanded_baseline_model.py ml/src/evaluate_expanded_baseline_model.py ml/src/analyze_expanded_weak_labels.py ml/src/predict_expanded_sample.py

python ml/src/extract_expanded_landmarks.py --participant P02 --dry-run

python ml/src/extract_expanded_landmarks.py --participant P02

python ml/src/check_expanded_landmark_dataset.py --participant P02

python ml/src/analyze_expanded_landmark_quality.py --participant P02

python ml/src/prepare_expanded_training_dataset.py --participant P02 --dry-run

python ml/src/prepare_expanded_training_dataset.py --participant P02

python ml/src/check_expanded_training_dataset.py --participant P02

python ml/src/train_expanded_baseline_model.py --dry-run

python ml/src/train_expanded_baseline_model.py --overwrite

python ml/src/evaluate_expanded_baseline_model.py

python ml/src/analyze_expanded_weak_labels.py

python ml/src/predict_expanded_sample.py --sample-id P02_A_R01
python ml/src/predict_expanded_sample.py --sample-id P02_payment_R01
python ml/src/predict_expanded_sample.py --sample-id P02_document_R01
python ml/src/predict_expanded_sample.py --sample-id P02_signature_R01
python ml/src/predict_expanded_sample.py --sample-id P02_atm_R01
```

## Evidence Screenshot Names

- `01_sprint_2_12_expanded_landmark_extraction_dry_run.png`
- `02_sprint_2_12_expanded_landmark_extraction_completed.png`
- `03_sprint_2_12_expanded_landmark_verification_passed.png`
- `04_sprint_2_12_expanded_landmark_quality_passed.png`
- `05_sprint_2_12_expanded_dataset_preparation_completed.png`
- `06_sprint_2_12_expanded_training_dataset_verification_passed.png`
- `07_sprint_2_12_expanded_training_dry_run_passed.png`
- `08_sprint_2_12_expanded_model_training_completed.png`
- `09_sprint_2_12_expanded_model_evaluation_completed.png`
- `10_sprint_2_12_weak_label_analysis_completed.png`
- `11_sprint_2_12_prediction_A.png`
- `12_sprint_2_12_prediction_payment.png`
- `13_sprint_2_12_prediction_document.png`
- `14_sprint_2_12_prediction_signature.png`
- `15_sprint_2_12_prediction_atm.png`

## Accuracy Comparison

Sprint 2.10 V1 baseline reference:

- Test accuracy: approximately 0.9208
- Macro F1: approximately 0.9012

Sprint 2.12 expanded V2 result:

- Best model: ExtraTreesClassifier
- Validation accuracy: 0.9535
- Validation macro F1: 0.9419
- Held-out test accuracy: 0.9441
- Held-out test macro F1: 0.9256
- Held-out weighted F1: 0.9329
- Accuracy change from Sprint 2.10: +0.0233
- Macro F1 change from Sprint 2.10: +0.0244

Adding the 30 banking intents did not reduce controlled-test accuracy. The result remains a controlled single-participant baseline, not production accuracy.

## Weak Label Summary

Weak or confusing labels found: 9.

- E confused with J
- H
- N confused with M
- V confused with U
- 3 confused with H
- account confused with savings
- block_card confused with replace_card
- help confused with signature
- confirm confused with email_address

Extra recording is not recommended now. Any weak-label recording should be delayed until after mobile/Flutter testing confirms a real live-recognition issue.

## Acceptance Criteria

- Expanded landmark extraction completes for 805 expected samples.
- Expanded landmark check passes.
- Expanded landmark quality analysis passes structurally.
- Expanded dataset file has shape `(805, 60, 126)`.
- Expanded mask file has shape `(805, 60, 2)`.
- Split counts are 558 train, 86 validation, and 161 test.
- Model training selects a best scikit-learn baseline using validation only.
- Evaluation reports test accuracy, macro F1, weighted F1, per-label metrics, and a confusion matrix.
- Weak-label analysis recommends whether Sprint 2.13 is needed.

## Next Step

Sprint 2.13 should focus on final model export and TensorFlow Lite preparation. If the scikit-learn ExtraTrees model cannot be converted directly to TFLite, train a TensorFlow/Keras model using the expanded V2 dataset, evaluate it against the Sprint 2.12 baseline, then export a mobile-compatible model and metadata for Flutter.

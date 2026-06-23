# SignSync Phase 2 Audit Report: Sprints 2.1 to 2.10

## Overall Audit Status
**PASS**. The Phase 2 implementation through Sprint 2.10 is structurally complete, the current scoped dataset and baseline artifacts pass their verification checks, and the project is ready to begin Sprint 2.11 planning after the current outputs are committed to version control.

## Scope Audited
- Project: SignSync - A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions.
- Current vocabulary: 56 labels.
- Current full dataset participant: P02.
- Audit boundary: checking and reporting only. No videos were recorded, moved, deleted, re-extracted, retrained, or converted during this audit.

## Sprint Status Summary
| Sprint | Status | Main Output | Evidence Found |
| --- | --- | --- | --- |
| 2.1 | PASS | Project structure and 56-label scope | Setup README, labels module, metadata file, scope summary, screenshots |
| 2.2 | PASS | Safe raw video collection tool | `collect_video.py`, collection summary, screenshots |
| 2.3 | PASS | 55-video P02 trial collection | Trial command/plan/check reports and screenshots |
| 2.4 | PASS | Two-hand MediaPipe landmark extraction | Tasks API model, extraction/check reports, screenshots |
| 2.5 | PASS | Trial ML-ready dataset preparation | Trial dataset, label mapping, split CSV, preparation/check reports |
| 2.6 | PASS | Trial baseline model | Saved model, label names, training/evaluation reports, confusion matrix |
| 2.7 | PASS | Pipeline validation and full recording plan | Input, prediction, limitation, remaining-label, and readiness reports |
| 2.8 | PASS | Full remaining-label video collection | 450-video collection check, rework evidence, screenshot |
| 2.9 | PASS | Full landmark extraction | 505-output landmark check, extraction report, five screenshots |
| 2.10 | PASS | Full training dataset and baseline model | 505-sample dataset, mode metadata, Extra Trees model, reports, eight screenshots |

## Audit Verification Commands Run
```powershell
python -m py_compile ml/src/labels.py ml/src/collect_video.py ml/src/check_full_collection_dataset.py ml/src/check_full_landmark_dataset.py ml/src/check_full_training_dataset.py ml/src/predict_full_sample.py
python ml/src/check_full_collection_dataset.py --participant P02
python ml/src/check_full_landmark_dataset.py --participant P02
python ml/src/check_full_training_dataset.py --participant P02
python ml/src/predict_full_sample.py --sample-id P02_A_R01
python ml/src/predict_full_sample.py --sample-id P02_payment_R01
python ml/src/predict_full_sample.py --sample-id P02_7_R01
```

## Verification Output Summary
- Syntax compilation: PASS.
- Sprint 2.8 collection check: PASS, 45 labels, 10 repetitions each, 450 expected videos, 0 missing, 0 duplicates.
- Sprint 2.9 landmark check: PASS, 505 raw videos, 505 landmark outputs, 505 mask outputs, 0 failed/missing/invalid, 0 duplicate metadata IDs.
- Sprint 2.10 training dataset check: PASS, 17 of 17 checks passed.
- Predictions: `P02_A_R01`, `P02_payment_R01`, and `P02_7_R01` all predicted their true labels correctly with reported confidence 1.0000.

## Dataset Counts
- Alphabet labels: 26.
- Digit labels: 10.
- Banking intent labels: 20.
- Total labels: 56.
- Raw videos: 505.
- Landmark files: 505.
- Mask files: 505.
- Prepared samples: 505.
- Prepared tensor shapes: `X = (505, 60, 126)`, `mask = (505, 60, 2)`, `y = (505,)`.
- Train/validation/test split: 348/56/101.

## Vocabulary And Mode Metadata
- `payment` is included in the vocabulary, full dataset, and Normal Mode group.
- `receipt` is excluded from the vocabulary and expected full dataset scope.
- `normal_mode` contains the 26 alphabet labels plus 20 banking intent labels (46 labels).
- `number_mode` contains the 10 digit labels.
- `all_labels` contains all 56 current labels.

## Baseline Model Results
- Selected model: `ExtraTreesClassifier`.
- Validation accuracy: 0.9821.
- Validation macro F1: 0.9762.
- Held-out test accuracy: 0.9208.
- Held-out test macro F1: 0.9012.
- Held-out test weighted F1: 0.9102.
- Evidence: Sprint 2.10 training/evaluation reports and confusion matrix CSV/PNG.

## Evidence Files Confirmed
- Sprint 2.8 full collection check: `sprint_2_8_full_collection_check.md`.
- Sprint 2.9 full landmark check: `sprint_2_9_full_landmark_check.md`.
- Sprint 2.10 quality report: `sprint_2_10_full_landmark_quality_report.md`.
- Sprint 2.10 dataset preparation report: `sprint_2_10_full_dataset_preparation_report.md`.
- Sprint 2.10 training dataset check: `sprint_2_10_full_training_dataset_check.md`.
- Sprint 2.10 training/evaluation reports: `sprint_2_10_training_report.md`, `sprint_2_10_evaluation_report.md`.
- Sprint 2.10 confusion matrix: `sprint_2_10_confusion_matrix.csv` and `sprint_2_10_confusion_matrix.png`.
- Sprint 2.10 prediction screenshots: `06_sprint_2_10_prediction_A.png`, `07_sprint_2_10_prediction_payment.png`, and `08_sprint_2_10_prediction_7.png`.

## Risks And Limitations
- The current dataset uses one participant (P02), so it is a controlled single-participant baseline rather than a real-world generalization result.
- Environmental, lighting, background, device, and cross-participant variation remain limited.
- Mobile/Flutter integration and on-device testing are still pending.
- Adding 30 more banking intents in Sprint 2.11 may change class separability and reduce measured accuracy; the dataset and model will need renewed validation.
- Git housekeeping remains: Sprint 2.9 and Sprint 2.10 generated reports, screenshots, model metadata, and source files should be reviewed and committed without adding raw videos, landmark arrays, `.npz` datasets, or model binaries.

## Final Recommendation
**Yes.** It is safe to move to Sprint 2.11, provided Sprint 2.11 begins as a new scoped vocabulary/data-collection change and the current Sprint 2.9/2.10 source and evidence artifacts are committed first. The present model metrics should continue to be described as a controlled single-participant baseline, not production accuracy.

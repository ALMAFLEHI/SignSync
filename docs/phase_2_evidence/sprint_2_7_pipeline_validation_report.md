# Sprint 2.7 Saved Model Pipeline Validation Report

## Result
The saved Sprint 2.6 model loaded successfully and produced predictions after loading. The pipeline from the Sprint 2.5 dataset, through the Sprint 2.6 saved model, to prediction is working.

| Split | Samples | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted Precision | Weighted Recall | Weighted F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 33 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| validation | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| test | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| all | 55 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Important Limitation
The high score validates the stored trial pipeline, but it must not be claimed as production accuracy. The current dataset is small, contains only trial labels, and has no cross-participant evaluation.

## Output Files
- Metrics CSV: docs/phase_2_evidence/sprint_2_7_pipeline_validation_report.csv
- Prediction check CSV: docs/phase_2_evidence/sprint_2_7_prediction_check_report.csv

# Sprint 2.7 Trial Dataset Limitation Report

## Dataset Summary
- Total samples: 55
- Labels: 11
- Participants: 1 (P02)
- Train/validation/test samples: 33/11/11
- One test sample per class: yes
- Production accuracy claim supported: no

## Samples and Repetitions Per Label
| Label | Samples | Unique repetitions |
| --- | ---: | ---: |
| 0 | 5 | 5 |
| 1 | 5 | 5 |
| 2 | 5 | 5 |
| A | 5 | 5 |
| B | 5 | 5 |
| C | 5 | 5 |
| balance | 5 | 5 |
| confirm | 5 | 5 |
| deposit | 5 | 5 |
| help | 5 | 5 |
| withdraw | 5 | 5 |

## Why the 100% Trial Result Is Limited
- Small sample size: the trial dataset contains only 55 samples.
- Same participant: all trial samples are from one participant (P02).
- Limited environmental variation: recordings do not represent varied cameras, rooms, or capture conditions.
- Limited lighting and background variation: the trial data is not designed to test robustness to those changes.
- No cross-participant test has been performed.
- No full label coverage yet: only 11 of the 56 scoped labels are present.
- Trial labels only: the saved model was trained and evaluated on the early trial vocabulary.
- One test sample per class: an 11-sample test split cannot establish final production accuracy.

## Conclusion
Sprint 2.6 validates the machine learning pipeline, but the current result should not be interpreted as final production accuracy. More samples, more labels, and ideally more participants are required before final model evaluation.

## Output Files
- JSON report: docs/phase_2_evidence/sprint_2_7_dataset_limitation_report.json
- Markdown report: docs/phase_2_evidence/sprint_2_7_dataset_limitation_report.md

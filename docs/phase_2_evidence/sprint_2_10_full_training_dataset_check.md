# Sprint 2.10 Full Training Dataset Check

## Result
PASS

## Checks
| Check | Status | Detail |
| --- | --- | --- |
| X shape | PASS | (505, 60, 126) |
| mask shape | PASS | (505, 60, 2) |
| y shape | PASS | (505,) |
| label count | PASS | 56 |
| payment included | PASS | True |
| receipt excluded | PASS | True |
| unique sample IDs | PASS | 505 |
| finite landmark values | PASS | no NaN or infinity |
| split CSV exists | PASS | ml/data_processed/datasets/signsync_full_v1_splits.csv |
| split CSV count | PASS | 505 |
| train split count | PASS | 348 |
| validation split count | PASS | 56 |
| test split count | PASS | 101 |
| dataset split counts | PASS | {np.str_('train'): 348, np.str_('val'): 56, np.str_('test'): 101} |
| split sample ID match | PASS | matches dataset |
| every label has train/val/test samples | PASS | all 56 labels represented |
| label groups JSON | PASS | all_labels, normal_mode, number_mode |

## Failed Checks
- None

## Report Files
- CSV report: docs/phase_2_evidence/sprint_2_10_full_training_dataset_check.csv
- Markdown report: docs/phase_2_evidence/sprint_2_10_full_training_dataset_check.md

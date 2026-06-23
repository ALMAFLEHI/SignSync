# Sprint 2.10 Full Dataset Preparation and Baseline Plan

## Goal
Prepare the verified 505-sample landmark dataset for machine learning and define a current scikit-learn baseline workflow without using TensorFlow, TFLite, Flutter, or Sprint 2.11 work.

## Expected Dataset
- Samples: 505.
- Labels: 56.
- Landmark tensor: `X = 505 x 60 x 126`.
- Hand-mask tensor: `mask = 505 x 60 x 2`.
- Class IDs: `y = 505`.
- `payment` included; `receipt` excluded.

## Split Strategy
Repetition-based splitting prevents random leakage between recordings of the same sign.

- Trial labels, 5 repetitions: R01-R03 train, R04 validation, R05 test.
- Full collection labels, 10 repetitions: R01-R07 train, R08 validation, R09-R10 test.
- Expected train/validation/test counts: 348/56/101.

## Mode Metadata
The dataset saves mode groups for future Flutter integration:
- `normal_mode`: alphabet plus banking intent labels.
- `number_mode`: digits only.
- `all_labels`: all 56 current labels.

## Baseline Workflow
- Statistical features: mean, standard deviation, minimum, maximum, first frame, and last frame.
- Feature width: 756.
- Candidates: Logistic Regression, Random Forest, and Extra Trees.
- Model selection uses validation data only.
- Final evaluation uses the test split only.

## Safety Boundaries
- Original raw videos and landmark files remain unchanged.
- Full dataset preparation and training require explicit confirmation.
- No TensorFlow, TFLite, Flutter, new recordings, or Sprint 2.11 work is included.

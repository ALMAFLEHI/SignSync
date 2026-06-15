# SignSync Sprint 2.5 Dataset Preparation Plan

## Project Name
SignSync: A Real-Time, On-Device ASL-to-Text Recognition Framework for Privacy-Preserving Banking Service Interactions

## Sprint Name
Phase 2, Sprint 2.5: Dataset Cleaning and Training Data Preparation

## Sprint Goal
Prepare the extracted two-hand landmark data from Sprint 2.4 into a clean machine-learning-ready dataset for Sprint 2.6 model training.

## Input Data
- Participant: `P02`
- Trial samples: 55
- Trial labels: `A`, `B`, `C`, `0`, `1`, `2`, `deposit`, `withdraw`, `balance`, `help`, `confirm`
- Metadata source: `ml/metadata.csv`
- Landmark source: `ml/data_processed/landmarks/[label]/`

## Output Dataset Format
The prepared dataset will be saved as:

```text
ml/data_processed/datasets/signsync_trial_v1_2hand_60f.npz
```

The `.npz` file contains:
- `X`
- `y`
- `sample_ids`
- `labels`
- `label_names`
- `splits`
- `target_frames`
- `landmark_dim`

## Landmark Input Shape
Each Sprint 2.4 landmark file is expected to use:

```text
number_of_frames x 126
```

Each Sprint 2.4 mask file is expected to use:

```text
number_of_frames x 2
```

## Standardized Training Shape
Each sample is standardized to:

```text
60 x 126
```

The full dataset shape is expected to be:

```text
55 x 60 x 126
```

## Label Mapping Rule
Labels are mapped using the stable trial label order from `ml/src/trial_config.py`:

```text
A, B, C, 0, 1, 2, deposit, withdraw, balance, help, confirm
```

## Split Rule
Because each class has 5 samples:

- `R01`, `R02`, `R03` are assigned to `train`
- `R04` is assigned to `val`
- `R05` is assigned to `test`

Expected split totals:

- Train: 33 samples
- Validation: 11 samples
- Test: 11 samples

## Quality Check Rule
A landmark sample passes quality checks if:

- landmark file exists
- mask file exists
- landmark shape is valid
- mask shape is valid
- frame counts match
- no NaN values exist
- no infinite values exist
- any-hand detection rate is at least `0.80`

## Acceptance Criteria
- [ ] Landmark quality check passes.
- [ ] Dataset preparation dry-run passes.
- [ ] Training dataset `.npz` is created.
- [ ] `X` shape is `55 x 60 x 126`.
- [ ] `y` shape is `55`.
- [ ] 11 labels are mapped correctly.
- [ ] Train/validation/test splits are created.
- [ ] Dataset verification passes.
- [ ] Reports are generated.
- [ ] No model training is created.
- [ ] No Flutter integration is created.

## What This Sprint Does Not Include
- No raw video recording.
- No landmark extraction.
- No model training.
- No TensorFlow Lite conversion.
- No Flutter integration.
- No Sprint 2.6 work.

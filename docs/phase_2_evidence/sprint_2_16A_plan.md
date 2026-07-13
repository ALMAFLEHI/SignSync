# Sprint 2.16A Plan

## Goal

Use the approved 76-class V3 scope for future dataset preparation while preserving the historical 86-class workflow. Improve four retained weak banking labels using phone-camera landmark samples.

## Completed Setup

- Versioned the historical 50-intent/86-class V2 scope.
- Added the active 40-intent/76-class V3 scope.
- Excluded exactly 10 approved labels from future training without deleting data.
- Restricted Flutter Banking Intent Mode to the active 40 labels while retaining 86 raw model outputs for debugging.
- Revised the phone pilot to `transfer`, `document`, `signature`, and `atm`.
- Prepared validation and future mixed-dataset scripts.

## Controlled Experiment Completed

The controlled experiment used 25 phone samples per pilot label, for 100 total. The samples passed detailed validation and were split deterministically into 60 training, 20 validation, and 20 untouched test samples. Active historical data and real phone data were combined into an 805-sample, 76-class dataset.

The unchanged 86-class baseline, Experiment A without augmentation, and Experiment B with conservative training-only augmentation were evaluated. Experiment B is the offline recommendation: 95% phone test accuracy, 0.9722 phone macro F1, 0.9193 full active test accuracy, and no high-confidence wrong phone predictions. Both new TFLite variants passed the `[1, 756]` to `[1, 76]` contract and Keras parity checks.

## Reviewed Deployment Completed

Experiment B was reviewed and deployed with its matching 76-class metadata after a non-overwriting backup of the previous 86-class assets. Contract, parity, Flutter, and Android debug build checks passed.

## Pending Live Test

Execute and review the 65 fresh stabilized attempts in `sprint_2_16A_live_A55_test_plan.md`. Sprint 2.16A remains open until the selected model is tested live on the Samsung Galaxy A55. Sprint 2.16B and Sprint 2.17 remain blocked.

# Phase 2, Sprint 2.16A: Phone-Camera Weak Label Dataset Pilot and Accuracy Improvement Setup

## Sprint Status

Setup complete. Waiting for the user to record and pull phone-camera landmark samples before retraining.

## Goal

Sprint 2.16A starts a controlled improvement loop for five weak banking-intent labels found during Sprint 2.15 live phone testing.

Target weak labels:

- `transfer`
- `address_change`
- `document`
- `signature`
- `atm`

## What Was Added

- Confidence thresholds:
  - Alphabet Mode: 0.65
  - Number Mode: 0.60
  - Banking Intent Mode: 0.70
- Top-2 confidence gap check: 0.15
- Try Again output for low-confidence or ambiguous predictions
- 3-capture majority vote stabilization
- Phone Dataset Collection page in Flutter
- Local JSON landmark sample saving
- Python validation/import/dataset setup scripts
- Sprint 2.16A evidence reports

## Phone Sample Workflow

In Flutter:

1. Open `Phone Dataset Collection`.
2. Select one weak label.
3. Start camera.
4. Capture and save a 60-frame sample.
5. Repeat until each weak label has 20 samples.

Android save path:

```text
/storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples/
```

Pull samples to PC:

```powershell
adb pull /storage/emulated/0/Android/data/com.example.flutter_app/files/signsync_phone_samples "D:\SWE  MOODLE\Year 3 Semester 2\FYP Part 2\SignSync\ml\data_phone\landmark_samples"
```

## Python Commands

```powershell
python ml/src/check_phone_landmark_samples.py
python ml/src/import_phone_landmark_samples.py
python ml/src/prepare_phone_augmented_dataset.py --participant P02_PHONE
python ml/src/check_phone_augmented_dataset.py
```

## Current Limitation

No phone samples exist in `ml/data_phone/landmark_samples/` yet. Therefore:

- mixed dataset creation is pending
- retraining is pending
- TFLite export is pending
- Flutter model asset update is pending
- live weak-label retest is pending

## Scope Confirmation

- old laptop-camera dataset kept
- no old data deleted
- no fake samples created
- no raw video saved
- no cloud/server processing
- no Sprint 2.16B work
- no Sprint 2.17 work
- no 100% accuracy claim

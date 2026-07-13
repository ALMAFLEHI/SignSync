# Phase 2, Sprint 2.16A: Active Scope Revision and Phone Dataset Pilot

## Status

Scope revision complete. Waiting for manual phone-camera landmark recording before mixed-dataset creation and retraining.

## Active Vocabulary

- Alphabet labels: 26
- Digit labels: 10
- Banking intents: 40
- Future model classes: 76
- Historical model classes: 86

The 50-intent V2 vocabulary, historical datasets, mappings, models, and evidence remain preserved. Ten banking intents are excluded only from the active V3 scope and future training.

## Revised Phone Pilot

Record at least 20 phone landmark samples for each retained weak label:

- `transfer`
- `document`
- `signature`
- `atm`

Minimum total: 80 samples. Each JSON sample uses participant `P02_PHONE`, source `phone_live_landmark`, 60 frames, and 126 values per frame. No raw video is saved.

## Workflow

1. Open `Phone Dataset Collection` in the Android app.
2. Record 20 or more samples for each of the four labels.
3. Pull the JSON files to `ml/data_phone/landmark_samples/`.
4. Run:

```powershell
python ml/src/check_active_scope_v3.py
python ml/src/check_phone_landmark_samples.py
python ml/src/import_phone_landmark_samples.py
python ml/src/prepare_phone_augmented_dataset.py --participant P02_PHONE
python ml/src/check_phone_augmented_dataset.py
```

The future dataset is `signsync_scope_v3_40_phone_pilot_v1_2hand_60f.npz`. The future model contract is `[1, 756]` input and `[1, 76]` output. The current Flutter model and metadata remain 86-class until a validated 76-class model is trained and exported.

## Boundaries

No historical data was deleted, no fake samples were generated, no retraining or TFLite conversion was performed, and Sprint 2.16B/2.17 were not started.

# Sprint 2.15 Live Inference Report

## Inference Scope

Sprint 2.15 reuses the Sprint 2.13 TFLite model assets already integrated in Sprint 2.14:

- `model_dynamic_range.tflite`
- `model_float32.tflite`
- `labels.txt`
- `label_mapping.json`
- `label_groups.json`
- `tflite_model_metadata.json`

No model retraining or reconversion was performed.

## Live Inference Flow

1. Android native code streams 126-value MediaPipe landmark frames.
2. Flutter collects 60 valid frames.
3. Flutter feature engine computes 756 statistical features.
4. Existing TFLite classifier runs `[1, 756]` input.
5. UI displays prediction, confidence, raw output length, selected mode, and top predictions.
6. Alphabet Mode, Number Mode, and Banking Intent Mode filter the displayed final prediction.

## Three Recognition Modes

- Alphabet Mode: final prediction is selected only from A-Z.
- Number Mode: final prediction is selected only from 0-9.
- Banking Intent Mode: final prediction is selected only from banking intent labels.

Raw model top predictions remain available for debugging. This is useful because high-confidence wrong raw predictions were observed during phone testing.

## Samsung Phone Test Results

Small representative set tested:

- `A`: correct, 77.92% confidence
- `7`: correct, 60.14% confidence
- `deposit`: correct, 91.75% confidence
- `payment`: correct, 99.44% confidence, but needed retry
- `balance`: correct, 81.35% confidence
- `transfer`: failed 3 attempts, often predicted `Z`
- `address_change`: mixed result, correct once and failed other attempts; sometimes predicted `transfer` with around 97% confidence
- `document`: failed
- `signature`: mixed result, correct once and failed other attempts
- `atm`: failed

## Weak Labels Identified

The weak/confusing labels discovered in Sprint 2.15 were:

- `transfer`
- `address_change`
- `document`
- `signature`
- `atm`

## Runtime Metrics Added

The live camera page records:

- 60-frame capture duration
- approximate capture FPS
- feature computation time
- TFLite inference time
- end-to-end prediction time

## Accuracy Interpretation

Sprint 2.15 is complete for live pipeline implementation and limited real-phone validation. The sprint does not claim perfect accuracy. Full banking intent testing was not done, and high-confidence wrong predictions were observed.

Accuracy improvement and phone-camera dataset expansion are deferred to Sprint 2.16.

## Privacy Confirmation

The implemented Sprint 2.15 pipeline is on-device:

- no video upload
- no server inference
- no cloud processing
- no network call for recognition

The camera frame, landmark extraction, feature computation, and TFLite inference all remain local to the Android app.

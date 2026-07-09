# Sprint 2.16A Plan

## Goal

Sprint 2.16A is a phone-camera weak-label pilot for SignSync. The goal is to improve live demo reliability without replacing or deleting the existing laptop-camera dataset.

## Scope

- Improve Flutter live prediction robustness.
- Add confidence thresholds per recognition mode.
- Add top-2 gap checking.
- Add a simple 3-capture majority-vote stabilization workflow.
- Add a phone-camera landmark JSON collection page.
- Add Python scripts to validate, import, and prepare a mixed laptop + phone dataset.
- Keep the model output contract at `[1, 86]`.

## Weak Labels

Exactly five labels are targeted:

- `transfer`
- `address_change`
- `document`
- `signature`
- `atm`

Minimum target: 20 phone-camera landmark samples per weak label, 100 total.

## Phone Sample Strategy

Samples are captured on the Samsung Android phone as landmark JSON only. No raw video is saved. Each sample contains 60 frames and 126 landmark values per frame.

Participant/source:

- participant: `P02_PHONE`
- source: `phone_live_landmark`
- device: `Samsung Android phone`

## Model Improvement Strategy

Once enough phone samples are pulled to `ml/data_phone/landmark_samples/`, the Python pipeline will combine:

- old laptop-camera expanded dataset
- new phone-camera weak-label samples

Retraining and TFLite export are pending until valid phone samples exist. No fake samples are created.

## Hand Ordering Note

The Android bridge returns 126 values in a fixed layout:

- values `0-62`: left hand
- values `63-125`: right hand

MediaPipe handedness is used first. If handedness is missing, detections fall back to normalized average x-position. Missing hand slots are zero-filled. Frames with no hands are not added to the 60-frame buffer.

This matches the previous Python layout as closely as possible, with the known limitation that live front-camera mirroring and MediaPipe handedness may not always be identical to laptop-video extraction.

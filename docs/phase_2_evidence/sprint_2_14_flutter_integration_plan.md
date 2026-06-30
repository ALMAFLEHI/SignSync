# Sprint 2.14 Flutter Integration Plan

## Objective

Build a Flutter prototype that loads Sprint 2.13 TFLite assets and validates local inference using exported 756-feature test samples.

## Scope

- Create or update `flutter_app`.
- Copy model and metadata assets into Flutter.
- Export fixed test feature JSON samples.
- Add Flutter services for metadata loading, TFLite inference, mode filtering, feature computation, and test sample loading.
- Add a simple UI for offline test feature inference.

## Out of Scope

- Live camera recognition.
- MediaPipe mobile integration.
- New recordings.
- Raw video changes.
- Model retraining or reconversion.
- Sprint 2.15 implementation.

## Mode Filtering

The model outputs all 86 class probabilities. The app filters the final displayed prediction by mode:

- Normal Mode: alphabet labels and banking intents only.
- Number Mode: digits `0` to `9` only.

Raw top predictions are still available in the UI for debugging.

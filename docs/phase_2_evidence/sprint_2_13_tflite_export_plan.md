# Sprint 2.13 TFLite Export Plan

## Goal

Create a TensorFlow/Keras model and TensorFlow Lite export path for the completed SignSync expanded V2 dataset.

## Why This Sprint Is Needed

The Sprint 2.12 ExtraTreesClassifier baseline achieved strong controlled accuracy, but it is not a direct mobile/TFLite deployment target. Sprint 2.13 prepares a model format that can be used later by the Flutter app.

## Model Strategy

Use the same 756 statistical features as the scikit-learn baseline:

- mean
- standard deviation
- minimum
- maximum
- first frame
- last frame

Each sample starts as `(60, 126)` landmarks and becomes a `(756,)` float32 feature vector.

## TFLite Contract

- Input shape: `[1, 756]`
- Input dtype: `float32`
- Output shape: `[1, 86]`
- Output dtype: `float32`
- Output meaning: softmax probabilities over the 86 V2 labels

## Label and Mode Metadata

- Total labels: 86
- Normal Mode: 76 labels
- Number Mode: 10 labels
- `payment` included
- `receipt` excluded
- `document` included
- `signature` included
- `transaction_history` excluded
- `dispute_transaction` excluded

## Scope Boundary

Sprint 2.13 does not record videos, modify raw videos, create Flutter UI files, start mobile testing, or start Sprint 2.14.

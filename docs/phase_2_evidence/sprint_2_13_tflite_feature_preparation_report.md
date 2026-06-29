# Sprint 2.13 TFLite Feature Preparation Report

## Summary
- Source dataset: ml/data_processed/datasets/signsync_expanded_v2_2hand_60f.npz
- Source X shape: (805, 60, 126)
- Feature dataset: ml/data_processed/datasets/signsync_expanded_v2_stats_756f.npz
- X_features shape: (805, 756)
- y shape: (805,)
- Feature order: mean, std, min, max, first_frame, last_frame
- Train/validation/test: 558/86/161
- Normal Mode labels: 76
- Number Mode labels: 10

## Flutter Note
The Flutter app must collect 60 frames of 126-value landmarks, compute the same 756 statistical features, and pass a float32 tensor shaped `[1, 756]` to the TFLite model.

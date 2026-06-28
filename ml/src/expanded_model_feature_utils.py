"""Statistical feature extraction for the Sprint 2.12 expanded scikit-learn baselines."""

from __future__ import annotations

import numpy as np

from expanded_dataset_config import LANDMARK_DIMENSION, TARGET_FRAMES


FEATURE_MODE = "stats"
STATS_FEATURE_MULTIPLIER = 6
STATS_FEATURE_SIZE = LANDMARK_DIMENSION * STATS_FEATURE_MULTIPLIER


def create_statistical_features(X: np.ndarray) -> np.ndarray:
    """Convert sequences from samples x 60 x 126 into 756 fixed statistics."""
    if X.ndim != 3 or X.shape[1:] != (TARGET_FRAMES, LANDMARK_DIMENSION):
        raise ValueError(
            "Expected sequence data shaped samples x "
            f"{TARGET_FRAMES} x {LANDMARK_DIMENSION}, found {X.shape}."
        )
    features = np.concatenate(
        [
            X.mean(axis=1),
            X.std(axis=1),
            X.min(axis=1),
            X.max(axis=1),
            X[:, 0, :],
            X[:, -1, :],
        ],
        axis=1,
    )
    if features.shape[1] != STATS_FEATURE_SIZE:
        raise ValueError(
            f"Expected {STATS_FEATURE_SIZE} statistical features, found {features.shape[1]}."
        )
    return features.astype(np.float32, copy=False)

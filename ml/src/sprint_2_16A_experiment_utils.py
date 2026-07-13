"""Shared loading, feature, and augmentation helpers for Sprint 2.16A."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from sprint_2_16A_experiment_config import (
    AUGMENTATION_CONFIG_PATH,
    FEATURE_ORDER,
    FEATURE_WIDTH,
    FRAME_WIDTH,
    PARTICIPANT_ID,
    PHONE_DEVICE_METADATA,
    PHONE_SAMPLE_DIR,
    PHONE_SOURCE,
    PILOT_LABELS,
    TARGET_FRAMES,
)


@dataclass(frozen=True)
class PhoneSequence:
    """One independently validated phone landmark sequence."""

    sample_id: str
    participant_id: str
    label: str
    repetition: int
    source: str
    device: str
    frames: np.ndarray
    path: Path
    sha256: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest without modifying the source file."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_phone_sequences(sample_dir: Path = PHONE_SAMPLE_DIR) -> list[PhoneSequence]:
    """Load all phone JSON files and enforce the controlled-pilot contract."""
    paths = sorted(path for path in sample_dir.rglob("*.json") if path.is_file())
    sequences: list[PhoneSequence] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON: {path.as_posix()}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"JSON root must be an object: {path.as_posix()}")

        sample_id = _required_str(payload, "sample_id", path)
        participant_id = _required_str(payload, "participant_id", path)
        label = _required_str(payload, "label", path)
        source = _required_str(payload, "source", path)
        device = _required_str(payload, "device", path)
        repetition = _required_int(payload, "repetition", path)
        frame_count = _required_int(payload, "frame_count", path)
        frame_width = _required_int(payload, "frame_width", path)

        if participant_id != PARTICIPANT_ID:
            raise ValueError(f"Unexpected participant in {path.as_posix()}: {participant_id}")
        if label not in PILOT_LABELS:
            raise ValueError(f"Unexpected label in {path.as_posix()}: {label}")
        if source != PHONE_SOURCE:
            raise ValueError(f"Unexpected source in {path.as_posix()}: {source}")
        if device != PHONE_DEVICE_METADATA:
            raise ValueError(f"Unexpected device metadata in {path.as_posix()}: {device}")
        expected_id = f"{PARTICIPANT_ID}_{label}_R{repetition:02d}"
        if sample_id != expected_id or path.stem != expected_id:
            raise ValueError(
                f"Sample ID/file mismatch for {path.as_posix()}: expected {expected_id}"
            )
        if frame_count != TARGET_FRAMES or frame_width != FRAME_WIDTH:
            raise ValueError(
                f"Invalid declared shape for {sample_id}: {frame_count} x {frame_width}"
            )

        raw_frames = payload.get("frames")
        if not isinstance(raw_frames, list) or not raw_frames:
            raise ValueError(f"Frames must be a non-empty list for {sample_id}")
        if len(raw_frames) != TARGET_FRAMES:
            raise ValueError(f"Expected {TARGET_FRAMES} frames for {sample_id}")
        frames = np.asarray(raw_frames, dtype=np.float64)
        if frames.shape != (TARGET_FRAMES, FRAME_WIDTH):
            raise ValueError(f"Unexpected sequence shape for {sample_id}: {frames.shape}")
        if not np.isfinite(frames).all():
            raise ValueError(f"NaN or infinite landmark value found in {sample_id}")

        sequences.append(
            PhoneSequence(
                sample_id=sample_id,
                participant_id=participant_id,
                label=label,
                repetition=repetition,
                source=source,
                device=device,
                frames=frames,
                path=path,
                sha256=sha256_file(path),
            )
        )
    return sequences


def statistical_features(sequences: np.ndarray) -> np.ndarray:
    """Compute mean/std/min/max/first/last features with population std."""
    values = np.asarray(sequences)
    if values.ndim == 2:
        values = values[np.newaxis, ...]
        squeeze = True
    elif values.ndim == 3:
        squeeze = False
    else:
        raise ValueError(f"Expected a 2D or 3D sequence array, found {values.shape}.")
    if values.shape[1:] != (TARGET_FRAMES, FRAME_WIDTH):
        raise ValueError(
            f"Expected sequence shape (*, {TARGET_FRAMES}, {FRAME_WIDTH}), found {values.shape}."
        )
    features = np.concatenate(
        [
            values.mean(axis=1),
            values.std(axis=1, ddof=0),
            values.min(axis=1),
            values.max(axis=1),
            values[:, 0, :],
            values[:, -1, :],
        ],
        axis=1,
    )
    if features.shape[1] != FEATURE_WIDTH or not np.isfinite(features).all():
        raise ValueError("Feature extraction did not produce finite 756-value rows.")
    features = features.astype(np.float32, copy=False)
    return features[0] if squeeze else features


def load_augmentation_config() -> dict[str, Any]:
    """Load and validate the versioned conservative augmentation settings."""
    config = json.loads(AUGMENTATION_CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("config_version") != "sprint_2_16A_conservative_v1":
        raise ValueError("Unexpected Sprint 2.16A augmentation configuration version.")
    if config.get("derivatives_per_training_sample") != 1:
        raise ValueError("The pilot allows exactly one augmented derivative per train sample.")
    for disabled_key in (
        "temporal_resampling",
        "frame_masking_or_landmark_dropout",
        "horizontal_mirroring",
    ):
        if config.get(disabled_key, {}).get("enabled") is not False:
            raise ValueError(f"{disabled_key} must remain disabled for the controlled pilot.")
    return config


def augment_sequence(
    sequence: np.ndarray,
    rng: np.random.Generator,
    config: dict[str, Any],
) -> tuple[np.ndarray, dict[str, float]]:
    """Apply small spatial transforms while preserving all-zero hand slots."""
    source = np.asarray(sequence, dtype=np.float32)
    if source.shape != (TARGET_FRAMES, FRAME_WIDTH):
        raise ValueError(f"Unexpected augmentation source shape: {source.shape}")
    augmented = source.copy()

    tx = float(rng.uniform(*config["spatial_translation"]["x_range"]))
    ty = float(rng.uniform(*config["spatial_translation"]["y_range"]))
    scale = float(rng.uniform(*config["scale"]["range"]))
    angle_degrees = float(rng.uniform(*config["rotation"]["degrees_range"]))
    angle = math.radians(angle_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    sigma = float(config["coordinate_jitter"]["gaussian_sigma"])

    source_missing_masks: list[np.ndarray] = []
    for hand_start in (0, 63):
        hand_end = hand_start + 63
        source_hand = source[:, hand_start:hand_end]
        missing = np.all(source_hand == 0.0, axis=1)
        source_missing_masks.append(missing)
        for frame_index in np.flatnonzero(~missing):
            landmarks = augmented[frame_index, hand_start:hand_end].reshape(21, 3)
            wrist = landmarks[0].copy()
            centered = landmarks - wrist
            centered *= scale
            x_values = centered[:, 0].copy()
            y_values = centered[:, 1].copy()
            centered[:, 0] = cosine * x_values - sine * y_values
            centered[:, 1] = sine * x_values + cosine * y_values
            transformed = centered + wrist
            transformed[:, 0] += tx
            transformed[:, 1] += ty
            transformed += rng.normal(0.0, sigma, size=transformed.shape).astype(np.float32)
            augmented[frame_index, hand_start:hand_end] = transformed.reshape(63)
        augmented[missing, hand_start:hand_end] = 0.0

    for hand_index, hand_start in enumerate((0, 63)):
        missing = source_missing_masks[hand_index]
        if not np.all(augmented[missing, hand_start : hand_start + 63] == 0.0):
            raise ValueError("Augmentation changed a missing-hand zero block.")
    if augmented.shape != source.shape or not np.isfinite(augmented).all():
        raise ValueError("Augmentation produced an invalid sequence.")
    if np.array_equal(source, augmented):
        raise ValueError("Augmentation produced an exact duplicate.")

    return augmented, {
        "translation_x": tx,
        "translation_y": ty,
        "scale": scale,
        "rotation_degrees": angle_degrees,
        "jitter_sigma": sigma,
    }


def stable_rng(seed: int, sample_id: str) -> np.random.Generator:
    """Create a stable per-sample generator independent of file iteration order."""
    digest = hashlib.sha256(f"{seed}:{sample_id}".encode("utf-8")).digest()
    derived_seed = int.from_bytes(digest[:8], byteorder="little", signed=False)
    return np.random.default_rng(derived_seed)


def _required_str(payload: dict[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string in {path.as_posix()}")
    return value


def _required_int(payload: dict[str, Any], key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer in {path.as_posix()}")
    return value

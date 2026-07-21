"""Shared validation and artifact helpers for Sprint 2.17."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from sprint_2_16A_experiment_utils import (
    augment_sequence,
    sha256_file,
    stable_rng,
    statistical_features,
)
from sprint_2_17_config import (
    FINAL_LABELS,
    FRAME_WIDTH,
    PARTICIPANT_ID,
    PHONE_DEVICE,
    PHONE_SOURCE,
    ROOT,
    TARGET_FRAMES,
)


@dataclass(frozen=True)
class PhoneSequence:
    """One read-only validated Samsung phone landmark sequence."""

    sample_id: str
    participant_id: str
    label: str
    repetition: int
    source: str
    device: str
    frames: np.ndarray
    path: Path
    sha256: str
    sequence_sha256: str
    missing_left_frames: int
    missing_right_frames: int


def utc_now() -> str:
    """Return a stable ISO-8601 UTC timestamp for generated metadata."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def relative_path(path: Path) -> str:
    """Return a repository-relative POSIX path."""
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sequence_sha256(frames: np.ndarray) -> str:
    """Hash canonical little-endian float32 sequence content."""
    values = np.asarray(frames, dtype="<f4")
    return hashlib.sha256(values.tobytes(order="C")).hexdigest()


def load_phone_sequence(path: Path) -> PhoneSequence:
    """Load one source JSON without modifying it and enforce its contract."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {relative_path(path)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {relative_path(path)}")

    sample_id = _required_string(payload, "sample_id", path)
    participant_id = _required_string(payload, "participant_id", path)
    label = _required_string(payload, "label", path)
    source = _required_string(payload, "source", path)
    device = _required_string(payload, "device", path)
    repetition = _required_integer(payload, "repetition", path)
    frame_count = _required_integer(payload, "frame_count", path)
    frame_width = _required_integer(payload, "frame_width", path)

    if participant_id != PARTICIPANT_ID:
        raise ValueError(f"Unexpected participant for {sample_id}: {participant_id}")
    if label not in FINAL_LABELS:
        raise ValueError(f"Label is outside the frozen 40: {label}")
    if repetition not in range(1, 26):
        raise ValueError(f"Repetition is outside R01-R25 for {sample_id}.")
    if source != PHONE_SOURCE or device != PHONE_DEVICE:
        raise ValueError(f"Unexpected phone origin metadata for {sample_id}.")
    expected_id = f"{PARTICIPANT_ID}_{label}_R{repetition:02d}"
    if sample_id != expected_id or path.stem != expected_id:
        raise ValueError(f"Sample ID or filename mismatch: expected {expected_id}.")
    if frame_count != TARGET_FRAMES or frame_width != FRAME_WIDTH:
        raise ValueError(f"Invalid declared shape for {sample_id}.")

    raw_frames = payload.get("frames")
    if not isinstance(raw_frames, list) or not raw_frames:
        raise ValueError(f"Frames must be a non-empty list for {sample_id}.")
    frames = np.asarray(raw_frames, dtype=np.float32)
    if frames.shape != (TARGET_FRAMES, FRAME_WIDTH):
        raise ValueError(f"Unexpected sequence shape for {sample_id}: {frames.shape}")
    if not np.isfinite(frames).all():
        raise ValueError(f"NaN or infinity found in {sample_id}.")

    left_missing = np.all(frames[:, :63] == 0.0, axis=1)
    right_missing = np.all(frames[:, 63:] == 0.0, axis=1)
    if np.any(left_missing & right_missing):
        raise ValueError(f"A no-hand frame was retained in {sample_id}.")

    return PhoneSequence(
        sample_id=sample_id,
        participant_id=participant_id,
        label=label,
        repetition=repetition,
        source=source,
        device=device,
        frames=frames,
        path=path,
        sha256=sha256_file(path),
        sequence_sha256=sequence_sha256(frames),
        missing_left_frames=int(np.sum(left_missing)),
        missing_right_frames=int(np.sum(right_missing)),
    )


def load_phone_sequences(sample_dir: Path) -> list[PhoneSequence]:
    """Load all JSON samples in frozen label and repetition order."""
    label_order = {label: index for index, label in enumerate(FINAL_LABELS)}
    samples = [
        load_phone_sequence(path)
        for path in sample_dir.rglob("*.json")
        if path.is_file()
    ]
    return sorted(samples, key=lambda item: (label_order[item.label], item.repetition))


def write_json(path: Path, payload: Any) -> None:
    """Write readable UTF-8 JSON to a derived artifact path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2), encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write UTF-8 CSV with a stable column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV artifact."""
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def json_safe(value: Any) -> Any:
    """Convert NumPy-rich structures into JSON-safe values."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return relative_path(value)
    return value


def _required_string(payload: dict[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string in {relative_path(path)}")
    return value.strip()


def _required_integer(payload: dict[str, Any], key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer in {relative_path(path)}")
    return value


__all__ = [
    "PhoneSequence",
    "augment_sequence",
    "load_phone_sequence",
    "load_phone_sequences",
    "read_csv",
    "relative_path",
    "sequence_sha256",
    "sha256_file",
    "stable_rng",
    "statistical_features",
    "utc_now",
    "write_csv",
    "write_json",
]

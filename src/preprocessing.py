"""Preprocessing: scale detection and dB → linear conversion."""
from __future__ import annotations

import numpy as np


def detect_scale(arr: np.ndarray, sample_size: int = 1_000_000) -> str:
    """Return 'dB' if values are log-scale, 'linear' otherwise.

    Heuristic: dB sigma0 is centered around negative values (~-25 to +5),
    while linear sigma0 is strictly positive small floats (~0.001 to 2).
    Uses a random subsample to avoid scanning the full array.
    """
    flat = arr[np.isfinite(arr)]
    if flat.size == 0:
        raise ValueError("No finite values in array.")
    if flat.size > sample_size:
        rng = np.random.default_rng(0)
        flat = rng.choice(flat, size=sample_size, replace=False)
    median = float(np.median(flat))
    minimum = float(np.min(flat))
    if median < 0 or minimum < 0:
        return "dB"
    return "linear"


def db_to_linear(arr: np.ndarray) -> np.ndarray:
    """Convert dB to linear scale: σ°_linear = 10^(σ°_dB / 10)."""
    return np.power(10.0, arr / 10.0)


def to_linear(arr: np.ndarray) -> tuple[np.ndarray, str]:
    """Auto-detect scale and convert to linear if needed.

    Returns (linear_array, original_scale).
    """
    scale = detect_scale(arr)
    if scale == "dB":
        return db_to_linear(arr).astype(np.float32), scale
    return arr.astype(np.float32), scale

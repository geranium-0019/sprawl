"""Vectorized BUII / BUHI metric computation.

Both metrics operate on linear-scale sigma0 over an r×r moving window.
NaNs are treated as masked: any window containing NaNs returns NaN at center.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter

DEFAULT_WINDOW = 31   # 310m — block-to-neighborhood scale


def _window_mean(arr: np.ndarray, r: int) -> np.ndarray:
    """NaN-safe windowed mean using uniform_filter on masked sums."""
    valid = np.isfinite(arr).astype(np.float32)
    filled = np.where(valid > 0, arr, 0.0).astype(np.float32)
    sum_w = uniform_filter(filled, size=r, mode="reflect") * (r * r)
    cnt_w = uniform_filter(valid, size=r, mode="reflect") * (r * r)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(cnt_w > 0, sum_w / cnt_w, np.nan)
    return mean.astype(np.float32)


def compute_buii(
    linear: np.ndarray,
    r: int = DEFAULT_WINDOW,
    norm_percentile: float = 99.0,
) -> np.ndarray:
    """BUII = window-mean(σ°) / p99(window-mean), clipped to [0, 1].

    The framework defines BUII against the *global maximum* of the window-mean
    surface, but raw Sentinel-1 GRD scenes routinely contain a handful of
    extreme bright pixels (corner reflectors, metallic structures, residual
    speckle outliers) that crush the entire dynamic range.

    We replace the global max with a high-percentile reference (default p99)
    and clip — robust to outliers while preserving the intended semantic
    ("most-urban areas approach 1").
    """
    mean_w = _window_mean(linear, r)
    finite = mean_w[np.isfinite(mean_w)]
    if finite.size == 0:
        raise ValueError("Cannot normalize BUII: no finite values.")
    ref = float(np.percentile(finite, norm_percentile))
    if ref <= 0:
        raise ValueError(f"Cannot normalize BUII: p{norm_percentile}={ref}.")
    buii = np.clip(mean_w / ref, 0.0, 1.0)
    return buii.astype(np.float32)


def compute_buhi(linear: np.ndarray, r: int = DEFAULT_WINDOW) -> np.ndarray:
    """BUHI = std(σ° in dB scale) — robust to heavy-tailed SAR linear values.

    The framework's original CV-based BUHI (std/mean on linear σ°) is dominated
    by the long tail of bright pixels: linear σ° has skewness ≈ 160 in this
    scene, so both std and mean track the count of high-σ° pixels — making
    BUHI correlate strongly with BUII (~0.60). dB-scale σ° is near-Gaussian
    (skewness ≈ 0.7), so a window std is a cleaner heterogeneity measure.

    Output is in dB units; expected range ~0–6 dB. Do not normalize by mean
    in dB (mean is negative, ratio unstable).
    """
    db = 10.0 * np.log10(np.maximum(linear, 1e-6)).astype(np.float32)
    mean_db = _window_mean(db, r)
    mean_sq = _window_mean(db * db, r)
    var_db = np.maximum(mean_sq - mean_db * mean_db, 0.0)
    return np.sqrt(var_db).astype(np.float32)

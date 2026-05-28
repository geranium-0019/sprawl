"""PNG map output for BUII and BUHI rasters."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


_METRIC_CMAPS = {
    "buii": "Reds",
    "buhi": "Greens",
}


def _percentile_clip(arr: np.ndarray, lo: float = 1, hi: float = 99) -> tuple[float, float]:
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0, 1.0
    return float(np.percentile(finite, lo)), float(np.percentile(finite, hi))


def save_metric_map(
    arr: np.ndarray,
    out_path: str | Path,
    title: str,
    metric: str,
    vmin: float | None = None,
    vmax: float | None = None,
    dpi: int = 150,
) -> None:
    """Single-metric raster as PNG with colorbar."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cmap = _METRIC_CMAPS.get(metric, "viridis")
    if vmin is None or vmax is None:
        p1, p99 = _percentile_clip(arr)
        vmin = vmin if vmin is not None else p1
        vmax = vmax if vmax is not None else p99
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title)
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label=metric.upper())
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

"""Raster I/O for SAR-USPM pipeline.

Thin wrappers around rasterio that preserve geospatial metadata (CRS, transform,
nodata) when chaining read → compute → write steps.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.profiles import Profile


def read_band(path: str | Path, band: int = 1) -> tuple[np.ndarray, Profile]:
    """Read a single band as float32 with the source profile attached."""
    with rasterio.open(path) as src:
        arr = src.read(band).astype(np.float32)
        profile = src.profile.copy()
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
    profile.update(count=1, dtype="float32", nodata=np.nan)
    return arr, profile


def read_band_count(path: str | Path) -> int:
    with rasterio.open(path) as src:
        return src.count


def write_raster(
    path: str | Path,
    arr: np.ndarray,
    profile: Profile,
    dtype: str = "float32",
    nodata: float | int | None = None,
) -> None:
    """Write a single-band raster, inheriting CRS/transform from `profile`."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    out_profile.update(
        count=1,
        dtype=dtype,
        nodata=nodata,
        compress="LZW",
        tiled=True,
        blockxsize=512,
        blockysize=512,
    )
    out_arr = arr.astype(dtype)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(out_arr, 1)

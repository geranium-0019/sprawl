"""Compare validation performance across moving-window sizes.

This script recomputes BUII, BUHI, and SBI for several window sizes from the
same Sentinel-1 VV raster, aggregates each result to the existing 310 m
validation grid, and compares against the GBA-derived reference metrics.
"""
from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metrics import compute_buhi, compute_buii
from src.preprocessing import to_linear


RAW_VV = Path(
    "data/raw/2025_S1A_IW_GRDH_1SDV_20250427T221758_20250427T221823_058948_074F2C_66DD_Orb_Cal_Spk_TC.tif"
)
VV_BAND = 2
FOOTPRINT = Path("data/processed/building_footprint_ratio_310m.tif")
MIXING = Path("data/processed/built_nonbuilt_mixing_index_310m.tif")
OUT_DIR = Path("outputs/window_sensitivity")
PROC_DIR = Path("data/processed/window_sensitivity")
WINDOWS = (5, 11, 21, 31, 41)


def percentile_stretch(arr: np.ndarray, lo: float = 1, hi: float = 99) -> np.ndarray:
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        raise ValueError("No finite values for percentile stretch.")
    p_lo, p_hi = np.percentile(finite, [lo, hi])
    if p_hi <= p_lo:
        raise ValueError(f"Invalid stretch range: p{lo}={p_lo}, p{hi}={p_hi}")
    return np.clip((arr - p_lo) / (p_hi - p_lo), 0.0, 1.0).astype(np.float32)


def harmonic_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denom > 0, 2.0 * a * b / denom, 0.0)
    out[~np.isfinite(out)] = np.nan
    return out.astype(np.float32)


def aggregate_to_reference(
    arr: np.ndarray,
    src_profile: dict,
    ref_profile: dict,
) -> np.ndarray:
    dst = np.full(
        (ref_profile["height"], ref_profile["width"]),
        np.nan,
        dtype=np.float32,
    )
    reproject(
        source=arr.astype(np.float32),
        destination=dst,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        src_nodata=np.nan,
        dst_transform=ref_profile["transform"],
        dst_crs=ref_profile["crs"],
        dst_nodata=np.nan,
        resampling=Resampling.average,
    )
    return dst


def write_raster(path: Path, arr: np.ndarray, profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    out_profile.update(
        count=1,
        dtype="float32",
        nodata=np.nan,
        compress="LZW",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(arr.astype(np.float32), 1)


def read_reference(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
    return arr, profile


def plot_results(results: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=180)
    ax.plot(results["window"], results["buii_footprint_r"], marker="o", label="BUII vs footprint ratio")
    ax.plot(results["window"], results["sbi_mixing_r"], marker="o", label="SBI vs mixing index")
    ax.set_xlabel("Moving window size (pixels)")
    ax.set_ylabel("Spearman r")
    ax.set_xticks(results["window"])
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "window_validation_comparison.png")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    footprint, ref_profile = read_reference(FOOTPRINT)
    mixing, _ = read_reference(MIXING)

    with rasterio.open(RAW_VV) as src:
        raw = src.read(VV_BAND).astype(np.float32)
        src_profile = src.profile.copy()
        src_profile.update(count=1, dtype="float32", nodata=np.nan)
        if src.nodata is not None:
            raw = np.where(raw == src.nodata, np.nan, raw)

    linear, source_scale = to_linear(raw)
    print(f"Loaded {RAW_VV.name} band {VV_BAND}; source scale={source_scale}; shape={linear.shape}")
    del raw

    rows: list[dict[str, float | int]] = []
    validation_table: pd.DataFrame | None = None

    for window in WINDOWS:
        print(f"Computing window={window}...")
        buii = compute_buii(linear, r=window)
        buhi = compute_buhi(linear, r=window)
        sbi = harmonic_mean(percentile_stretch(buii), percentile_stretch(buhi))

        buii_310 = aggregate_to_reference(buii, src_profile, ref_profile)
        sbi_310 = aggregate_to_reference(sbi, src_profile, ref_profile)

        write_raster(PROC_DIR / f"buii_w{window}_310m.tif", buii_310, ref_profile)
        write_raster(PROC_DIR / f"sbi_w{window}_310m.tif", sbi_310, ref_profile)

        valid = np.isfinite(buii_310) & np.isfinite(sbi_310) & np.isfinite(footprint) & np.isfinite(mixing)
        buii_r, buii_p = spearmanr(buii_310[valid], footprint[valid])
        sbi_r, sbi_p = spearmanr(sbi_310[valid], mixing[valid])

        rows.append(
            {
                "window": window,
                "meters": window * 10,
                "n": int(valid.sum()),
                "buii_footprint_r": float(buii_r),
                "buii_footprint_p": float(buii_p),
                "sbi_mixing_r": float(sbi_r),
                "sbi_mixing_p": float(sbi_p),
            }
        )

        flat = pd.DataFrame(
            {
                "window": window,
                "buii": buii_310[valid],
                "sbi": sbi_310[valid],
                "footprint_ratio": footprint[valid],
                "mixing_index": mixing[valid],
            }
        )
        validation_table = flat if validation_table is None else pd.concat([validation_table, flat], ignore_index=True)
        print(f"  BUII r={buii_r:.3f}; SBI r={sbi_r:.3f}; n={valid.sum()}")

    results = pd.DataFrame(rows)
    results.to_csv(OUT_DIR / "window_validation_comparison.csv", index=False)
    if validation_table is not None:
        validation_table.to_csv(OUT_DIR / "window_validation_table.csv", index=False)
    plot_results(results)
    print("\nWindow validation comparison:")
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()

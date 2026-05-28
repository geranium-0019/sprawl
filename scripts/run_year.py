"""Run the full single-year pipeline (preprocess → metrics → maps).

Usage:
    python scripts/run_year.py --year 2025 \
        --input data/raw/2025_S1A_..._TC.tif \
        --vv-band 2

For 2025 the VV band is band 2 (band 1 = VH). Use --vv-band to override.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.io_raster import read_band, write_raster
from src.preprocessing import to_linear
from src.metrics import compute_buii, compute_buhi, DEFAULT_WINDOW
from src.visualization import save_metric_map


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--vv-band", type=int, default=2,
                   help="1-indexed VV band number (default: 2)")
    p.add_argument("--window", type=int, default=DEFAULT_WINDOW,
                   help=f"BUII/BUHI window in pixels (default: {DEFAULT_WINDOW})")
    p.add_argument("--out-root", type=Path, default=Path("outputs"))
    return p.parse_args()


def banner(msg: str) -> None:
    print(f"\n=== {msg} ===", flush=True)


def main() -> None:
    args = parse_args()
    t_start = time.time()
    out_dir = args.out_root / str(args.year)
    map_dir = out_dir / "maps"
    out_dir.mkdir(parents=True, exist_ok=True)
    map_dir.mkdir(parents=True, exist_ok=True)

    banner(f"[1/3] Reading band {args.vv_band} (VV) from {args.input.name}")
    raw, profile = read_band(args.input, band=args.vv_band)
    print(f"  shape={raw.shape}, dtype={raw.dtype}, "
          f"min={np.nanmin(raw):.4f}, max={np.nanmax(raw):.4f}, "
          f"mean={np.nanmean(raw):.4f}")

    banner("[2/3] Detecting scale & converting to linear")
    linear, src_scale = to_linear(raw)
    print(f"  source scale: {src_scale}  →  using linear")
    print(f"  linear range: [{np.nanmin(linear):.4f}, {np.nanmax(linear):.4f}]")
    del raw

    banner(f"[3/3] Computing BUII / BUHI (r={args.window})")
    t0 = time.time()
    buii = compute_buii(linear, r=args.window)
    print(f"  BUII done ({time.time() - t0:.1f}s)")
    t0 = time.time()
    buhi = compute_buhi(linear, r=args.window)
    print(f"  BUHI done ({time.time() - t0:.1f}s)")
    del linear

    write_raster(out_dir / f"buii_{args.year}.tif", buii, profile,
                 dtype="float32", nodata=float("nan"))
    write_raster(out_dir / f"buhi_{args.year}.tif", buhi, profile,
                 dtype="float32", nodata=float("nan"))

    save_metric_map(buii, map_dir / f"buii_{args.year}.png",
                    f"BUII {args.year}", "buii", vmin=0, vmax=1)
    save_metric_map(buhi, map_dir / f"buhi_{args.year}.png",
                    f"BUHI {args.year}", "buhi")

    banner(f"DONE in {time.time() - t_start:.1f}s")
    print(f"  outputs: {out_dir}")


if __name__ == "__main__":
    main()

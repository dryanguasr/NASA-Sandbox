"""Crop official USGS/MRO rasters. No synthetic fallback and no full-mosaic read.

The fine DEM is a simulation reference, NOT a measured drone reconstruction.
Both instruments belong to MRO; this is not a multi-mission competition entry.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window, from_bounds

BASE = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/"
SOURCES = {
    "reference": {
        "url": BASE + "HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif",
        "instrument": "MRO/HiRISE", "native_post_spacing_m": 1,
        "doi": "10.5066/P9REJ9JN",
        "citation": "Fergason et al. (2020), Mars 2020 Terrain Relative Navigation HiRISE DTM Mosaic, USGS.",
    },
    "prior": {
        "url": BASE + "CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif",
        "instrument": "MRO/CTX", "native_post_spacing_m": 20,
        "doi": "10.5066/P906QQT8",
        "citation": "Fergason et al. (2020), Mars 2020 Terrain Relative Navigation CTX DTM Mosaic, USGS.",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crop(source: str, crs: CRS, transform, n: int) -> tuple[np.ndarray, dict]:
    """Read a native-resolution source window then warp onto the local metric grid."""
    half = n * transform.a / 2
    with rasterio.open(source) as src:
        if src.crs is None:
            raise ValueError(f"Missing planetary CRS: {source}")
        if not src.crs.is_projected:
            raise ValueError("Expected a projected Mars raster")
        bounds = transform_bounds(crs, src.crs, -half, -half, half, half, densify_pts=21)
        win = from_bounds(*bounds, transform=src.transform)
        c0, r0 = int(np.floor(win.col_off)) - 3, int(np.floor(win.row_off)) - 3
        c1 = int(np.ceil(win.col_off + win.width)) + 3
        r1 = int(np.ceil(win.row_off + win.height)) + 3
        win = Window(c0, r0, c1-c0, r1-r0).intersection(Window(0, 0, src.width, src.height))
        if win.width * win.height > 16_000_000:
            raise ValueError("Requested crop exceeds 16 million native pixels")
        tile = src.read(1, window=win, masked=True).filled(np.nan).astype(np.float32)
        dest = np.full((n, n), np.nan, dtype=np.float32)
        reproject(tile, dest, src_transform=src.window_transform(win), src_crs=src.crs,
                  src_nodata=np.nan, dst_transform=transform, dst_crs=crs,
                  dst_nodata=np.nan, resampling=Resampling.bilinear)
        meta = {
            "source_crs_wkt": src.crs.to_wkt(), "source_shape": [src.height, src.width],
            "source_pixel_size": list(src.res), "source_nodata": str(src.nodata),
            "window_col_row_width_height": [int(win.col_off), int(win.row_off), int(win.width), int(win.height)],
            "source_window_sha256": hashlib.sha256(tile.tobytes()).hexdigest(),
            "valid_fraction": float(np.isfinite(dest).mean()),
        }
        return dest, meta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("data/jezero"))
    p.add_argument("--lon", type=float, default=77.45)
    p.add_argument("--lat", type=float, default=18.45)
    p.add_argument("--side-m", type=float, default=512.0)
    p.add_argument("--cell-m", type=float, default=4.0)
    p.add_argument("--reference-file", help="Optional already downloaded copy of the same HiRISE product")
    p.add_argument("--prior-file", help="Optional already downloaded copy of the same CTX product")
    args = p.parse_args()
    if not (0 < args.cell_m <= args.side_m <= 2000):
        p.error("Require 0 < cell-m <= side-m <= 2000")
    n = round(args.side_m / args.cell_m)
    if n < 8 or n > 512 or not np.isclose(n*args.cell_m, args.side_m):
        p.error("side-m / cell-m must be an integer in [8, 512]")
    if not (-85 < args.lat < 85 and -180 <= args.lon <= 360):
        p.error("Invalid study-area centre")
    args.out.mkdir(parents=True, exist_ok=True)
    local_crs = CRS.from_string(
        f"+proj=eqc +lat_ts={args.lat} +lat_0={args.lat} +lon_0={args.lon} "
        "+R=3396190 +units=m +no_defs")
    affine = from_origin(-args.side_m/2, args.side_m/2, args.cell_m, args.cell_m)
    arrays, details = {}, {}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="90",
                      GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_CACHEMAX=128):
        for name, spec in SOURCES.items():
            source = getattr(args, name + "_file") or spec["url"]
            print(f"Reading {name}: {source}", flush=True)
            arrays[name], extra = crop(source, local_crs, affine, n)
            details[name] = dict(spec, **extra)
    valid = np.isfinite(arrays["reference"]) & np.isfinite(arrays["prior"])
    if valid.mean() < .99:
        raise RuntimeError(f"Only {valid.mean():.1%} common coverage; choose a covered crop. No synthetic replacement.")
    origin_z = float(np.median(arrays["reference"][valid]))
    outfile = args.out / "terrain.npz"
    np.savez_compressed(outfile, reference=arrays["reference"], prior=arrays["prior"], valid=valid)
    metadata = {
        "schema_version": 1, "dataset_type": "USGS_MRO_REAL_RASTER_CROPS",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "center_lon_east_deg": args.lon, "center_lat_planetocentric_deg": args.lat,
        "shape": [n, n], "cell_m": args.cell_m, "side_m": args.side_m,
        "origin_z_m": origin_z, "local_crs_wkt": local_crs.to_wkt(),
        "affine_gdal": list(affine.to_gdal()), "row_order": "north_to_south",
        "longitude_direction": "east", "mars_sphere_radius_m": 3396190,
        "vertical_reference": "source product MOLA topography / DeltaGeoid; no Earth datum conversion",
        "resampling": "bilinear; CTX remains 20 m information on the 4 m computational grid",
        "sources": details, "terrain_sha256": digest(outfile),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "rasterio": rasterio.__version__},
        "limitations": [
            "HiRISE DEM is the held-out simulation reference, not perfect physical truth.",
            "No real drone data, mineral detection, soil mechanics, or operational EVA certification.",
            "CTX/HiRISE share processing and control data; they are not independent error samples.",
            "Both instruments are from one mission, MRO; not claimed to meet the full competition challenge.",
        ],
    }
    (args.out / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n")
    for name, arr in arrays.items():
        with rasterio.open(args.out / f"{name}.tif", "w", driver="GTiff", width=n, height=n,
                           count=1, dtype="float32", crs=local_crs, transform=affine,
                           nodata=np.nan, compress="deflate") as dst:
            dst.write(arr, 1)
    print(json.dumps({"shape": [n,n], "reference_range_m": [float(np.nanmin(arrays['reference'])), float(np.nanmax(arrays['reference']))],
                      "prior_reference_rmse_m": float(np.sqrt(np.nanmean((arrays['prior']-arrays['reference'])**2))),
                      "terrain_sha256": metadata["terrain_sha256"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()

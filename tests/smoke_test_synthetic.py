"""Smoke test for notebooks/02_wheat_ndvi_nirv_pipeline.ipynb.

Executes the notebook's own code cells (imports, Timer, Config, diagnostics,
discovery, all processing functions, run, save, summary, plot) against a tiny
synthetic dataset: two adjacent 100x100 px Sentinel-2-like tiles in EPSG:32632,
a crop type raster in EPSG:3035, and two fake NUTS3 regions. No Google Drive,
no GPU and no network access are needed. Runs in a few seconds.

    python tests/smoke_test_synthetic.py
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import box

NB = Path(__file__).resolve().parents[1] / "notebooks" / "02_wheat_ndvi_nirv_pipeline.ipynb"

TILE_PX = 100          # pixels per side
RES = 10               # metres per pixel
NODATA = -10000
WHEAT = 11
TILES = {"T32UMU": (600000, 5400000), "T32UNU": (601000, 5400000)}   # (x_min, y_max), adjacent


def make_synthetic_data(base: Path):
    rng = np.random.default_rng(0)
    month_dir = base / "WASP_Cache" / "2017" / "04_April"
    month_dir.mkdir(parents=True)

    for tid, (x0, y0) in TILES.items():
        tr = from_origin(x0, y0, RES, RES)
        # red DN 200-1500 (max > 1000 so the notebook's scale-factor heuristic picks 10000, as for real WASP data)
        b4 = rng.integers(200, 1500, (TILE_PX, TILE_PX)).astype("int16")
        b8 = rng.integers(2000, 5000, (TILE_PX, TILE_PX)).astype("int16")
        b4[:5, :] = NODATA          # nodata strip in the top 5 rows
        b8[:5, :] = NODATA
        for band, arr in (("B4", b4), ("B8", b8)):
            path = month_dir / f"SENTINEL2A_20170415-000000-000_L3A_{tid}_C_{band}.tif"
            with rasterio.open(path, "w", driver="GTiff", height=TILE_PX, width=TILE_PX, count=1,
                               dtype="int16", crs="EPSG:32632", transform=tr, nodata=NODATA) as dst:
                dst.write(arr, 1)

    # Crop type raster: 20 m grid covering both tiles, winter wheat in the upper half (y > 5399500),
    # built in EPSG:32632 and then reprojected to EPSG:3035 (the pipeline must reproject it back).
    ct_res = 20
    ct_w, ct_h = 150, 100                                   # 3000 m x 2000 m
    ct_tr = from_origin(599500, 5400500, ct_res, ct_res)
    ct = np.ones((ct_h, ct_w), dtype="uint8")
    ct[:50, :] = WHEAT                                      # rows 0..49 → y 5400500..5399500
    dst_crs = "EPSG:3035"
    dst_tr, dst_w, dst_h = calculate_default_transform("EPSG:32632", dst_crs, ct_w, ct_h,
                                                       *rasterio.transform.array_bounds(ct_h, ct_w, ct_tr))
    ct_3035 = np.zeros((dst_h, dst_w), dtype="uint8")
    reproject(ct, ct_3035, src_transform=ct_tr, src_crs="EPSG:32632",
              dst_transform=dst_tr, dst_crs=dst_crs, resampling=Resampling.nearest)
    ct_dir = base / "Data_CropTypes"
    ct_dir.mkdir()
    with rasterio.open(ct_dir / "croptypes_2017.tif", "w", driver="GTiff", height=dst_h, width=dst_w,
                       count=1, dtype="uint8", crs=dst_crs, transform=dst_tr, nodata=0) as dst:
        dst.write(ct_3035, 1)

    # Two fake NUTS3 regions: A = left tile + left half of right tile, B = right half of right tile.
    regions = gpd.GeoDataFrame(
        {"NUTS_ID": ["DE211", "DE212"], "NUTS_NAME": ["Region A", "Region B"]},
        geometry=[box(600000, 5399000, 601500, 5400000), box(601500, 5399000, 602000, 5400000)],
        crs="EPSG:32632",
    ).to_crs("EPSG:4326")
    return regions


def load_cells():
    nb = json.load(open(NB, encoding="utf-8"))
    return [("".join(c["source"])) for c in nb["cells"] if c["cell_type"] == "code"]


def find_cell(cells, marker):
    hits = [c for c in cells if marker in c]
    assert len(hits) == 1, f"marker {marker!r} matched {len(hits)} cells"
    return hits[0]


def run_cell(ns, src, label):
    assert not re.search(r"^\s*[!%]", src, re.M), f"cell {label} contains shell/magic lines"
    print(f"\n--- exec: {label} ---")
    exec(compile(src, f"<{label}>", "exec"), ns)


def main():
    cells = load_cells()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        regions = make_synthetic_data(base)
        os.environ["WHEAT_DRIVE_BASE"] = str(base)

        ns = {"__name__": "__nb__"}
        run_cell(ns, find_cell(cells, "# GPU CHECK"), "imports")
        assert ns["GPU_AVAILABLE"] in (True, False)
        run_cell(ns, find_cell(cells, "class Timer:"), "Timer")
        run_cell(ns, find_cell(cells, "class Config:"), "Config")
        cfg = ns["config"]
        cfg.YEARS, cfg.MONTHS = [2017], ["April"]
        run_cell(ns, find_cell(cells, "def diagnose_tile_properties"), "diagnose")
        assert cfg.NODATA_VALUE == NODATA and cfg.SCALE_FACTOR == 10000, (cfg.NODATA_VALUE, cfg.SCALE_FACTOR)
        run_cell(ns, find_cell(cells, "def discover_tile_structure"), "discover")
        assert sorted(ns["tile_structure"]["all_tiles"]) == sorted(TILES)

        # NUTS3 cell downloads from GISCO: replace with the synthetic regions.
        ns["pipeline_start"] = __import__("time").time()
        ns["nuts3"] = regions
        ns["nuts3_wgs"] = regions.copy()

        for marker in ("def find_intersecting_nuts3", "class WheatMaskHandler", "def calculate_indices_gpu",
                       "def process_single_tile", "def aggregate_tile_stats", "def run_pipeline_tiles_by_month"):
            run_cell(ns, find_cell(cells, marker), marker)

        # unit check of the index maths on CPU
        b4 = np.array([[400, NODATA, 0]], dtype="int16")
        b8 = np.array([[3600, NODATA, 0]], dtype="int16")
        ndvi, nirv = ns["calculate_indices_gpu"](b4, b8, 10000, float(NODATA))
        assert np.isclose(ndvi[0, 0], 0.8) and np.isclose(nirv[0, 0], 0.8 * 0.36), (ndvi, nirv)
        assert ndvi[0, 1] == NODATA and ndvi[0, 2] == NODATA, ndvi

        run_cell(ns, find_cell(cells, "Timer.reset()"), "run pipeline")
        final, per_tile = ns["final_stats"], ns["per_tile_stats"]
        print(final)
        assert not final.is_empty(), "pipeline produced no results"
        assert set(final["index"].unique()) == {"NDVI", "NIRv"}
        assert set(final["nuts3_id"].unique()) == {"DE211", "DE212"}
        a_ndvi = final.filter((final["index"] == "NDVI") & (final["nuts3_id"] == "DE211")).row(0, named=True)
        b_ndvi = final.filter((final["index"] == "NDVI") & (final["nuts3_id"] == "DE212")).row(0, named=True)
        assert a_ndvi["n_tiles"] == 2, a_ndvi          # region A spans both tiles
        assert b_ndvi["n_tiles"] == 1, b_ndvi
        assert 0.4 < a_ndvi["mean"] < 0.9, a_ndvi       # E[b4]=850, E[b8]=3500 → NDVI ≈ 0.61
        # expected valid wheat pixels: 45 rows (50 wheat rows minus 5 nodata rows) x width
        exp_a, exp_b = 45 * 150, 45 * 50
        assert abs(a_ndvi["total_pixels"] - exp_a) / exp_a < 0.15, (a_ndvi["total_pixels"], exp_a)
        assert abs(b_ndvi["total_pixels"] - exp_b) / exp_b < 0.15, (b_ndvi["total_pixels"], exp_b)
        nirv_a = final.filter((final["index"] == "NIRv") & (final["nuts3_id"] == "DE211")).row(0, named=True)
        assert 0.1 < nirv_a["mean"] < 0.4, nirv_a        # NIRv ≈ 0.61 × 0.35 ≈ 0.21

        run_cell(ns, find_cell(cells, "parquet_path = output_dir"), "save")
        run_cell(ns, find_cell(cells, "SUMMARY BY YEAR"), "summary")
        run_cell(ns, find_cell(cells, "MULTI-YEAR COMPARISON"), "plot")
        run_cell(ns, find_cell(cells, "PIPELINE COMPLETE"), "final summary")
        out = cfg.OUTPUT_BASE
        for name in ("2017_nuts3_stats.parquet", "2017_nuts3_stats.csv", "2017_pertile_stats.parquet",
                     "2017_ndvi_timeseries.png"):
            assert (out / name).exists(), f"missing output {name}"

    print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()

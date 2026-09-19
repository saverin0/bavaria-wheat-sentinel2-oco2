# Winter Wheat Vegetation Indices for Bavaria from Sentinel-2 (2017–2024)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/saverin0/bavaria-wheat-sentinel2-oco2/blob/main/notebooks/02_wheat_ndvi_nirv_pipeline.ipynb)

Monthly **NDVI** and **NIRv** for **winter wheat fields** in Bavaria, Germany, aggregated to the 96 NUTS3
regions (Landkreise) for March–June of every year from 2017 to 2024. The indices are computed from
DLR's monthly Sentinel-2 L3A WASP composites, masked with DLR's yearly 10 m crop type maps, and
aggregated with exact (partial-pixel) zonal statistics. The resulting time series is intended as
input for crop-yield modelling.

An optional side analysis extracts Sentinel-2 red/NIR reflectance for every OCO-2 solar-induced
fluorescence (SIF) sounding footprint over Bavaria so SIF can be compared with NDVI/NIRv.

## Project context

This repository is the Sentinel-2 half of a two-person Master of Data Science capstone project,
*Crop Yield Prediction and Attribution Using OCO-2 Satellite Data* (University of Europe for Applied
Sciences, Potsdam, January 2026), by **Abhishek Singh** and **Vishal Thamizharasan**.

- **Abhishek Singh** (this repository): the Sentinel-2 WASP tile cache, the GPU NDVI/NIRv pipeline with
  year-specific winter wheat masks, NUTS3 zonal statistics, and the OCO-2 footprint × Sentinel-2
  extraction.
- **Vishal Thamizharasan** ([vishalt11/remote-sensing-crop-yield](https://github.com/vishalt11/remote-sensing-crop-yield)):
  OCO-2 SIF and GOSIF processing, zonal statistics of SIF footprints against the crop type maps (wheat
  share, C3/C4 share), the yield models, and the R Shiny dashboard.

The monthly NUTS3 NDVI/NIRv table produced here was joined with official winter wheat yields from the
Bavarian State Office for Statistics and with OCO-2 SIF and climate variables (VPD, humidity,
temperature) to train yield models for 2017–2023 and test on 2024. The best model, XGBoost at NUTS3
level with OCO-2 SIF, reached an RMSE of 0.453 t/ha, about 6.6 % of Bavaria's 2024 mean winter wheat
yield of 6.83 t/ha. SIF, NIRv, vapour pressure deficit and C3 crop share were the most important
predictors. A model using only the NDVI/NIRv features from this repository reached 0.993 t/ha, which
supports SIF as the strongest single predictor. The modelling code and dashboard live in the linked
repository, not here.

## Results of the recorded run

The notebooks in this repository keep the outputs of the completed run.

| | |
|---|---|
| Study area | Bavaria, 96 NUTS3 regions (NUTS 2021) |
| Period | 2017–2024, March, April, May, June |
| Input tiles | 29 Sentinel-2 MGRS tiles per month, 4,768 GeoTIFFs, 1.13 TB |
| Winter wheat pixels processed | 1.64 billion (10 m) |
| Output rows | 6,094 (year × month × index × NUTS3) |
| Runtime | 5.5 h on a Google Colab A100 / High-RAM runtime (Drive I/O bound) |

Average of the regional NDVI means over March–June (from section 17 of notebook 02):

| Year | Mean NDVI | Winter wheat pixels | Regions with data |
|---|---|---|---|
| 2017 | 0.678 | 223.4 M | 95 |
| 2018 | 0.618 | 182.4 M | 94 |
| 2019 | 0.683 | 200.8 M | 95 |
| 2020 | 0.700 | 213.9 M | 96 |
| 2021 | 0.690 | 186.2 M | 96 |
| 2022 | 0.620 | 189.5 M | 95 |
| 2023 | 0.785 | 219.5 M | 95 |
| 2024 | 0.739 | 219.7 M | 96 |

For 2017 the monthly Bavaria-wide NDVI rises from 0.46 (March) to 0.60 (April) and 0.86 (May) and
falls to 0.79 in June as the wheat ripens.

Notebook 03 matched 151,793 OCO-2 SIF footprints over Bavaria (all land cover, March–June 2017–2024)
with the Sentinel-2 composites: the Pearson correlation of daily SIF is 0.54 with NIRv and 0.42 with NDVI.

## Repository layout

```
notebooks/
  01_download_wasp_tiles.ipynb            build the Sentinel-2 tile cache on Google Drive (run once)
  02_wheat_ndvi_nirv_pipeline.ipynb       main pipeline: wheat mask → NDVI/NIRv → NUTS3 statistics
  03_oco2_sif_sentinel2_extraction.ipynb  optional: Sentinel-2 B4/B8 per OCO-2 SIF footprint
tests/
  smoke_test_synthetic.py                 runs the notebook-02 code on tiny synthetic rasters (no data, no GPU)
requirements.txt
LICENSE                                   Apache 2.0
```

## Data sources

All inputs are public. Nothing in this repository contains data; the notebooks read from a project
folder on Google Drive.

| Dataset | Provider / access | Licence | Used for |
|---|---|---|---|
| Sentinel-2 L3A monthly WASP composites, bands B4 (red) and B8 (NIR), 10 m | DLR EOC Geoservice STAC API, collection `S2_L3A_WASP`: `https://geoservice.dlr.de/eoc/ogc/stac/v1` | CC-BY-4.0 | reflectance |
| CropTypes – Crop Type Maps for Germany, yearly, 10 m, V02 (2017–2024) | DLR EOC Geoservice: <https://geoservice.dlr.de/web/datasets/croptypes_de>, download <https://download.geoservice.dlr.de/CROPTYPES/files/> | CC-BY-4.0 | winter wheat mask (class **11**) |
| NUTS 2021 boundaries, level 3, 1:1M, EPSG:4326 | Eurostat GISCO GeoJSON: `NUTS_RG_01M_2021_4326_LEVL_3.geojson` | © EuroGeographics | aggregation regions |
| OCO-2 L2 Lite SIF (`OCO2_L2_Lite_SIF`), optional | NASA GES DISC | NASA open data | notebook 03 only |

Crop type maps: 8-bit Cloud Optimised GeoTIFF, EPSG:32632, whole Germany per year. Legend excerpt:
`0 no data, 11 winter wheat, 12 winter barley, 13 winter rye, 21 spring wheat, 30 maize, 60 sugar beet,
71 rapeseed, 83 permanent grassland`. Citation: Gessner, U.; Hirner, A.; Asam, S.; Wenzl, M.; Kuenzer, C.
*Combining Machine Learning and Spatio-Temporal Filtering to Map Crop Types of Germany for Seven Years.*
IEEE GRSL 2025, 22, 2504805, doi:10.1109/LGRS.2025.3587517.

## Google Drive layout expected by the notebooks

```
<DRIVE_BASE>/                        default: /content/drive/MyDrive/Capstone Project
├── WASP_Cache/                      written by notebook 01
│   └── {year}/{MM_Month}/SENTINEL2*_L3A_T{tile}_C_B4.tif and _B8.tif
├── Data_CropTypes/
│   └── croptypes_{year}.tif         DLR crop type map for each year (see below)
├── oco2_sif.parquet                 optional, notebook 03
├── Results_PerTile/                 written by notebook 02
└── Results_OCO2/                    written by notebook 03
```

`DRIVE_BASE` is set once in the configuration cell of each notebook (or through the
`WHEAT_DRIVE_BASE` environment variable when running outside Colab).

**Preparing the crop type maps.** Download the GeoTIFF for each year from the
`CROPTYPES_DE_P1Y_{year}_V02` folder on the DLR download server and store it as
`Data_CropTypes/croptypes_{year}.tif`. The pipeline reprojects the map to each tile's grid, so the
whole-Germany file works, but clipping it to Bavaria first saves memory and time:

```python
import rasterio
from rasterio.windows import from_bounds
# Bavaria bounding box in EPSG:32632 (approx.)
bounds = (480000, 5220000, 860000, 5610000)
with rasterio.open("CROPTYPES_DE_P1Y_2017_V02.tif") as src:
    win = from_bounds(*bounds, src.transform)
    data = src.read(1, window=win)
    profile = src.profile | {"height": data.shape[0], "width": data.shape[1],
                             "transform": src.window_transform(win), "driver": "GTiff"}
with rasterio.open("croptypes_2017.tif", "w", **profile) as dst:
    dst.write(data, 1)
```

**Preparing the OCO-2 table (optional).** Notebook 03 expects a Parquet file with one row per
sounding and the columns `Delta_date` (YYYY-MM-DD), `Lon_corner1..4`, `Lat_corner1..4`,
`Daily_SIF_740nm`, optionally `Delta_Time`, `Quality_Flag`. These are the footprint vertex and
daily-corrected SIF fields of the OCO-2 SIF Lite NetCDF files, filtered to the Bavaria bounding box.

## Running on Google Colab

1. **Notebook 01** (any runtime, no GPU): searches the DLR STAC catalogue for every tile intersecting
   Bavaria, month by month, and streams B4 and B8 into `WASP_Cache/`. The full cache is 1.13 TB, so a
   Google Drive plan with 2 TB is required. The download is resumable. To try the workflow on a subset,
   set `MAX_TILES_PER_MONTH` or shorten `YEARS`/`MONTHS`.
2. **Notebook 02** (A100 or other GPU, High-RAM recommended): set `QUICK_TEST=True` in the
   configuration cell for a few-minute test on one year, one month and two tiles, then run with
   `QUICK_TEST=False` for the full study. Results are written to `Results_PerTile/`. Without a GPU the
   same code runs on the CPU with NumPy, only slower.
3. **Notebook 03** (High-RAM, CPU): only if you have the OCO-2 table.

Each notebook installs its own dependencies in the first cell. For a local run use
`pip install -r requirements.txt` (add `cupy-cuda12x` for GPU support) and set `WHEAT_DRIVE_BASE`.

## Method

For every year, month and tile:

1. Read B4 and B8 (int16 digital numbers, nodata −10000, reflectance = DN / 10000; both values are
   auto-detected from a sample tile in section 6 of notebook 02).
2. `NDVI = (B8 − B4) / (B8 + B4)`, clipped to [−1, 1]; `NIRv = NDVI × B8_reflectance`. Pixels with a
   non-positive denominator are set to nodata. Computed with CuPy on the GPU or NumPy on the CPU.
3. Reproject the year's crop type map to the tile grid (nearest neighbour) and keep only pixels with
   class 11 (winter wheat). The reprojected mask is cached per tile grid.
4. Write the masked index to a temporary GeoTIFF and run `exactextract` against the NUTS3 polygons
   that intersect the tile (polygons reprojected to the tile CRS, EPSG:32632 or 32633). Statistics:
   mean, standard deviation, min, max and coverage-weighted pixel count.

Aggregation across tiles (section 13): for each year/month/index/NUTS3,
`mean = Σ(mean_t × n_t) / Σ n_t`, `std = sqrt(Σ(std_t² × n_t) / Σ n_t)`, `min`/`max` over tiles,
`total_pixels = Σ n_t`, `n_tiles` = number of contributing tiles. Because tiles do not overlap, no pixel
is counted twice. Note that the pooled `std` ignores differences between tile means, so it slightly
underestimates the true regional standard deviation for regions spanning several tiles.

### Output schema (`Results_PerTile/2017_2024_nuts3_stats.csv` / `.parquet`)

| Column | Description |
|---|---|
| `year`, `month` | e.g. 2017, `April` |
| `index` | `NDVI` or `NIRv` |
| `nuts3_id`, `region_name` | NUTS 2021 id (e.g. `DE211`) and name |
| `mean`, `std`, `min`, `max` | statistics over winter wheat pixels in the region |
| `total_pixels` | coverage-weighted number of winter wheat pixels (10 m) |
| `n_tiles` | number of Sentinel-2 tiles contributing |

`2017_2024_pertile_stats.parquet` holds the same statistics before aggregation, with a `tile_id` column.

## Testing without the data

```
pip install -r requirements.txt
python tests/smoke_test_synthetic.py
```

The test builds two 100 × 100 px synthetic tiles, a crop type raster in a different CRS and two fake
NUTS3 regions in a temporary folder, then executes the actual code cells of notebook 02 (imports, Timer,
Config, diagnostics, tile discovery, all processing functions, run, save, summary and plot) and checks
the resulting statistics, pixel counts and output files.

## Known limitations

- Google Drive I/O dominates the runtime; copying the tiles of one year to the Colab local disk before
  processing would be considerably faster.
- The WASP composites are monthly syntheses; residual cloud or snow pixels are not filtered beyond
  what the WASP processor already does.
- The crop type maps have an overall accuracy of about 75 % (winter wheat F1 > 0.8), so the wheat mask
  contains some misclassified fields.
- NUTS 2021 boundaries are used for all years.

## Authors and acknowledgements

- Abhishek Singh: Sentinel-2 processing pipeline (this repository)
- Vishal Thamizharasan: OCO-2/GOSIF processing, yield models and dashboard
  ([vishalt11/remote-sensing-crop-yield](https://github.com/vishalt11/remote-sensing-crop-yield))

Supervised at the University of Europe for Applied Sciences, Potsdam, as part of the Master of Data
Science capstone project, winter 2025/26.

## Licence

Code: Apache License 2.0 (see `LICENSE`). Input data remain under the licences of their providers
(DLR products CC-BY-4.0, Eurostat GISCO, NASA).

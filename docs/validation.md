# Validation Design

## Purpose

This validation is designed to test whether the proposed SAR-derived morphology indices correspond to physically interpretable urban form.

The validation does not aim to reproduce predefined land-cover classes. Instead, it evaluates two direct relationships:

```text
BUII / intensity  -> built-up density
SBI / harmonic index -> built/non-built transitional mixing
```

BUHI is not directly validated against building morphology because SAR heterogeneity can be caused by many sources, including agricultural texture, vegetation boundaries, water edges, terrain shadow, and mixed land cover. Therefore, BUHI is used as an internal component of SBI, but the external validation focuses on the composite harmonic index.

---

## Data

### Study AOI

The validation area was defined from the Sentinel-1 scene used in the study.

Input raster:

```text
/home/gray/tendra/data/raw/2015_of_S1A_IW_GRDH_1SDV_20150701T221702_20150701T221737_006623_008D5B_5E02_Orb_Cal_Spk_TC.tif
```

Raster metadata:

```text
Sensor/product: Sentinel-1A IW GRDH
Acquisition time: 2015-07-01 22:17 UTC
CRS: EPSG:4326 / WGS84
Pixel size: ~0.00008983 degrees, approximately 10 m
Raster size: 5657 × 4445 pixels
Bands: 2 Float32 bands
```

AOI bounds:

```text
Longitude: 110.5955 to 111.1037 E
Latitude:  -7.7546 to  -7.3553 S
```

The same AOI was transformed to EPSG:3857 for processing the GlobalBuildingAtlas building data:

```text
min_x = 12311434.744
min_y = -865885.695
max_x = 12368007.309
max_y = -821046.490
```

### SAR-derived indices

The SAR-derived validation inputs were generated from Sentinel-1 VV backscatter:

```text
BUII: Built-Up Intensity Index
SBI: Sprawl Balance Index / harmonic index
```

BUII represents normalized local backscatter intensity. SBI is the harmonic index combining stretched BUII and stretched BUHI, designed to be high where both built-up intensity and heterogeneity are present.

For validation, the SAR index rasters were clipped to the AOI and resampled to EPSG:3857. They were then aggregated from 10 m to 310 m using average resampling.

Processed SAR files:

```text
/home/gray/tendra/data/processed/buii_2025_aoi_3857_10m.tif
/home/gray/tendra/data/processed/sbi_2025_aoi_3857_10m.tif
/home/gray/tendra/data/processed/buii_2025_aoi_310m.tif
/home/gray/tendra/data/processed/sbi_2025_aoi_310m.tif
```

### External reference

GlobalBuildingAtlas building footprints were used as an independent external reference dataset. The required 5° × 5° tile was selected based on the Sentinel-1 AOI:

```text
GBA tile: e110_s05_e115_s10
Region folder: oceania
```

Input GBA files:

```text
/home/gray/tendra/GBA_tiles/oceania/e110_s05_e115_s10.geojson
/home/gray/tendra/GBA_tiles/Polygon/oceania/e110_s05_e115_s10.geojson
```

The first file corresponds to ODbL polygons and the second file corresponds to additional GBA.LoD1 polygons.

The building data were clipped to the Sentinel-1 AOI and rasterized to a 10 m building mask. The mask was then aggregated to 310 m to calculate building-based reference metrics.

Clipped building outputs:

```text
/home/gray/tendra/data/processed/gba_part1_odbl_aoi.gpkg
/home/gray/tendra/data/processed/gba_part2_lod1_polygon_aoi.gpkg
/home/gray/tendra/data/processed/gba_buildings_aoi_merged.gpkg
/home/gray/tendra/data/processed/gba_buildings_aoi_2015_s1.gpkg
```

Feature counts after AOI clipping:

```text
Part I clipped: 523,867 buildings
Part II clipped: 2,035,740 buildings
Merged AOI dataset: 2,559,607 buildings
```

The merged AOI building dataset was stored as a GeoPackage in EPSG:3857:

```text
Geometry type: MultiPolygon
CRS: EPSG:3857 / WGS 84 Pseudo-Mercator
Feature count: 2,559,607
```

### Building reference metrics

The building polygons were converted into a 10 m binary building mask:

```text
building pixel = 1
non-building pixel = 0
```

The 10 m mask was then aggregated to 310 m using average resampling. The resulting value is interpreted as the building footprint ratio:

```text
building_footprint_ratio = mean(building_mask_10m) within each 310 m cell
```

The built/non-built mixing index was then calculated from the footprint ratio:

```text
p = building_footprint_ratio
built_nonbuilt_mixing_index = 4 * p * (1 - p)
```

Reference metric rasters:

```text
/home/gray/tendra/data/processed/gba_building_mask_aoi_3857_10m.tif
/home/gray/tendra/data/processed/building_footprint_ratio_310m.tif
/home/gray/tendra/data/processed/built_nonbuilt_mixing_index_310m.tif
```

### Validation table

The final validation table contains one record per 310 m grid cell:

```text
/home/gray/tendra/data/processed/validation_table_310m.csv
```

Number of valid grid cells:

```text
n = 26,208
```

Main fields:

```text
x, y
buii
sbi
footprint_ratio
mixing_index
```

Summary statistics:

| Variable | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| BUII | 0.263 | 0.221 | 0.021 | 1.000 |
| SBI | 0.233 | 0.192 | 0.000 | 1.000 |
| Building footprint ratio | 0.102 | 0.070 | 0.000 | 0.755 |
| Built/non-built mixing index | 0.320 | 0.259 | 0.000 | 1.000 |

The validation is therefore based on comparable 310 m grid-level measurements from SAR-derived indices and GlobalBuildingAtlas-derived building metrics.

---

## Validation 1: BUII as Built-Up Density

### Purpose

To test whether SAR backscatter intensity works as a direct proxy for built-up density.

### Reference metric

```text
building_footprint_ratio = building_footprint_area / grid_cell_area
```

This metric represents the proportion of each 310 m grid cell covered by building footprints.

### Main comparison

```text
BUII vs building_footprint_ratio
```

### Expected relationship

If BUII is a valid built-up intensity proxy, grid cells with higher building footprint ratios should generally have higher BUII values.

### Statistic

```text
Spearman rank correlation
```

Spearman correlation is used because both SAR values and building-density metrics are expected to be non-normal and skewed.

### Result

```text
Spearman r = 0.755
p < 0.001
n = 26,208 grid cells
```

### Interpretation

The strong positive correlation supports the interpretation of BUII as a built-up density proxy.

---

## Validation 2: SBI as Built/Non-Built Mixing

### Purpose

To test whether the harmonic index captures transitional urban morphology, where built-up and non-built surfaces are spatially mixed.

### Reference metric

For each 310 m grid cell:

```text
p = building_footprint_area / grid_cell_area
built_nonbuilt_mixing_index = 4 * p * (1 - p)
```

Interpretation:

```text
p = 0.0 -> mixing_index = 0  fully non-built
p = 0.5 -> mixing_index = 1  strongest built/non-built mixture
p = 1.0 -> mixing_index = 0  fully built-up
```

This metric is suitable for evaluating transitional morphology because it is low in both fully non-built and fully built-up cells, and highest when built-up and non-built surfaces are balanced.

### Main comparison

```text
SBI vs built_nonbuilt_mixing_index
```

### Expected relationship

If SBI is a valid transition / sprawl morphology proxy, it should be higher in cells where building footprints and non-built surfaces are spatially mixed.

### Statistic

```text
Spearman rank correlation
```

### Result

```text
Spearman r = 0.779
p < 0.001
n = 26,208 grid cells
```

### Interpretation

The strong positive correlation supports the interpretation of SBI as a proxy for built/non-built transitional mixing.

---

## Summary

| Validation target | External reference | Statistic | Result | Interpretation |
|---|---|---:|---:|---|
| BUII / intensity | Building footprint ratio | Spearman r | 0.755 | Supports built-up density interpretation |
| SBI / harmonic index | Built/non-built mixing index | Spearman r | 0.779 | Supports transitional mixing interpretation |

---

## Window-Size Sensitivity

To evaluate whether the selected 31 × 31 pixel window is reasonable, the validation was repeated using five odd-numbered moving windows:

```text
5 × 5 pixels = approximately 50 m
11 × 11 pixels = approximately 110 m
21 × 21 pixels = approximately 210 m
31 × 31 pixels = approximately 310 m baseline
41 × 41 pixels = approximately 410 m
```

Odd-numbered windows were used so that each moving window has a clear center pixel. The 5 × 5 and 11 × 11 windows were included to test very local behavior, while 21 × 21, 31 × 31, and 41 × 41 represent nearby block-to-neighborhood scales around the baseline.

### Validation performance

| Window | Approx. scale | BUII vs footprint ratio | SBI vs mixing index |
|---:|---:|---:|---:|
| 5 × 5 | 50 m | 0.771 | 0.799 |
| 11 × 11 | 110 m | 0.768 | 0.793 |
| 21 × 21 | 210 m | 0.762 | 0.784 |
| 31 × 31 | 310 m | 0.749 | 0.773 |
| 41 × 41 | 410 m | 0.727 | 0.752 |

All correlations are Spearman r values with p < 0.001 and n = 26,390 grid cells.

The smallest windows give the highest validation correlations. This is expected because the external reference metrics are derived directly from building footprints, so very local SAR windows are more tightly aligned with local building coverage. However, the purpose of the framework is not to maximize building-footprint correlation at the most local scale. The goal is to represent block-to-neighborhood morphology and reduce sensitivity to individual buildings, small local patches, and pixel-scale SAR texture.

### Map consistency between windows

| Metric | Window pair | Spearman r |
|---|---|---:|
| BUII | 5 vs 11 | 0.996 |
| BUII | 5 vs 31 | 0.958 |
| BUII | 11 vs 31 | 0.972 |
| BUII | 21 vs 31 | 0.992 |
| BUII | 31 vs 41 | 0.991 |
| BUII | 21 vs 41 | 0.969 |
| SBI | 5 vs 11 | 0.988 |
| SBI | 5 vs 31 | 0.921 |
| SBI | 11 vs 31 | 0.956 |
| SBI | 21 vs 31 | 0.989 |
| SBI | 31 vs 41 | 0.990 |
| SBI | 21 vs 41 | 0.962 |

The very high map-to-map correlations show that the main spatial patterns are robust across nearby window sizes.

### Interpretation

The 31 × 31 window is not selected because it maximizes the validation correlation. The highest correlations occur at 5 × 5 and 11 × 11 because these windows are closer to individual building and parcel scales. Those windows are useful as a local-scale check, but they are less appropriate for the stated objective of capturing neighborhood-scale morphology.

The 31 × 31 window is selected as a balanced neighborhood-scale window. It preserves strong validation relationships with building morphology, remains highly consistent with nearby windows, and avoids excessive sensitivity to very local texture. The larger 41 × 41 window smooths the maps more strongly and slightly weakens the validation relationships. The 31 × 31 window therefore provides a practical compromise between local morphological detail and spatial robustness.

### Literature-based justification for 31 × 31

The 31 × 31 pixel window also has a practical connection to existing LCZ-style remote-sensing work. At Sentinel-1's 10 m spatial resolution, 31 × 31 pixels correspond to approximately:

```text
31 × 10 m = 310 m
```

This is close to the 320 m × 320 m Sentinel-1/Sentinel-2 patch scale used in the So2Sat LCZ42 benchmark for Local Climate Zone classification. LCZ-based remote-sensing studies use this type of patch scale to represent local urban morphology, compactness, and built-form characteristics rather than individual buildings.

A 32 × 32 pixel window would match 320 m exactly, but it is an even-sized moving window and therefore does not have a single center pixel. For moving-window raster computation, an odd-sized kernel is preferable because each output pixel corresponds to a clearly centered local neighborhood.

Therefore, the 31 × 31 window can be interpreted as the centered moving-window approximation of the established 320 m LCZ-style local morphology scale:

```text
So2Sat LCZ42 patch scale: 320 m × 320 m
This study: 31 × 31 pixels ≈ 310 m × 310 m
```

This supports the use of 31 × 31 as a block-to-neighborhood scale window rather than an arbitrary parameter choice.

---

## Output files

```text
/home/gray/tendra/data/processed/validation_table_310m.csv
/home/gray/tendra/outputs/validation/correlation_table.csv
/home/gray/tendra/outputs/validation/scatter_buii_footprint_ratio.png
/home/gray/tendra/outputs/validation/scatter_sbi_mixing_index.png
/home/gray/tendra/outputs/window_sensitivity/window_validation_comparison.csv
/home/gray/tendra/outputs/window_sensitivity/window_map_correlations.csv
/home/gray/tendra/outputs/window_sensitivity/window_validation_comparison.png
```

## Important note

The building footprint ratio and mixing index were calculated using a raster-based approximation:

```text
building polygons -> 10 m building mask -> 310 m aggregation
```

Therefore, this should be described as a grid/raster-based approximation unless a later vector-exact area aggregation is implemented.

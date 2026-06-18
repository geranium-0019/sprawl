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

## Output files

```text
/home/gray/tendra/data/processed/validation_table_310m.csv
/home/gray/tendra/outputs/validation/correlation_table.csv
/home/gray/tendra/outputs/validation/scatter_buii_footprint_ratio.png
/home/gray/tendra/outputs/validation/scatter_sbi_mixing_index.png
```

## Important note

The building footprint ratio and mixing index were calculated using a raster-based approximation:

```text
building polygons -> 10 m building mask -> 310 m aggregation
```

Therefore, this should be described as a grid/raster-based approximation unless a later vector-exact area aggregation is implemented.

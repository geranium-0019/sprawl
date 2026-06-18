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

### SAR indices

SAR-derived indices were generated from Sentinel-1 VV backscatter:

```text
BUII: Built-Up Intensity Index
SBI: Sprawl Balance Index / harmonic index
```

Both were aggregated to the same 310 m grid used by the framework.

### External reference

GlobalBuildingAtlas building footprints were used as an independent external reference dataset.

The building data were clipped to the Sentinel-1 AOI and rasterized to a 10 m building mask. The mask was then aggregated to 310 m to calculate building-based reference metrics.

AOI:

```text
Longitude: 110.5955 to 111.1037 E
Latitude:  -7.7546 to  -7.3553 S
```

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

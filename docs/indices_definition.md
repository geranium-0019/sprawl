# SAR Urban Morphology Indices — Definition and Interpretation

This document defines the four indices used in this study, derived from Sentinel-1 GRD backscatter (σ°, VV polarization, 10 m pixel).  
All indices are computed in `src/metrics.py` and `scripts/run_year.py`.

---

## Common preprocessing

| Step | Detail |
|------|--------|
| Input | Sentinel-1 GRD, VV band, terrain-corrected (σ°, linear scale) |
| Pixel size | 10 m |
| Moving window | 31 × 31 pixels = **310 m** (block-to-neighborhood scale) |
| NaN handling | Windows containing NaN return NaN at center (masked pixels excluded from all statistics) |

---

## 1. BUII — Built-Up Intensity Index

### Formula

$$\text{BUII} = \text{clip}\left(\frac{\overline{\sigma^\circ}_W}{P_{99}(\overline{\sigma^\circ}_W)},\ 0,\ 1\right)$$

where $\overline{\sigma^\circ}_W$ is the windowed mean of linear-scale σ° over a 31 × 31 pixel window.

### Step-by-step

1. Compute the windowed mean of linear σ° at each pixel (NaN-safe)
2. Compute the 99th percentile of the windowed-mean surface as the normalization reference
3. Divide by that reference and clip to [0, 1]

### Why p99 instead of global max

Raw Sentinel-1 scenes contain a small number of extremely bright pixels (corner reflectors, metallic structures, speckle outliers) that compress the dynamic range if used as the maximum. p99 is robust to these outliers while preserving the intended semantic: the densest built-up areas approach 1.

### Output range

| Statistic | Value |
|-----------|-------|
| Min | 0.010 |
| p1 | 0.075 |
| p50 | 0.215 |
| p99 | 1.000 |
| Max | 1.000 |

### Interpretation

- **High (→ 1)**: high mean backscatter over a 310 m window → dense built-up surface (urban core, industrial)
- **Low (→ 0)**: low mean backscatter → water, forest, bare soil, or low-density settlement
- Represents **average backscatter intensity** — a proxy for **surface density and built-up fraction**

---

## 2. BUHI — Built-Up Heterogeneity Index

### Formula

$$\text{BUHI} = \sqrt{\overline{({\sigma^\circ_{\text{dB}}})^2}_W - \left(\overline{\sigma^\circ_{\text{dB}}}_W\right)^2}$$

where $\sigma^\circ_{\text{dB}} = 10 \cdot \log_{10}(\sigma^\circ)$ and the overbar denotes the windowed mean.

This is the **standard deviation of σ° in dB scale** within a 31 × 31 pixel window.

### Step-by-step

1. Convert linear σ° to dB: `db = 10 · log10(max(σ°, 1e-6))`
2. Compute windowed mean of db and windowed mean of db²
3. `var = max(mean(db²) − mean(db)², 0)` (floor at 0 to prevent floating-point negatives)
4. `BUHI = sqrt(var)`

### Why dB scale instead of the original CV definition

The original framework defines BUHI as the coefficient of variation (CV = std/mean) on linear σ°. In this scene, linear σ° has skewness ≈ 160 (extremely heavy right tail), so both std and mean are dominated by a small number of bright pixels — making CV track the same information as BUII (correlation r ≈ 0.60).

Converting to dB reduces skewness to ≈ 0.7 (near-Gaussian), so the window standard deviation cleanly measures **land-cover heterogeneity** rather than outlier count. The dB mean is negative (σ° < 1 in linear), making a mean-normalized ratio unstable; therefore std is reported directly in dB units without normalization.

This transformation is equivalent to a standard log-transform applied to stabilize a heavy-tailed distribution before computing spread statistics.

### Output range

| Statistic | Value (dB) |
|-----------|------------|
| Min | 0.889 |
| p1 | 1.305 |
| p50 | 2.223 |
| p99 | 4.650 |
| Max | 9.916 |

### Interpretation

- **High (> ~4 dB)**: large variation in backscatter within the window → mixed land cover, irregular building arrangement, transition zone
- **Low (< ~1.5 dB)**: uniform backscatter → homogeneous surface (open water, dense forest, uniform farmland, or uniformly built-up area)
- Represents **spatial heterogeneity** — a proxy for **land-cover mixing and settlement irregularity**

---

## 3. Harmonic Mean (Sprawl Balance Index)

### Formula

$$\text{SBI} = \frac{2 \cdot \text{BUII}_s \cdot \text{BUHI}_s}{\text{BUII}_s + \text{BUHI}_s}$$

where $\text{BUII}_s$ and $\text{BUHI}_s$ are percentile-stretched versions of BUII and BUHI (each independently stretched to [0, 1] using p1–p99 of the scene).

Undefined when both are zero; set to 0 in that case.

### Conceptual basis

This is structurally identical to the **F1-score** in information retrieval (harmonic mean of precision and recall). It is maximized when both components are **simultaneously high and balanced**, and is strongly penalized when either component is low — more so than the arithmetic mean.

$$\text{SBI} = 0 \iff \text{BUII}_s = 0\ \text{or}\ \text{BUHI}_s = 0$$
$$\text{SBI} = 1 \iff \text{BUII}_s = \text{BUHI}_s = 1$$

### Output range

| Statistic | Value |
|-----------|-------|
| Min | 0.000 |
| p1 | 0.000 |
| p50 | 0.181 |
| p99 | 0.859 |
| Max | 1.000 |

### Interpretation

- **High (→ 1)**: both BUII and BUHI are high and balanced → strong evidence of urban sprawl morphology (moderate density with high heterogeneity)
- **Low (→ 0)**: one or both indices are low → either homogeneous non-urban (both low), dense homogeneous urban (BUII high, BUHI low), or heterogeneous but low-density surface such as water edges or mountain shadows (BUHI high, BUII low)
- Water bodies and mountain shadows are naturally suppressed because BUII ≈ 0 drives SBI toward 0

---

## 4. Dominance Index

### Formula

$$\text{Dominance} = \text{BUHI}_s - \text{BUII}_s$$

where $\text{BUII}_s$ and $\text{BUHI}_s$ are the same percentile-stretched values used in SBI.

### Output range

| Statistic | Value |
|-----------|-------|
| Min | −0.966 |
| p1 | −0.235 |
| p50 | +0.102 |
| p99 | +0.609 |
| Max | +0.900 |

### Interpretation

| Value | Meaning |
|-------|---------|
| **Strongly positive (→ +1)** | BUHI >> BUII: high heterogeneity, low density → sprawl candidate or water/shadow edge |
| **Near zero** | BUHI ≈ BUII: balanced → strongest sprawl signature when SBI is also high |
| **Strongly negative (→ −1)** | BUII >> BUHI: high density, low heterogeneity → mature urban core |

Dominance alone is ambiguous: a strongly positive value can indicate either sprawl **or** water/mountain shadow (both have low BUII). It must be interpreted jointly with SBI or with a water/shadow mask (BUII_stretched < 0.1).

### Visualization

In the dominance map (`sprawl_dominance_rgb_2025.tif`):
- **Color (hue)**: RdBu diverging colormap — blue = BUHI dominant, red = BUII dominant
- **Brightness**: modulated by SBI (harmonic mean) — dark pixels have low SBI regardless of dominance direction, naturally suppressing water and non-urban areas

---

## Joint interpretation framework

```
                    BUHI high
                        │
         Sprawl         │     Water / Shadow
         candidate      │     (exclude: BUII < 0.1)
                        │
BUII low ───────────────┼─────────────────── BUII high
                        │
   Non-urban            │     Urban core
   (forest, farmland)   │     (dense, homogeneous)
                        │
                    BUHI low
```

| Zone | BUII | BUHI | SBI | Dominance |
|------|------|------|-----|-----------|
| Urban core | High | Low | Low | Negative |
| **Sprawl / transition** | **Moderate** | **Moderate–High** | **High** | **Near zero** |
| Water / shadow | Very low | High | Very low | Strongly positive |
| Non-urban homogeneous | Low | Low | Very low | Near zero |

### Recommended workflow

1. Exclude water/shadow: `BUII_stretched < 0.1`
2. Use **SBI** to identify pixels where both indices are simultaneously elevated (sprawl likelihood score)
3. Use **Dominance** to assess whether the area is transitioning toward urban core (dominance decreasing over time) or remains sprawl-like

---

## File index

| File | Description |
|------|-------------|
| `outputs/2025/buii_2025.tif` | BUII raster ∈ [0, 1] |
| `outputs/2025/buhi_2025.tif` | BUHI raster (dB, ~0–10) |
| `outputs/2025/sprawl_index_harmonic_2025.tif` | SBI (harmonic mean of stretched BUII & BUHI) ∈ [0, 1] |
| `outputs/2025/sprawl_dominance_2025.tif` | Dominance (BUHI_s − BUII_s) ∈ [−1, 1] |
| `outputs/2025/sprawl_dominance_rgb_2025.tif` | RGB visualization of dominance × SBI brightness |

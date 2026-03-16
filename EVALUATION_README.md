# Wave-Harmonic Terrain Generation — Evaluation Replication Guide

This guide documents how to fully reproduce the Section 3.6 evaluation metrics from scratch.

---

## Prerequisites

```bash
pip install -r requirements.txt
```

Key dependencies: `numpy`, `scipy`, `matplotlib`, `fastapi`, `uvicorn`

---

## Step 1 — Generate Validation Dataset

Runs a deterministic sweep of **N=50 seeds** producing paired heightmaps for:
- **fBm Baseline** (Phase I + IV only)
- **Wave-Harmonic Model** (all 4 phases)

```bash
python extract_data.py
```

**Output:** `output/validation_samples/baseline_fbm/` and `output/validation_samples/wave_harmonic/`  
Each heightmap is exported as both `.npy` (NumPy float64) and `.raw` (float32 binary).

### Key Parameters Used

| Parameter | Value |
|:---|:---|
| Size | 256 × 256 |
| Noise Algorithm | `simplex` |
| Fractal Type | `fbm` |
| Octaves | 6 |
| Secondary Frequency | **2.5** |
| Wave Count (N) | 8 |
| Wave Intensity (α) | 0.3 |
| Thermal Erosion | Enabled |

---

## Step 2 — Run Metrics Evaluation

Computes all Section 3.6 metrics over the 50 sample pairs:

```bash
python evaluate_metrics.py
```

**Metrics calculated:**
- **Structural Complexity**: 2D FFT → Radial PSD → Log-log linear regression for spectral slope δ
- **Feature Diversity**: Laplacian curvature roughness, stratified by elevation threshold P=0.5
- **Memory Usage**: Peak allocation via `tracemalloc`
- **Latency / Throughput**: `time.perf_counter` over 5 full generation cycles
- **Big-O Complexity**: Theoretical asymptotic analysis per pipeline phase

---

## Step 3 — Generate Figures

Produces three publication-ready figures from the 50-sample dataset:

```bash
python plot_metrics.py
```

**Output:** `output/validation_samples/graphs/`

| Figure | Description |
|:---|:---|
| `fig1_psd_slope.png` | PSD log-log spectral slope comparison |
| `fig2_roughness_diff.png` | Differential roughness index bar chart |
| `fig3_terrain_compare.png` | Side-by-side heightmap renders |

---

## Step 4 — Run the Web Interface (Optional)

To visually test terrain parameters interactively:

```bash
# Terminal 1 — API backend
python -m server.main

# Terminal 2 — Frontend client
cd client
python -m http.server 3000
```

Open **http://localhost:3000** in your browser.  
API docs available at **http://localhost:8000/docs**.

---

## Reproducing a Specific Terrain

To reproduce the exact Seed 2 Wave-Harmonic terrain from Figure 3:

| Setting | Value |
|:---|:---|
| Seed | `2` |
| Algorithm | Simplex Noise |
| Fractal Type | FBM |
| Octaves | 6 |
| Enable Secondary Layer | ✅ |
| Blend Mode | ⚡ Wave Combination (Eq. 3) |
| Secondary Frequency | `2.5` |
| Wave Count | `8` |
| Wave Intensity | `0.3` |
| Thermal Erosion | ✅ |

---

## Algorithm Equations

| Phase | Equation |
|:---|:---|
| I — fBm | $P(x,y) = \sum_{i=0}^{k-1} a^i \cdot \text{noise}(f^i x,\ f^i y)$ |
| II — Wave Enhancement | $\psi(x,y) = \sum_{j=1}^{N} \alpha \cdot \sin(k_j \cdot p + \delta_j)$ |
| III — Combination | $H = P + P^2 \cdot \psi$ |
| IV — Thermal Erosion | $\Delta h = K_r \cdot (h_i - h_j - T) / 2$ |

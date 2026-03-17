# System Evaluation Report (Section 3.6, 3.7, 3.8)

Generated on: 2026-03-16 16:50:21

## Step 1: Data Generation
Status: Success (50 samples generated)

## Step 2: Algorithmic and Structural Metrics (Section 3.6)
```text
============================================================
 SYSTEM EVALUATION SUMMARY (Section 3.6)
============================================================
--- Algorithmic and Structural Metrics (50 Samples) ---

1. Structural Complexity (Spectral Analysis)
  fBm  PSD Slope (delta): mu = -3.3070  +/-  0.0645  (regression p = 0.0000)
  Wave PSD Slope (delta): mu = -3.3913  +/-  0.0785  (regression p = 0.0000)
  High-Frequency Energy Deviation: +20.87%

2. Feature Diversity (Roughness Index via Laplacian)
  Low-Elevation (P <= 0.5):
    fBm  Roughness: mu = 0.011900  +/-  0.000620
    Wave Roughness: mu = 0.011569  +/-  0.000564
  High-Elevation (P > 0.5):
    fBm  Roughness: mu = 0.011884  +/-  0.000610
    Wave Roughness: mu = 0.013120  +/-  0.000623
  Differential: Wave-Harmonic peaks are 1.13x rougher than valleys.

--- Service and Performance Metrics (Resolution: 256x256) ---
  Running latency test loop...

1. Capacity Tracking
  Peak Memory Usage: 14.76 MB

2. System Speed
  Latency (L): mu = 145.01 ms  +/-  14.40 ms
  Throughput (Th): 0.4520 MP/s

3. Theoretical Time Complexity (Big O) per phase:
  Phase I  (fBm Accumulation):    O(N^2 * k)      [k = octaves]
  Phase II (Wave Interference):   O(N^2 * J)      [J = wave_count]
  Phase III (Combination Logic):  O(N^2)          [constant-time matrix op]
  Phase IV (Thermal Erosion):     O(N^2 * I)      [I = erosion iterations]
  -----------------------------------------------------------
  Total Complexity:               O(N^2 * (k + J + 1 + I))
============================================================
 Evaluation Complete.
============================================================
```

## Step 3: Visual Validation
Status: Figures saved to `output/validation_samples/graphs/`

## Step 4: Benchmarking and Statistical Validation (Section 3.7 & 3.8)
```text
============================================================
  BENCHMARKING FRAMEWORK  (Sections 3.7 & 3.8)
============================================================
  Resolutions: (256, 512, 1024, 2048)
  Cycles per resolution: 15
  Variants: Raw Simplex | fBm | Wave-Harmonic

  >> Benchmarking 256×256 …

────────────────────────────────────────────────────────────
  Resolution: 256×256  |  n = 15 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       65.2 ± 6.8        14.77 ± 0.00             56.1
  fBm Standard (Baseline B)      145.6 ± 10.4        14.77 ± 0.00             68.0
  Wave-Harmonic (Proposed)       163.9 ± 15.3        14.76 ± 0.00             74.7

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.3446 ± 0.0527    0.9932    0.0000
  fBm Standard (Baseline B)      -3.3333 ± 0.0612    0.9933    0.0000
  Wave-Harmonic (Proposed)       -3.4173 ± 0.0615    0.9881    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0026  ✓ significant (p < 0.05)
    [Paired t-test] Memory: p = 0.0319  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0000  ✓ significant (p < 0.05)

  >> Benchmarking 512×512 …

────────────────────────────────────────────────────────────
  Resolution: 512×512  |  n = 15 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       385.9 ± 64.1        59.02 ± 0.00             82.9
  fBm Standard (Baseline B)      1317.9 ± 209.4        59.02 ± 0.00             87.7
  Wave-Harmonic (Proposed)       1397.9 ± 153.8        59.02 ± 0.00             89.3

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.3146 ± 0.0565    0.9945    0.0000
  fBm Standard (Baseline B)      -3.2934 ± 0.0646    0.9942    0.0000
  Wave-Harmonic (Proposed)       -3.3395 ± 0.0625    0.9906    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0181  ✓ significant (p < 0.05)
    [Paired t-test] Memory: p = 0.1445  ✗ not significant
    [Paired t-test] Spectral Slope: p = 0.0006  ✓ significant (p < 0.05)

  >> Benchmarking 1024×1024 …

────────────────────────────────────────────────────────────
  Resolution: 1024×1024  |  n = 15 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       1539.8 ± 71.9        236.03 ± 0.00             89.8
  fBm Standard (Baseline B)      5396.4 ± 206.3        236.03 ± 0.00             91.6
  Wave-Harmonic (Proposed)       5668.9 ± 138.2        236.03 ± 0.00             91.8

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.2070 ± 0.0489    0.9906    0.0000
  fBm Standard (Baseline B)      -3.1859 ± 0.0553    0.9905    0.0000
  Wave-Harmonic (Proposed)       -3.2078 ± 0.0524    0.9881    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Paired t-test] Latency: p = 0.0001  ✓ significant (p < 0.05)
    [Wilcoxon signed-rank] Memory: p = 0.2204  ✗ not significant
    [Paired t-test] Spectral Slope: p = 0.0219  ✓ significant (p < 0.05)

  >> Benchmarking 2048×2048 …

────────────────────────────────────────────────────────────
  Resolution: 2048×2048  |  n = 15 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       6076.2 ± 224.5        944.04 ± 0.00             92.0
  fBm Standard (Baseline B)      20859.4 ± 220.8        944.04 ± 0.00             92.3
  Wave-Harmonic (Proposed)       22297.0 ± 483.4        944.04 ± 0.00             92.2

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.0788 ± 0.0348    0.9886    0.0000
  fBm Standard (Baseline B)      -3.0630 ± 0.0392    0.9889    0.0000
  Wave-Harmonic (Proposed)       -3.0735 ± 0.0368    0.9873    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0001  ✓ significant (p < 0.05)
    [Paired t-test] Memory: p = 0.0415  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0975  ✗ not significant

============================================================
  Benchmarking complete.
============================================================

```


# System Evaluation Report (Section 3.6, 3.7, 3.8)

Generated on: 2026-03-16 17:18:56

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
  Latency (L): mu = 127.09 ms  +/-  9.79 ms
  Throughput (Th): 0.5156 MP/s

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
  Cycles per resolution: 50
  Variants: Raw Simplex | fBm | Wave-Harmonic

  >> Benchmarking 256×256 …

────────────────────────────────────────────────────────────
  Resolution: 256×256  |  n = 50 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       53.4 ± 10.0        14.76 ± 0.00             50.6
  fBm Standard (Baseline B)      124.4 ± 9.6        14.76 ± 0.00             58.5
  Wave-Harmonic (Proposed)       138.0 ± 10.5        14.76 ± 0.00             66.9

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.3294 ± 0.0539    0.9931    0.0000
  fBm Standard (Baseline B)      -3.3070 ± 0.0645    0.9932    0.0000
  Wave-Harmonic (Proposed)       -3.3913 ± 0.0785    0.9881    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0000  ✓ significant (p < 0.05)
    [Wilcoxon signed-rank] Memory: p = 0.0017  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0000  ✓ significant (p < 0.05)

  >> Benchmarking 512×512 …

────────────────────────────────────────────────────────────
  Resolution: 512×512  |  n = 50 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       344.5 ± 24.1        59.02 ± 0.00             81.1
  fBm Standard (Baseline B)      1168.2 ± 59.5        59.02 ± 0.00             91.2
  Wave-Harmonic (Proposed)       1265.8 ± 96.1        59.02 ± 0.00             91.4

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.2945 ± 0.0598    0.9943    0.0000
  fBm Standard (Baseline B)      -3.2635 ± 0.0685    0.9940    0.0000
  Wave-Harmonic (Proposed)       -3.3114 ± 0.0788    0.9904    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0000  ✓ significant (p < 0.05)
    [Wilcoxon signed-rank] Memory: p = 0.0305  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0000  ✓ significant (p < 0.05)

  >> Benchmarking 1024×1024 …

────────────────────────────────────────────────────────────
  Resolution: 1024×1024  |  n = 50 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       1500.3 ± 93.0        236.03 ± 0.00             93.0
  fBm Standard (Baseline B)      5227.4 ± 194.4        236.03 ± 0.00             93.9
  Wave-Harmonic (Proposed)       5526.8 ± 182.4        236.03 ± 0.00             94.5

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.1886 ± 0.0521    0.9906    0.0000
  fBm Standard (Baseline B)      -3.1600 ± 0.0582    0.9907    0.0000
  Wave-Harmonic (Proposed)       -3.1840 ± 0.0651    0.9882    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Paired t-test] Latency: p = 0.0000  ✓ significant (p < 0.05)
    [Wilcoxon signed-rank] Memory: p = 0.0020  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0000  ✓ significant (p < 0.05)

  >> Benchmarking 2048×2048 …

────────────────────────────────────────────────────────────
  Resolution: 2048×2048  |  n = 50 cycles
────────────────────────────────────────────────────────────

  Model                          Latency μ±σ (ms)       Memory μ±σ (MB)         CPU μ (%)
  ────────────────────────────── ────────────────────── ────────────────────── ──────────
  Raw Simplex (Baseline A)       5696.3 ± 234.2        944.04 ± 0.00             95.7
  fBm Standard (Baseline B)      19905.0 ± 1316.8        944.04 ± 0.00             96.1
  Wave-Harmonic (Proposed)       21020.6 ± 781.6        944.04 ± 0.00             96.3

  Model                          Slope δ μ±σ          R² μ         p (regression)
  ────────────────────────────── ──────────────────── ────────── ────────────────
  Raw Simplex (Baseline A)       -3.0654 ± 0.0371    0.9889    0.0000
  fBm Standard (Baseline B)      -3.0446 ± 0.0410    0.9893    0.0000
  Wave-Harmonic (Proposed)       -3.0567 ± 0.0453    0.9877    0.0000

  Statistical Validation (fBm Baseline B vs Wave-Harmonic):
    [Wilcoxon signed-rank] Latency: p = 0.0000  ✓ significant (p < 0.05)
    [Wilcoxon signed-rank] Memory: p = 0.0001  ✓ significant (p < 0.05)
    [Paired t-test] Spectral Slope: p = 0.0003  ✓ significant (p < 0.05)

============================================================
  Benchmarking complete.
============================================================

```


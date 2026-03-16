"""
Evaluation Metrics Script (Section 3.6 + 3.8)

Dual-faceted measurement framework:
1. Algorithmic and Structural Metrics  — PSD spectral slope (delta) + Roughness via Laplacian
2. Service and Performance Metrics     — Latency (mu +/- sigma), Throughput, Memory
3. Statistical Validation (Sec 3.8)   — Spectral regression p-values, mu +/- sigma format

Processes N=50 paired samples (fBm vs Wave-Harmonic) from extract_data.py output.
"""

import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.ndimage import laplace

sys.path.insert(0, str(Path(__file__).parent.absolute()))
from core.terrain_engine import TerrainEngine, TerrainConfig


# ─────────────────────────────────────────────────────────────
# Metric functions
# ─────────────────────────────────────────────────────────────

def compute_spectral_slope(heightmap):
    """
    Computes Structural Complexity via PSD (FFT + log-log regression).
    Returns (slope_delta, high_freq_energy, p_value).
    p_value from scipy.stats.linregress for Section 3.8 significance.
    """
    fft = np.fft.fft2(heightmap)
    power = np.abs(np.fft.fftshift(fft)) ** 2

    h, w = heightmap.shape
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)

    max_r = min(cx, cy)
    rp = np.zeros(max_r)
    cnt = np.zeros(max_r)

    for i in range(h):
        for j in range(w):
            ri = r[i, j]
            if ri < max_r:
                rp[ri] += power[i, j]
                cnt[ri] += 1

    mask = cnt > 0
    rp[mask] /= cnt[mask]
    freqs = np.arange(max_r)

    valid = (freqs > 1) & (rp > 0)
    if np.sum(valid) > 2:
        log_f = np.log(freqs[valid])
        log_p = np.log(rp[valid])
        slope, _, _, p_val, _ = stats.linregress(log_f, log_p)
    else:
        slope, p_val = 0.0, 1.0

    high_freq_energy = np.sum(rp[max_r // 4:])
    return slope, high_freq_energy, p_val


def compute_roughness_differential(heightmap, split=0.5):
    """
    Computes roughness via Laplacian curvature, split by elevation.
    Returns (low_elevation_roughness, high_elevation_roughness).
    """
    curv = np.abs(laplace(heightmap))
    low = np.mean(curv[heightmap <= split]) if np.any(heightmap <= split) else 0.0
    high = np.mean(curv[heightmap > split]) if np.any(heightmap > split) else 0.0
    return low, high


# ─────────────────────────────────────────────────────────────
# Structural metrics
# ─────────────────────────────────────────────────────────────

def evaluate_structural_metrics(sample_dir):
    out_path = Path(sample_dir)
    baseline_dir = out_path / "baseline_fbm"
    wave_dir = out_path / "wave_harmonic"

    if not baseline_dir.exists() or not wave_dir.exists():
        print(f"Error: sample directories not found at {out_path}.")
        print("Run `python extract_data.py` first.")
        return

    fbm_files = sorted(baseline_dir.glob("*.npy"))
    wave_files = sorted(wave_dir.glob("*.npy"))
    n = min(len(list(fbm_files)), len(list(wave_files)))
    fbm_files = sorted(baseline_dir.glob("*.npy"))
    wave_files = sorted(wave_dir.glob("*.npy"))

    print(f"--- Algorithmic and Structural Metrics ({n} Samples) ---")

    fbm_slopes, fbm_energies, fbm_pvals = [], [], []
    wave_slopes, wave_energies, wave_pvals = [], [], []
    fbm_r_low, fbm_r_high = [], []
    wave_r_low, wave_r_high = [], []

    for i, (f_fbm, f_wave) in enumerate(zip(sorted(baseline_dir.glob("*.npy")),
                                             sorted(wave_dir.glob("*.npy")))):
        if i >= n:
            break
        h_fbm = np.load(f_fbm)
        h_wave = np.load(f_wave)

        s_fbm, e_fbm, p_fbm = compute_spectral_slope(h_fbm)
        s_wv,  e_wv,  p_wv  = compute_spectral_slope(h_wave)
        fbm_slopes.append(s_fbm);  fbm_energies.append(e_fbm);  fbm_pvals.append(p_fbm)
        wave_slopes.append(s_wv);  wave_energies.append(e_wv);  wave_pvals.append(p_wv)

        rl_fbm, rh_fbm = compute_roughness_differential(h_fbm)
        rl_wv,  rh_wv  = compute_roughness_differential(h_wave)
        fbm_r_low.append(rl_fbm);  fbm_r_high.append(rh_fbm)
        wave_r_low.append(rl_wv);  wave_r_high.append(rh_wv)

    # Aggregates
    mu_fs = np.mean(fbm_slopes);   sd_fs = np.std(fbm_slopes)
    mu_ws = np.mean(wave_slopes);  sd_ws = np.std(wave_slopes)

    mu_fe = np.mean(fbm_energies)
    mu_we = np.mean(wave_energies)
    dev_pct = ((mu_we - mu_fe) / mu_fe) * 100
    sign = '+' if dev_pct >= 0 else ''

    mu_fp = np.mean(fbm_pvals)
    mu_wp = np.mean(wave_pvals)

    print("\n1. Structural Complexity (Spectral Analysis)")
    print(f"  fBm  PSD Slope (delta): mu = {mu_fs:.4f}  +/-  {sd_fs:.4f}  (regression p = {mu_fp:.4f})")
    print(f"  Wave PSD Slope (delta): mu = {mu_ws:.4f}  +/-  {sd_ws:.4f}  (regression p = {mu_wp:.4f})")
    print(f"  High-Frequency Energy Deviation: {sign}{dev_pct:.2f}%")

    print("\n2. Feature Diversity (Roughness Index via Laplacian)")
    print("  Low-Elevation (P <= 0.5):")
    print(f"    fBm  Roughness: mu = {np.mean(fbm_r_low):.6f}  +/-  {np.std(fbm_r_low):.6f}")
    print(f"    Wave Roughness: mu = {np.mean(wave_r_low):.6f}  +/-  {np.std(wave_r_low):.6f}")
    print("  High-Elevation (P > 0.5):")
    print(f"    fBm  Roughness: mu = {np.mean(fbm_r_high):.6f}  +/-  {np.std(fbm_r_high):.6f}")
    print(f"    Wave Roughness: mu = {np.mean(wave_r_high):.6f}  +/-  {np.std(wave_r_high):.6f}")

    diff_val = np.mean(wave_r_high) / np.mean(wave_r_low) if np.mean(wave_r_low) > 0 else 0
    print(f"  Differential: Wave-Harmonic peaks are {diff_val:.2f}x rougher than valleys.")


# ─────────────────────────────────────────────────────────────
# Service and performance metrics
# ─────────────────────────────────────────────────────────────

def evaluate_service_metrics(size=256, iterations=15):
    """
    Latency (mu +/- sigma), Throughput, and Peak Memory.
    """
    print(f"\n--- Service and Performance Metrics (Resolution: {size}x{size}) ---")

    config = TerrainConfig(
        seed=100, size=size,
        noise_algorithm="simplex", fractal_type="fbm",
        enable_secondary_noise=True,
        secondary_frequency=2.5,
        blend_mode="wave_combination",
        wave_count=8, wave_intensity=0.3,
        enable_thermal=True,
    )
    engine = TerrainEngine(config)

    # Peak memory
    tracemalloc.start()
    _ = engine.generate()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak_mem / (1024 * 1024)

    # Latency loop
    print("  Running latency test loop...")
    latencies = []
    for i in range(iterations):
        engine.config.seed = 200 + i
        t0 = time.perf_counter()
        _ = engine.generate()
        latencies.append((time.perf_counter() - t0) * 1000)

    mu_lat = np.mean(latencies)
    sd_lat = np.std(latencies)
    throughput = (size * size) / (mu_lat / 1000.0) / 1_000_000.0

    print("\n1. Capacity Tracking")
    print(f"  Peak Memory Usage: {peak_mb:.2f} MB")

    print("\n2. System Speed")
    print(f"  Latency (L): mu = {mu_lat:.2f} ms  +/-  {sd_lat:.2f} ms")
    print(f"  Throughput (Th): {throughput:.4f} MP/s")

    print("\n3. Theoretical Time Complexity (Big O) per phase:")
    print("  Phase I  (fBm Accumulation):    O(N^2 * k)      [k = octaves]")
    print("  Phase II (Wave Interference):   O(N^2 * J)      [J = wave_count]")
    print("  Phase III (Combination Logic):  O(N^2)          [constant-time matrix op]")
    print("  Phase IV (Thermal Erosion):     O(N^2 * I)      [I = erosion iterations]")
    print("  -----------------------------------------------------------")
    print("  Total Complexity:               O(N^2 * (k + J + 1 + I))")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(" SYSTEM EVALUATION SUMMARY (Section 3.6)")
    print("=" * 60)

    evaluate_structural_metrics("output/validation_samples")
    evaluate_service_metrics(size=256, iterations=15)

    print("=" * 60)
    print(" Evaluation Complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

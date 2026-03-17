"""
benchmark_framework.py — Section 3.7 & 3.8 Benchmarking Framework

Covers:
  3.7 — Multi-resolution performance benchmarking (256, 512, 1024, 2048)
       — n=50 independent cycles per resolution
       — Three-way baseline comparison (Raw → fBm → Wave-Harmonic)
       — Mean (μ) ± Standard Deviation (σ) per metric
       — CPU Utilization (%) via psutil

  3.8 — Paired t-test (or Wilcoxon) on latency and memory
       — p-values on PSD slope regression comparison
       — Normality check (Shapiro-Wilk) to select statistical test
"""

import sys
import time
import tracemalloc
import threading
from pathlib import Path

import numpy as np
import psutil
from scipy import stats
from scipy.ndimage import laplace

sys.path.insert(0, str(Path(__file__).parent.absolute()))
from core.terrain_engine import TerrainEngine, TerrainConfig


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _make_config(variant: str, size: int, seed: int) -> TerrainConfig:
    """Return TerrainConfig for one of the three comparison variants."""
    if variant == "raw":
        return TerrainConfig(
            seed=seed, size=size,
            noise_algorithm="simplex", fractal_type="none",
            enable_secondary_noise=False,
            enable_hydraulic=False, enable_thermal=False,
        )
    elif variant == "fbm":
        return TerrainConfig(
            seed=seed, size=size,
            noise_algorithm="simplex", fractal_type="fbm",
            octaves=6, enable_secondary_noise=False,
            enable_thermal=True,
        )
    else:  # wave_harmonic
        return TerrainConfig(
            seed=seed, size=size,
            noise_algorithm="simplex", fractal_type="fbm",
            octaves=6,
            enable_secondary_noise=True,
            secondary_frequency=2.5,
            blend_mode="wave_combination",
            wave_count=8,
            wave_intensity=0.3,
            enable_thermal=True,
        )


def _measure_cpu(stop_event: threading.Event, readings: list):
    """Background thread that samples CPU utilization every 100 ms."""
    proc = psutil.Process()
    while not stop_event.is_set():
        readings.append(proc.cpu_percent(interval=0.1))


def _psd_slope_and_pvalue(heightmap: np.ndarray):
    """Return (slope, r², p_value) from log-log linear regression of PSD."""
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
    if np.sum(valid) < 3:
        return 0.0, 0.0, 1.0

    log_f = np.log(freqs[valid])
    log_p = np.log(rp[valid])
    slope, intercept, r_val, p_val, _ = stats.linregress(log_f, log_p)
    return slope, r_val ** 2, p_val


def _roughness(heightmap: np.ndarray, split: float = 0.5):
    curv = np.abs(laplace(heightmap))
    low = np.mean(curv[heightmap <= split]) if np.any(heightmap <= split) else 0.0
    high = np.mean(curv[heightmap > split]) if np.any(heightmap > split) else 0.0
    return low, high


# ─────────────────────────────────────────────────────────────
# Core benchmark for a single resolution
# ─────────────────────────────────────────────────────────────

def benchmark_resolution(size: int, n_cycles: int = 50) -> dict:
    """
    Run n_cycles for all three variants at a given resolution.
    Returns a dict of results for 3.7 and 3.8 reporting.
    """
    variants = ["raw", "fbm", "wave_harmonic"]
    results = {v: {"latencies": [], "memories": [], "cpu": [], "slopes": [], "r2": [], "pvals_slope": []} for v in variants}

    engine = TerrainEngine()

    for cycle in range(n_cycles):
        seed = cycle + 1
        for v in variants:
            cfg = _make_config(v, size, seed)

            # --- CPU tracking thread ---
            stop_evt = threading.Event()
            cpu_readings = []
            cpu_thread = threading.Thread(target=_measure_cpu, args=(stop_evt, cpu_readings), daemon=True)

            # --- Memory tracking ---
            tracemalloc.start()

            # --- Latency ---
            cpu_thread.start()
            t0 = time.perf_counter()
            result = engine.generate(cfg)
            t1 = time.perf_counter()
            stop_evt.set()
            cpu_thread.join(timeout=1.0)

            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            latency_ms = (t1 - t0) * 1000
            mem_mb = peak_mem / (1024 * 1024)
            mean_cpu = float(np.mean(cpu_readings)) if cpu_readings else 0.0

            # --- Spectral analysis ---
            heightmap = result["heightmap"]
            slope, r2, pval = _psd_slope_and_pvalue(heightmap)

            results[v]["latencies"].append(latency_ms)
            results[v]["memories"].append(mem_mb)
            results[v]["cpu"].append(mean_cpu)
            results[v]["slopes"].append(slope)
            results[v]["r2"].append(r2)
            results[v]["pvals_slope"].append(pval)

    return results


# ─────────────────────────────────────────────────────────────
# Statistical tests (3.8)
# ─────────────────────────────────────────────────────────────

def _paired_test(a: list, b: list, label: str):
    """
    Performs Shapiro-Wilk normality check.
    If both distributions are normal → paired t-test.
    Otherwise → Wilcoxon signed-rank test.
    Reports μ ± σ and p-value.
    """
    a_arr = np.array(a)
    b_arr = np.array(b)

    _, p_a = stats.shapiro(a_arr)
    _, p_b = stats.shapiro(b_arr)
    both_normal = (p_a > 0.05) and (p_b > 0.05)

    if both_normal:
        stat, p_val = stats.ttest_rel(a_arr, b_arr)
        test_name = "Paired t-test"
    else:
        stat, p_val = stats.wilcoxon(a_arr, b_arr)
        test_name = "Wilcoxon signed-rank"

    sig = "✓ significant (p < 0.05)" if p_val < 0.05 else "✗ not significant"
    print(f"    [{test_name}] {label}: p = {p_val:.4f}  {sig}")
    return p_val


# ─────────────────────────────────────────────────────────────
# Report printing
# ─────────────────────────────────────────────────────────────

VARIANT_LABELS = {
    "raw":          "Raw Simplex (Baseline A)",
    "fbm":          "fBm Standard (Baseline B)",
    "wave_harmonic":"Wave-Harmonic (Proposed)",
}

def print_resolution_report(size: int, results: dict, n_cycles: int):
    print(f"\n{'─'*60}")
    print(f"  Resolution: {size}×{size}  |  n = {n_cycles} cycles")
    print(f"{'─'*60}")

    # ── Performance table ────────────────────────────────────
    print(f"\n  {'Model':<30} {'Latency μ±σ (ms)':<22} {'Memory μ±σ (MB)':<22} {'CPU μ (%)':>10}")
    print(f"  {'─'*30} {'─'*22} {'─'*22} {'─'*10}")

    for v, lbl in VARIANT_LABELS.items():
        lat = np.array(results[v]["latencies"])
        mem = np.array(results[v]["memories"])
        cpu = np.array(results[v]["cpu"])
        print(f"  {lbl:<30} {np.mean(lat):.1f} ± {np.std(lat):.1f}{'':<7} "
              f"{np.mean(mem):.2f} ± {np.std(mem):.2f}{'':<6} "
              f"{np.mean(cpu):>10.1f}")

    # ── Spectral slope table ─────────────────────────────────
    print(f"\n  {'Model':<30} {'Slope δ μ±σ':<20} {'R² μ':<10} {'p (regression)':>16}")
    print(f"  {'─'*30} {'─'*20} {'─'*10} {'─'*16}")

    for v, lbl in VARIANT_LABELS.items():
        sl = np.array(results[v]["slopes"])
        r2 = np.array(results[v]["r2"])
        pv = np.array(results[v]["pvals_slope"])
        print(f"  {lbl:<30} {np.mean(sl):.4f} ± {np.std(sl):.4f}    "
              f"{np.mean(r2):.4f}    {np.mean(pv):.4f}")

    # ── Statistical tests (3.8): fBm vs Wave-Harmonic ───────
    print(f"\n  Statistical Validation (fBm Baseline B vs Wave-Harmonic):")
    _paired_test(results["fbm"]["latencies"],  results["wave_harmonic"]["latencies"],  "Latency")
    _paired_test(results["fbm"]["memories"],   results["wave_harmonic"]["memories"],   "Memory")
    _paired_test(results["fbm"]["slopes"],     results["wave_harmonic"]["slopes"],     "Spectral Slope")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main(resolutions=(256, 512, 1024), n_cycles: int = 15):
    """
    Run the full benchmarking framework.
    Default: 256, 512, 1024 with n=15 cycles (fast). 
    For full spec compliance set resolutions=(256,512,1024,2048) and n_cycles=50.
    (2048 at n=50 can take 30+ min depending on the machine.)
    """
    print("=" * 60)
    print("  BENCHMARKING FRAMEWORK  (Sections 3.7 & 3.8)")
    print("=" * 60)
    print(f"  Resolutions: {resolutions}")
    print(f"  Cycles per resolution: {n_cycles}")
    print(f"  Variants: Raw Simplex | fBm | Wave-Harmonic")

    for size in resolutions:
        print(f"\n  >> Benchmarking {size}×{size} …")
        res = benchmark_resolution(size, n_cycles)
        print_resolution_report(size, res, n_cycles)

    print(f"\n{'='*60}")
    print("  Benchmarking complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Full resolution sweep as requested by the user
    main(resolutions=(256, 512, 1024, 2048), n_cycles=50)

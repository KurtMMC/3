"""
Data Extraction Script for Structural Validation

This script automates the "Systematic Sampling for Validation" as outlined in the experimental setup.
It utilizes an incremental seed range (1-50) to produce N=50 unique, deterministic samples.

For each seed, it generates:
1. fBm Baseline (Phase I + IV)
2. Wave-Harmonic Model (Phase I + II + III + IV)

Both algorithms start from identical topological foundations (same base noise parameters and seed).
The generated (N x N) outputs are exported as raw floating-point arrays (.npy and raw binary)
to allow for Fast Fourier Transform (FFT) and curvature analysis.
"""

import os
import sys
import numpy as np
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.terrain_engine import TerrainEngine, TerrainConfig


def extract_samples(size: int = 256, output_dir: str = "output/validation_samples"):
    """
    Generate and export N=50 deterministic samples for both fBm baseline
    and Wave-Harmonic models to allow for "paired-comparison".
    Exports as raw floating-point arrays.
    """
    out_path = Path(output_dir)
    
    # Create output directories for the two sets of models
    baseline_dir = out_path / "baseline_fbm"
    wave_dir = out_path / "wave_harmonic"
    
    baseline_dir.mkdir(parents=True, exist_ok=True)
    wave_dir.mkdir(parents=True, exist_ok=True)
    
    engine = TerrainEngine()
    
    total_seeds = 50
    print(f"Starting extraction of {total_seeds} paired samples (Size: {size}x{size})...")
    print("-" * 50)
    
    start_time = time.time()
    
    for seed in range(1, total_seeds + 1):
        # ----------------------------------------------------
        # 1. fBm Baseline Configuration (Topology & Erosion)
        # ----------------------------------------------------
        config_baseline = TerrainConfig(
            seed=seed,
            size=size,
            noise_algorithm="simplex",
            fractal_type="fbm",
            octaves=6,
            enable_secondary_noise=False, # Baseline lacks Wave Enhancement
            enable_thermal=True           # Erosion still applies
        )
        
        # ----------------------------------------------------
        # 2. Wave-Harmonic Configuration (Topology, Enhancement, Combination & Erosion)
        # ----------------------------------------------------
        config_wave = TerrainConfig(
            seed=seed,
            size=size,
            noise_algorithm="simplex",
            fractal_type="fbm",
            octaves=6,
            enable_secondary_noise=True,
            secondary_frequency=2.5,
            blend_mode="wave_combination", # Combination Logic (Contextual Scaling)
            wave_count=8,                  # Wave Enhancement Algorithm
            wave_intensity=0.3,
            enable_thermal=True            # Erosion
        )
        
        # Generate baseline
        res_baseline = engine.generate(config_baseline)
        h_base = res_baseline["heightmap"]
        
        # Generate Wave-Harmonic
        res_wave = engine.generate(config_wave)
        h_wave = res_wave["heightmap"]
        
        # Export as NumPy float arrays (.npy) for easy loading in SciPy/NumPy scripts
        # These are pure Floating-Point Arrays (N x N)
        np.save(baseline_dir / f"fbm_seed_{seed:02d}.npy", h_base)
        np.save(wave_dir / f"wave_seed_{seed:02d}.npy", h_wave)
        
        # Optionally, also export as RAW binary float32 for language-agnostic reading (C++, C#, etc.)
        h_base.astype(np.float32).tofile(baseline_dir / f"fbm_seed_{seed:02d}.raw")
        h_wave.astype(np.float32).tofile(wave_dir / f"wave_seed_{seed:02d}.raw")
        
        if seed % 10 == 0 or seed == 1:
            print(f"[{seed}/{total_seeds}] Exported floating-point arrays for seed {seed}")

    elapsed = time.time() - start_time
    print("-" * 50)
    print(f"Extraction complete in {elapsed:.2f} seconds.")
    print(f"Data saved to:\n  - {baseline_dir.absolute()}\n  - {wave_dir.absolute()}")
    print("Files are exported as both .npy and .raw (32-bit floating point) formats.")


if __name__ == "__main__":
    # You can change the size parameter here if you need higher/lower resolution arrays
    # default 256x256
    extract_samples(size=256)

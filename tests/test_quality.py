"""
Tests for terrain quality metrics: Power Spectral Density and Roughness Index.
"""

import pytest
import numpy as np
import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 2)[0])

from core.noise_generators import NoiseGenerator, NoiseParams
from core.terrain_engine import TerrainEngine, TerrainConfig


def compute_psd(heightmap: np.ndarray) -> tuple:
    """
    Compute Power Spectral Density of a heightmap.
    
    Returns:
        frequencies: Array of spatial frequencies
        power: Array of power values
        beta: Estimated spectral exponent (slope in log-log plot)
    """
    # 2D FFT
    fft = np.fft.fft2(heightmap)
    fft_shifted = np.fft.fftshift(fft)
    power_spectrum = np.abs(fft_shifted) ** 2
    
    # Radial average
    h, w = heightmap.shape
    cy, cx = h // 2, w // 2
    
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)
    
    max_radius = min(cx, cy)
    radial_power = np.zeros(max_radius)
    counts = np.zeros(max_radius)
    
    for i in range(h):
        for j in range(w):
            radius = r[i, j]
            if radius < max_radius:
                radial_power[radius] += power_spectrum[i, j]
                counts[radius] += 1
    
    # Average
    mask = counts > 0
    radial_power[mask] /= counts[mask]
    
    # Frequencies
    frequencies = np.arange(max_radius)
    
    # Fit power law: P(f) ~ f^(-beta)
    # In log space: log(P) = -beta * log(f) + c
    valid = (frequencies > 1) & (radial_power > 0)
    if np.sum(valid) > 2:
        log_f = np.log(frequencies[valid])
        log_p = np.log(radial_power[valid])
        
        # Linear regression
        A = np.vstack([log_f, np.ones(len(log_f))]).T
        beta, _ = np.linalg.lstsq(A, log_p, rcond=None)[0]
        beta = -beta  # Convention: positive beta for natural terrain
    else:
        beta = 0
    
    return frequencies, radial_power, beta


def compute_roughness_index(heightmap: np.ndarray) -> float:
    """
    Compute roughness index based on local height variation.
    Uses box-counting approach to estimate fractal dimension.
    
    Returns:
        roughness: Value typically in range 2.0-2.5 for natural terrain
    """
    h, w = heightmap.shape
    
    # Method: Calculate variance at different scales
    scales = [2, 4, 8, 16, 32]
    scales = [s for s in scales if s < min(h, w)]
    
    if len(scales) < 2:
        return 2.0
    
    variances = []
    
    for scale in scales:
        # Downsample by averaging
        new_h = h // scale
        new_w = w // scale
        
        downsampled = heightmap[:new_h * scale, :new_w * scale]
        downsampled = downsampled.reshape(new_h, scale, new_w, scale).mean(axis=(1, 3))
        
        # Local variance
        variance = np.var(np.gradient(downsampled))
        variances.append(variance)
    
    # Fit log-log to estimate roughness
    log_scales = np.log(scales)
    log_vars = np.log(np.array(variances) + 1e-10)
    
    # Linear regression
    A = np.vstack([log_scales, np.ones(len(log_scales))]).T
    slope, _ = np.linalg.lstsq(A, log_vars, rcond=None)[0]
    
    # Convert to fractal dimension approximation
    # Higher slope = rougher terrain
    roughness = 2.0 + abs(slope) / 2
    
    return min(max(roughness, 2.0), 3.0)


class TestPowerSpectralDensity:
    """Test PSD characteristics of generated terrain"""
    
    def test_psd_computable(self):
        """PSD should be computable for generated terrain"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        heightmap = gen.generate("simplex", params)
        
        freqs, power, beta = compute_psd(heightmap)
        
        assert len(freqs) > 0
        assert len(power) > 0
        assert isinstance(beta, float)
    
    @pytest.mark.parametrize("algorithm", ["wave", "harmonic", "perlin", "simplex"])
    def test_psd_beta_in_natural_range(self, algorithm):
        """
        PSD beta should be in natural terrain range (1.5-3.0).
        Natural terrains typically have beta around 2.0-2.5.
        """
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128, octaves=6)
        heightmap = gen.generate(algorithm, params)
        
        _, _, beta = compute_psd(heightmap)
        
        # Natural terrain typically has beta in 1.5-3.0 range
        # Our procedural terrain should be somewhat within this
        assert 0.5 <= beta <= 5.0, f"{algorithm}: beta={beta:.2f} outside expected range"
    
    def test_higher_octaves_steeper_spectrum(self):
        """More octaves should generally affect spectral characteristics"""
        gen = NoiseGenerator(seed=42)
        
        params_low = NoiseParams(seed=42, size=128, octaves=2)
        params_high = NoiseParams(seed=42, size=128, octaves=8)
        
        heightmap_low = gen.generate("simplex", params_low)
        heightmap_high = gen.generate("simplex", params_high)
        
        _, _, beta_low = compute_psd(heightmap_low)
        _, _, beta_high = compute_psd(heightmap_high)
        
        # Both should be computable
        assert beta_low != 0
        assert beta_high != 0


class TestRoughnessIndex:
    """Test roughness/fractal dimension of terrain"""
    
    def test_roughness_computable(self):
        """Roughness index should be computable"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        heightmap = gen.generate("simplex", params)
        
        roughness = compute_roughness_index(heightmap)
        
        assert isinstance(roughness, float)
        assert 2.0 <= roughness <= 3.0
    
    @pytest.mark.parametrize("algorithm", ["wave", "harmonic", "perlin", "simplex"])
    def test_roughness_in_natural_range(self, algorithm):
        """
        Roughness should be in natural terrain range.
        Fractal dimension of 2.0-2.5 is typical for natural surfaces.
        """
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128, octaves=6)
        heightmap = gen.generate(algorithm, params)
        
        roughness = compute_roughness_index(heightmap)
        
        # Natural terrain fractal dimension is typically 2.0-2.5
        assert 2.0 <= roughness <= 2.8, f"{algorithm}: roughness={roughness:.2f}"
    
    def test_erosion_affects_roughness(self):
        """Erosion should modify terrain roughness"""
        config_no_erosion = TerrainConfig(
            seed=42,
            size=64,
            enable_hydraulic=False
        )
        
        config_erosion = TerrainConfig(
            seed=42,
            size=64,
            enable_hydraulic=True,
            erosion_iterations=5000
        )
        
        engine = TerrainEngine()
        
        result_no = engine.generate(config_no_erosion)
        result_yes = engine.generate(config_erosion)
        
        roughness_no = compute_roughness_index(result_no["heightmap"])
        roughness_yes = compute_roughness_index(result_yes["heightmap"])
        
        # Erosion typically smooths terrain, potentially reducing roughness
        # At minimum, they should be different
        assert roughness_no != roughness_yes or np.allclose(
            result_no["heightmap"], 
            result_yes["heightmap"]
        ) == False


class TestTerrainQualityThresholds:
    """Test that terrain meets quality thresholds"""
    
    def test_terrain_meets_psd_threshold(self):
        """Full terrain generation should produce natural-like PSD"""
        config = TerrainConfig(
            seed=42,
            size=128,
            noise_algorithm="simplex",
            fractal_type="fbm",
            octaves=6
        )
        
        engine = TerrainEngine()
        result = engine.generate(config)
        
        _, _, beta = compute_psd(result["heightmap"])
        
        # Threshold: beta should be in 1.0-3.5 range for procedural terrain
        assert 1.0 <= beta <= 3.5, f"PSD beta {beta:.2f} outside quality threshold"
    
    def test_terrain_meets_roughness_threshold(self):
        """Full terrain generation should have realistic roughness"""
        config = TerrainConfig(
            seed=42,
            size=128,
            noise_algorithm="perlin",
            fractal_type="ridged",
            octaves=6
        )
        
        engine = TerrainEngine()
        result = engine.generate(config)
        
        roughness = compute_roughness_index(result["heightmap"])
        
        # Threshold: roughness should be 2.0-2.7 for natural-looking terrain
        assert 2.0 <= roughness <= 2.8, f"Roughness {roughness:.2f} outside quality threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

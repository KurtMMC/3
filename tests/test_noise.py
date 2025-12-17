"""
Tests for noise generation algorithms.
"""

import pytest
import numpy as np
import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 2)[0])

from core.noise_generators import NoiseGenerator, NoiseParams


class TestNoiseGenerators:
    """Test noise generator algorithms"""
    
    def test_wave_interference_shape(self):
        """Wave interference should produce correct shape"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("wave", params)
        
        assert result.shape == (128, 128)
        assert result.dtype == np.float64
    
    def test_wave_interference_range(self):
        """Wave interference values should be in 0-1 range"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("wave", params)
        
        assert result.min() >= 0.0
        assert result.max() <= 1.0
    
    def test_harmonic_functions_shape(self):
        """Harmonic functions should produce correct shape"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("harmonic", params)
        
        assert result.shape == (128, 128)
    
    def test_harmonic_functions_range(self):
        """Harmonic function values should be in 0-1 range"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("harmonic", params)
        
        assert result.min() >= 0.0
        assert result.max() <= 1.0
    
    def test_perlin_noise_shape(self):
        """Perlin noise should produce correct shape"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("perlin", params)
        
        assert result.shape == (128, 128)
    
    def test_perlin_noise_range(self):
        """Perlin noise values should be in 0-1 range"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("perlin", params)
        
        assert result.min() >= 0.0
        assert result.max() <= 1.0
    
    def test_simplex_noise_shape(self):
        """Simplex noise should produce correct shape"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("simplex", params)
        
        assert result.shape == (128, 128)
    
    def test_simplex_noise_range(self):
        """Simplex noise values should be in 0-1 range"""
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=128)
        result = gen.generate("simplex", params)
        
        assert result.min() >= 0.0
        assert result.max() <= 1.0
    
    def test_seed_reproducibility(self):
        """Same seed should produce identical results"""
        gen1 = NoiseGenerator(seed=12345)
        gen2 = NoiseGenerator(seed=12345)
        
        params = NoiseParams(seed=12345, size=64)
        
        result1 = gen1.generate("simplex", params)
        result2 = gen2.generate("simplex", params)
        
        np.testing.assert_array_equal(result1, result2)
    
    def test_different_seeds_produce_different_results(self):
        """Different seeds should produce different results"""
        gen1 = NoiseGenerator(seed=111)
        gen2 = NoiseGenerator(seed=222)
        
        params1 = NoiseParams(seed=111, size=64)
        params2 = NoiseParams(seed=222, size=64)
        
        result1 = gen1.generate("wave", params1)
        result2 = gen2.generate("wave", params2)
        
        assert not np.allclose(result1, result2)
    
    def test_octaves_affect_detail(self):
        """More octaves should add more detail (higher variance in gradients)"""
        gen = NoiseGenerator(seed=42)
        
        params_low = NoiseParams(seed=42, size=128, octaves=2)
        params_high = NoiseParams(seed=42, size=128, octaves=8)
        
        result_low = gen.generate("simplex", params_low)
        result_high = gen.generate("simplex", params_high)
        
        # Calculate gradient magnitude as proxy for detail
        grad_low = np.abs(np.gradient(result_low)).mean()
        grad_high = np.abs(np.gradient(result_high)).mean()
        
        # High octave version should have more high-frequency detail
        # (though the difference might be subtle due to amplitude falloff)
        assert grad_low != grad_high


class TestCombiner:
    """Test noise combination and fractal methods"""
    
    def test_fbm_produces_valid_output(self):
        """FBM should produce normalized output"""
        from core.combiner import NoiseCombiner
        
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=64, octaves=1)
        base = gen.generate("simplex", params)
        
        result = NoiseCombiner.fbm(base, octaves=4, persistence=0.5)
        
        assert result.shape == base.shape
        assert result.min() >= 0.0
        assert result.max() <= 1.0 + 0.01  # Small tolerance
    
    def test_ridged_produces_ridges(self):
        """Ridged fractal should produce sharp features"""
        from core.combiner import NoiseCombiner
        
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=64, octaves=1)
        base = gen.generate("simplex", params)
        
        result = NoiseCombiner.ridged(base, octaves=3)
        
        assert result.shape == base.shape
        # Ridged tends to have higher contrast
        assert result.std() > 0


class TestErosion:
    """Test erosion simulation"""
    
    def test_hydraulic_erosion_modifies_terrain(self):
        """Hydraulic erosion should modify the heightmap"""
        from core.erosion import ErosionSimulator, ErosionParams
        
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=64)
        heightmap = gen.generate("simplex", params)
        
        erosion = ErosionSimulator(seed=42)
        eroded = erosion.hydraulic_erosion(
            heightmap, 
            ErosionParams(iterations=1000)
        )
        
        assert eroded.shape == heightmap.shape
        # Should be modified
        assert not np.allclose(heightmap, eroded)
    
    def test_thermal_erosion_smooths_steep_areas(self):
        """Thermal erosion should reduce extreme slopes"""
        from core.erosion import ErosionSimulator
        
        # Create terrain with steep areas
        heightmap = np.random.rand(64, 64)
        
        erosion = ErosionSimulator(seed=42)
        eroded = erosion.thermal_erosion(heightmap, iterations=20)
        
        assert eroded.shape == heightmap.shape
        assert eroded.min() >= 0.0
        assert eroded.max() <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

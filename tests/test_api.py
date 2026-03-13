"""
Tests for API endpoints including latency benchmarks.
"""

import pytest
import time
import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 2)[0])

import numpy as np
from fastapi.testclient import TestClient
from server.main import app
from core.noise_generators import NoiseGenerator, NoiseParams
from core.combiner import NoiseCombiner
from core.erosion import ErosionSimulator, ErosionParams


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_returns_200(self):
        """Health endpoint should return 200"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_format(self):
        """Health response should have correct format"""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"


class TestTerrainGeneration:
    """Test terrain generation endpoint"""

    def test_generate_with_defaults(self):
        """Generation with default params should succeed"""
        response = client.post("/api/generate_terrain", json={})

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "heightmap" in data
        assert "normal_map" in data
        assert "splat_map" in data

    def test_generate_custom_size(self):
        """Generation with custom size should work"""
        response = client.post("/api/generate_terrain", json={
            "size": 128,
            "seed": 12345
        })

        assert response.status_code == 200
        data = response.json()

        assert data["size"] == 128
        assert data["seed"] == 12345

    def test_generate_all_algorithms(self):
        """All noise algorithms should work"""
        algorithms = ["wave", "harmonic", "perlin", "simplex"]

        for algo in algorithms:
            response = client.post("/api/generate_terrain", json={
                "noise_algorithm": algo,
                "size": 64
            })

            assert response.status_code == 200, f"Failed for {algo}"
            assert response.json()["success"] is True

    def test_generate_all_fractal_types(self):
        """All fractal types should work"""
        fractals = ["none", "fbm", "ridged", "billow"]

        for fractal in fractals:
            response = client.post("/api/generate_terrain", json={
                "fractal_type": fractal,
                "size": 64
            })

            assert response.status_code == 200, f"Failed for {fractal}"

    def test_invalid_size_rejected(self):
        """Invalid size should be rejected"""
        response = client.post("/api/generate_terrain", json={
            "size": 2000  # Above max
        })

        assert response.status_code == 422  # Validation error

    def test_generation_time_reported(self):
        """Response should include generation time"""
        response = client.post("/api/generate_terrain", json={"size": 64})
        data = response.json()

        assert "generation_time_ms" in data
        assert data["generation_time_ms"] > 0


class TestLatencyBenchmarks:
    """Latency benchmark tests"""

    @pytest.mark.parametrize("size,max_ms", [
        (64,  200),
        (128, 500),
        (256, 2000),
    ])
    def test_generation_latency(self, size, max_ms):
        """Generation should complete within time threshold"""
        start = time.perf_counter()

        response = client.post("/api/generate_terrain", json={
            "size": size,
            "noise_algorithm": "simplex",
            "fractal_type": "fbm",
            "enable_hydraulic": False,
            "enable_thermal": False
        })

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < max_ms, f"Size {size}: {elapsed_ms:.0f}ms > {max_ms}ms"

    def test_erosion_latency_acceptable(self):
        """Erosion enabled should still complete in reasonable time"""
        start = time.perf_counter()

        response = client.post("/api/generate_terrain", json={
            "size": 128,
            "enable_hydraulic": True,
            "erosion_iterations": 10000
        })

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 10000, f"Erosion took too long: {elapsed_ms:.0f}ms"


# ---------------------------------------------------------------------------
# Phase II + III — Wave Enhancement & Combination  (Eq. 2 & 3)
# ---------------------------------------------------------------------------

class TestWaveCombination:
    """Tests for Phase II wave enhancement (Eq. 2) and Phase III combination (Eq. 3)"""

    def test_wave_combination_blend_mode_via_api(self):
        """
        Phase III blend_mode='wave_combination' should succeed via API
        (H_final = P + P·ψ, Eq. 3).
        """
        response = client.post("/api/generate_terrain", json={
            "size": 64,
            "enable_secondary_noise": True,
            "blend_mode": "wave_combination",
            "wave_count": 6,
            "wave_intensity": 0.4,
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_wave_enhancement_psi_is_signed(self):
        """
        Phase II: ψ(x,y) must be a signed offset (not pre-normalised to [0,1])
        so the contextual scaling term P·ψ in Eq. 3 works correctly.
        """
        gen = NoiseGenerator(seed=42)
        params = NoiseParams(seed=42, size=64, frequency=3.0,
                             wave_count=8, wave_intensity=0.3)
        psi = gen.generate_wave_enhancement(params)

        assert psi.min() < 0, "ψ must contain negative values (signed offset)"
        assert psi.max() > 0, "ψ must contain positive values"

    def test_wave_combination_output_in_01(self):
        """
        Phase III: H_final = P + P·ψ must be clipped to [0, 1].
        """
        gen = NoiseGenerator(seed=99)
        params = NoiseParams(seed=99, size=64, frequency=3.0,
                             wave_count=8, wave_intensity=0.5)

        P   = gen.generate(algorithm="simplex", params=params)
        psi = gen.generate_wave_enhancement(params)
        H   = NoiseCombiner.wave_combination(P, psi)

        assert H.min() >= 0.0, f"H_final min {H.min()} < 0"
        assert H.max() <= 1.0, f"H_final max {H.max()} > 1"

    def test_contextual_scaling_effect(self):
        """
        Eq. 3 contextual scaling: high-elevation areas should exhibit
        more variance than low-elevation areas after wave combination.
        """
        gen = NoiseGenerator(seed=7)
        params = NoiseParams(seed=7, size=128, frequency=3.0,
                             wave_count=8, wave_intensity=0.8)

        P   = gen.generate(algorithm="perlin", params=params)
        psi = gen.generate_wave_enhancement(params)
        H   = NoiseCombiner.wave_combination(P, psi)

        delta = H - P   # distortion applied by wave combination

        high_mask = P > 0.7   # mountainous region (P ≈ 1)
        low_mask  = P < 0.3   # valley region      (P ≈ 0)

        if high_mask.sum() > 10 and low_mask.sum() > 10:
            high_std = delta[high_mask].std()
            low_std  = delta[low_mask].std()
            assert high_std > low_std, (
                f"Contextual scaling failed: mountain std {high_std:.4f} "
                f"should exceed valley std {low_std:.4f}"
            )


# ---------------------------------------------------------------------------
# Phase IV — Erosion  (Eq. 4 hydraulic + Eq. 5 thermal)
# ---------------------------------------------------------------------------

class TestErosion:
    """Tests for Phase IV erosion sub-models (Eq. 4 & 5)"""

    def _make_heightmap(self, size: int = 64, seed: int = 0) -> np.ndarray:
        """Helper: generate a reproducible Phase I heightmap."""
        gen = NoiseGenerator(seed=seed)
        params = NoiseParams(seed=seed, size=size, frequency=3.0, octaves=4)
        return gen.generate(algorithm="simplex", params=params)

    def test_hydraulic_erosion_reduces_peaks(self):
        """
        Eq. 4: Hydraulic erosion should lower the global maximum height
        as sediment is redistributed from peaks to valleys.
        """
        hmap = self._make_heightmap()
        sim  = ErosionSimulator(seed=0)
        params = ErosionParams(iterations=2000)

        eroded = sim.hydraulic_erosion(hmap, params)

        assert eroded.max() <= hmap.max() + 0.05, (
            "Hydraulic erosion should not increase peak height significantly"
        )
        # Sediment redistribution means the mean shouldn't drop drastically
        assert abs(eroded.mean() - hmap.mean()) < 0.1

    def test_hydraulic_erosion_output_in_01(self):
        """Eq. 4: Output must remain in [0, 1] after hydraulic erosion."""
        hmap   = self._make_heightmap()
        sim    = ErosionSimulator(seed=1)
        eroded = sim.hydraulic_erosion(hmap, ErosionParams(iterations=1000))

        assert eroded.min() >= 0.0
        assert eroded.max() <= 1.0

    def test_thermal_erosion_reduces_slope(self):
        """
        Eq. 5: Thermal erosion should smooth extreme slopes.
        Create a synthetic cliff and verify max slope decreases.
        """
        size = 64
        synthetic = np.zeros((size, size), dtype=np.float64)
        synthetic[:, size // 2:] = 1.0   # hard cliff at mid-point

        sim    = ErosionSimulator(seed=2)
        params = ErosionParams(talus_angle=0.3, thermal_rate=0.5)
        eroded = sim.thermal_erosion(synthetic, params=params, iterations=80)

        def max_slope(h):
            dx = np.abs(h[:, 1:] - h[:, :-1])
            dy = np.abs(h[1:, :] - h[:-1, :])
            return max(dx.max(), dy.max())

        before_slope = max_slope(synthetic)
        after_slope  = max_slope(eroded)

        assert after_slope < before_slope, (
            f"Thermal erosion did not reduce slope: {before_slope:.4f} → {after_slope:.4f}"
        )

    def test_thermal_erosion_uses_params(self):
        """
        Eq. 5: talus_angle and thermal_rate from ErosionParams must be
        respected — higher thermal_rate should produce more smoothing.
        """
        size = 64
        cliff = np.zeros((size, size), dtype=np.float64)
        cliff[:, size // 2:] = 1.0

        sim = ErosionSimulator(seed=3)

        mild   = sim.thermal_erosion(cliff.copy(),
                                     ErosionParams(talus_angle=0.5, thermal_rate=0.1),
                                     iterations=30)
        strong = sim.thermal_erosion(cliff.copy(),
                                     ErosionParams(talus_angle=0.5, thermal_rate=0.9),
                                     iterations=30)

        mild_range   = mild.max()   - mild.min()
        strong_range = strong.max() - strong.min()

        # Stronger erosion = more compressed height range (more smoothed)
        assert strong_range <= mild_range, (
            f"Higher thermal_rate should produce more smoothing: "
            f"mild range={mild_range:.4f}, strong range={strong_range:.4f}"
        )

    def test_talus_angle_param_forwarded(self):
        """
        Eq. 5: talus_angle and thermal_rate in TerrainRequest are accepted
        by the API without error.
        """
        response = client.post("/api/generate_terrain", json={
            "size": 64,
            "enable_thermal": True,
            "talus_angle": 0.2,
            "thermal_rate": 0.6,
        })
        assert response.status_code == 200
        assert response.json()["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for API endpoints including latency benchmarks.
"""

import pytest
import time
import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 2)[0])

from fastapi.testclient import TestClient
from server.main import app


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
        (64, 200),
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
        # Erosion is expensive, allow more time
        assert elapsed_ms < 10000, f"Erosion took too long: {elapsed_ms:.0f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

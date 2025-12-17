"""
API routes for terrain generation.
"""

import time
from fastapi import APIRouter, HTTPException

import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 2)[0])

from server.models import TerrainRequest, TerrainResponse, HealthResponse, ExportResponse
from server.serialization import (
    heightmap_to_png_base64,
    normal_map_to_png_base64,
    splat_map_to_png_base64
)
from server.export import create_export_package
from core.terrain_engine import TerrainEngine, TerrainConfig


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()


@router.post("/generate_terrain", response_model=TerrainResponse)
async def generate_terrain(request: TerrainRequest):
    """
    Generate terrain based on provided parameters.
    Returns heightmap, normal map, and splat map as base64 PNGs.
    """
    try:
        start_time = time.perf_counter()
        
        # Create configuration from request
        config = TerrainConfig(
            seed=request.seed,
            size=request.size,
            noise_algorithm=request.noise_algorithm,
            frequency=request.frequency,
            amplitude=request.amplitude,
            octaves=request.octaves,
            persistence=request.persistence,
            lacunarity=request.lacunarity,
            fractal_type=request.fractal_type,
            enable_hydraulic=request.enable_hydraulic,
            enable_thermal=request.enable_thermal,
            erosion_iterations=request.erosion_iterations,
            erosion_strength=request.erosion_strength,
            # Noise layer combination
            enable_secondary_noise=request.enable_secondary_noise,
            secondary_algorithm=request.secondary_algorithm,
            secondary_frequency=request.secondary_frequency,
            secondary_amplitude=request.secondary_amplitude,
            blend_mode=request.blend_mode,
            blend_weight=request.blend_weight
        )
        
        # Generate terrain
        engine = TerrainEngine(config)
        result = engine.generate()
        
        # Serialize outputs
        heightmap_b64 = heightmap_to_png_base64(result["heightmap"])
        normal_map_b64 = normal_map_to_png_base64(result["normal_map"])
        splat_map_b64 = splat_map_to_png_base64(result["splat_map"])
        
        generation_time = (time.perf_counter() - start_time) * 1000
        
        return TerrainResponse(
            success=True,
            seed=request.seed,
            size=request.size,
            heightmap=heightmap_b64,
            normal_map=normal_map_b64,
            splat_map=splat_map_b64,
            generation_time_ms=round(generation_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export_terrain", response_model=ExportResponse)
async def export_terrain(request: TerrainRequest):
    """
    Export terrain in multiple formats for Unity, Blender, and Godot.
    Returns OBJ mesh, RAW heightmaps (8/16-bit), and PNG textures.
    """
    try:
        # Create configuration from request
        config = TerrainConfig(
            seed=request.seed,
            size=request.size,
            noise_algorithm=request.noise_algorithm,
            frequency=request.frequency,
            amplitude=request.amplitude,
            octaves=request.octaves,
            persistence=request.persistence,
            lacunarity=request.lacunarity,
            fractal_type=request.fractal_type,
            enable_hydraulic=request.enable_hydraulic,
            enable_thermal=request.enable_thermal,
            erosion_iterations=request.erosion_iterations,
            erosion_strength=request.erosion_strength,
            enable_secondary_noise=request.enable_secondary_noise,
            secondary_algorithm=request.secondary_algorithm,
            secondary_frequency=request.secondary_frequency,
            secondary_amplitude=request.secondary_amplitude,
            blend_mode=request.blend_mode,
            blend_weight=request.blend_weight
        )
        
        # Generate terrain
        engine = TerrainEngine(config)
        result = engine.generate()
        
        # Create export package
        exports = create_export_package(
            result["heightmap"],
            result["normal_map"],
            result["splat_map"]
        )
        
        return ExportResponse(
            success=True,
            size=request.size,
            **exports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


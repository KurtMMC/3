"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class TerrainRequest(BaseModel):
    """Request model for terrain generation"""
    
    # Basic settings
    seed: int = Field(default=42, description="Random seed for reproducible generation")
    size: int = Field(default=256, ge=32, le=1024, description="Terrain size (32-1024)")
    
    # Noise settings
    noise_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = Field(
        default="simplex", 
        description="Base noise algorithm"
    )
    frequency: float = Field(default=3.0, ge=0.1, le=20.0, description="Base frequency")
    amplitude: float = Field(default=1.0, ge=0.1, le=2.0, description="Height amplitude")
    octaves: int = Field(default=6, ge=1, le=10, description="Noise octaves for detail")
    persistence: float = Field(default=0.5, ge=0.1, le=1.0, description="Amplitude falloff per octave")
    lacunarity: float = Field(default=2.0, ge=1.0, le=4.0, description="Frequency multiplier per octave")
    
    # Fractal settings
    fractal_type: Literal["none", "fbm", "ridged", "billow"] = Field(
        default="fbm",
        description="Fractal processing type"
    )
    
    # Erosion settings
    enable_hydraulic: bool = Field(default=False, description="Enable hydraulic erosion")
    enable_thermal: bool = Field(default=False, description="Enable thermal erosion")
    erosion_iterations: int = Field(default=30000, ge=1000, le=100000, description="Erosion iterations")
    erosion_strength: float = Field(default=0.3, ge=0.1, le=1.0, description="Erosion intensity")
    
    # Noise Layer Combination
    enable_secondary_noise: bool = Field(default=False, description="Enable secondary noise layer")
    secondary_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = Field(
        default="perlin",
        description="Secondary noise algorithm to combine with primary"
    )
    secondary_frequency: float = Field(default=5.0, ge=0.1, le=20.0, description="Secondary noise frequency")
    secondary_amplitude: float = Field(default=0.5, ge=0.1, le=2.0, description="Secondary noise amplitude")
    blend_mode: Literal["add", "multiply", "lerp", "min", "max"] = Field(
        default="add",
        description="How to blend primary and secondary noise"
    )
    blend_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight for blending (0=primary only, 1=secondary only)")


class TerrainResponse(BaseModel):
    """Response model for terrain generation"""
    
    success: bool
    seed: int
    size: int
    heightmap: str  # Base64 encoded PNG
    normal_map: str  # Base64 encoded PNG
    splat_map: str  # Base64 encoded PNG
    generation_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "seed": 42,
                "size": 256,
                "heightmap": "base64...",
                "normal_map": "base64...",
                "splat_map": "base64...",
                "generation_time_ms": 150.5
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"


class ExportResponse(BaseModel):
    """Response model for terrain export"""
    success: bool
    size: int
    obj: str  # Base64 OBJ mesh
    raw_16bit: str  # Base64 RAW heightmap (16-bit for Unity)
    raw_8bit: str  # Base64 RAW heightmap (8-bit)
    heightmap_png: str  # Base64 PNG heightmap
    normal_png: str  # Base64 PNG normal map


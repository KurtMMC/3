"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class TerrainRequest(BaseModel):
    """Request model for terrain generation"""
    
    # Basic settings
    seed: int = Field(default=42, description="Random seed for reproducible generation. Same seed + same settings = same terrain.")
    size: int = Field(default=256, ge=32, le=1024, description="Resolution of the terrain (width & height). Must be between 32 and 1024.")
    
    # Noise settings
    noise_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = Field(
        default="simplex", 
        description="The base noise algorithm used for terrain generation."
    )
    frequency: float = Field(default=3.0, ge=0.1, le=20.0, description="Base frequency of the noise. Higher values = more zoomed out.")
    amplitude: float = Field(default=1.0, ge=0.1, le=2.0, description="Height amplitude (vertical scale).")
    octaves: int = Field(default=6, ge=1, le=10, description="Number of noise layers (detail). Higher values = more fine detail.")
    persistence: float = Field(default=0.5, ge=0.1, le=1.0, description="Amplitude falloff per octave. Lower = smoother details.")
    lacunarity: float = Field(default=2.0, ge=1.0, le=4.0, description="Frequency multiplier per octave.")
    
    # Fractal settings
    fractal_type: Literal["none", "fbm", "ridged", "billow"] = Field(
        default="fbm",
        description="Fractal type determining how octaves are combined. 'ridged' creates sharp peaks, 'billow' creates rounded hills."
    )
    
    # Erosion settings
    enable_hydraulic: bool = Field(default=False, description="Simulate water erosion to create river channels and sediment.")
    enable_thermal: bool = Field(default=False, description="Simulate thermal erosion (material slippage) to smooth steep slopes.")
    erosion_iterations: int = Field(default=30000, ge=1000, le=100000, description="Number of erosion simulation drops/steps.")
    erosion_strength: float = Field(default=0.3, ge=0.1, le=1.0, description="Intensity of the erosion effect.")
    
    # Noise Layer Combination
    enable_secondary_noise: bool = Field(default=False, description="Enable a second independent noise layer to blend with the first.")
    secondary_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = Field(
        default="perlin",
        description="Algorithm for the secondary noise layer."
    )
    secondary_frequency: float = Field(default=5.0, ge=0.1, le=20.0, description="Frequency for the secondary noise layer.")
    secondary_amplitude: float = Field(default=0.5, ge=0.1, le=2.0, description="Amplitude for the secondary noise layer.")
    blend_mode: Literal["add", "multiply", "lerp", "min", "max", "wave_combination"] = Field(
        default="add",
        description="How to combine the primary and secondary noise layers. 'wave_combination' applies Phase III Eq. 3: H = P + P·ψ."
    )
    blend_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Mixing weight (0.0 = primary only, 1.0 = secondary only). Not used by wave_combination.")

    # Phase II — Wave Enhancement parameters (Eq. 2), used when blend_mode='wave_combination'
    wave_count: int = Field(default=8, ge=1, le=32, description="Phase II (Eq. 2): Number of superimposed waves (N). Higher = more geological complexity.")
    wave_intensity: float = Field(default=0.3, ge=0.0, le=2.0, description="Phase II (Eq. 2): Global wave amplitude scalar (α). Controls ridge height.")

    # Phase IV — Thermal erosion parameters (Eq. 5)
    talus_angle: float = Field(default=0.5, ge=0.01, le=2.0, description="Phase IV (Eq. 5): Slope threshold T for thermal slippage. Lower = more aggressive smoothing.")
    thermal_rate: float = Field(default=0.3, ge=0.01, le=1.0, description="Phase IV (Eq. 5): Material transfer rate Kr per thermal iteration.")


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


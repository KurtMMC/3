"""
Terrain Engine - Runtime execution pipeline.
Chains: Input → Noise → Combiner → Erosion → Output
"""

import numpy as np
from typing import Literal, Optional, Dict, Any
from dataclasses import dataclass, field

from .noise_generators import NoiseGenerator, NoiseParams
from .combiner import NoiseCombiner
from .erosion import ErosionSimulator, ErosionParams


@dataclass
class TerrainConfig:
    """Complete terrain generation configuration"""
    # Basic
    seed: int = 42
    size: int = 256
    
    # Noise
    noise_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = "simplex"
    frequency: float = 3.0
    amplitude: float = 1.0
    octaves: int = 6
    persistence: float = 0.5
    lacunarity: float = 2.0
    
    # Fractal
    fractal_type: Literal["none", "fbm", "ridged", "billow"] = "fbm"
    
    # Erosion
    enable_hydraulic: bool = False
    enable_thermal: bool = False
    erosion_iterations: int = 30000
    erosion_strength: float = 0.3
    
    # Noise Layer Combination
    enable_secondary_noise: bool = False
    secondary_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = "perlin"
    secondary_frequency: float = 5.0
    secondary_amplitude: float = 0.5
    blend_mode: Literal["add", "multiply", "lerp", "min", "max"] = "add"
    blend_weight: float = 0.5


class TerrainEngine:
    """
    Runtime execution engine for terrain generation.
    Orchestrates the full pipeline from parameters to output.
    """
    
    def __init__(self, config: Optional[TerrainConfig] = None):
        self.config = config or TerrainConfig()
        self._setup()
    
    def _setup(self):
        """Initialize generation components"""
        self.noise_gen = NoiseGenerator(self.config.seed)
        self.combiner = NoiseCombiner()
        self.erosion = ErosionSimulator(self.config.seed)
    
    def generate(self, config: Optional[TerrainConfig] = None) -> Dict[str, np.ndarray]:
        """
        Execute full terrain generation pipeline.
        
        Returns:
            Dict containing 'heightmap', 'normal_map', 'splat_map'
        """
        if config:
            self.config = config
            self._setup()
        
        # Step 1: Generate base noise
        noise_params = NoiseParams(
            seed=self.config.seed,
            size=self.config.size,
            frequency=self.config.frequency,
            amplitude=self.config.amplitude,
            octaves=self.config.octaves,
            persistence=self.config.persistence,
            lacunarity=self.config.lacunarity
        )
        
        heightmap = self.noise_gen.generate(
            algorithm=self.config.noise_algorithm,
            params=noise_params
        )
        
        # Step 1.5: Combine with secondary noise if enabled
        if self.config.enable_secondary_noise:
            secondary_params = NoiseParams(
                seed=self.config.seed + 1000,  # Different seed for variety
                size=self.config.size,
                frequency=self.config.secondary_frequency,
                amplitude=self.config.secondary_amplitude,
                octaves=self.config.octaves,
                persistence=self.config.persistence,
                lacunarity=self.config.lacunarity
            )
            
            secondary_heightmap = self.noise_gen.generate(
                algorithm=self.config.secondary_algorithm,
                params=secondary_params
            )
            
            # Blend the two noise layers
            heightmap = self.combiner.combine(
                layers=[heightmap, secondary_heightmap],
                weights=[1.0 - self.config.blend_weight, self.config.blend_weight],
                mode=self.config.blend_mode
            )
        
        # Step 2: Apply fractal processing
        if self.config.fractal_type == "fbm":
            heightmap = self.combiner.fbm(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence
            )
        elif self.config.fractal_type == "ridged":
            heightmap = self.combiner.ridged(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence
            )
        elif self.config.fractal_type == "billow":
            heightmap = self.combiner.billow(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence
            )
        
        # Step 3: Apply erosion
        if self.config.enable_hydraulic or self.config.enable_thermal:
            erosion_params = ErosionParams(
                iterations=self.config.erosion_iterations,
                erosion=self.config.erosion_strength,
                deposition=self.config.erosion_strength
            )
            heightmap = self.erosion.apply(
                heightmap,
                hydraulic=self.config.enable_hydraulic,
                thermal=self.config.enable_thermal,
                hydraulic_params=erosion_params
            )
        
        # Step 4: Generate derivative maps
        normal_map = self._compute_normal_map(heightmap)
        splat_map = self._compute_splat_map(heightmap)
        
        return {
            "heightmap": heightmap,
            "normal_map": normal_map,
            "splat_map": splat_map
        }
    
    def _compute_normal_map(self, heightmap: np.ndarray) -> np.ndarray:
        """
        Compute normal map from heightmap using Sobel operator.
        RGB encodes XYZ normal direction.
        """
        # Compute gradients
        grad_x = np.zeros_like(heightmap)
        grad_y = np.zeros_like(heightmap)
        
        # Sobel-like gradient
        grad_x[:, 1:-1] = heightmap[:, 2:] - heightmap[:, :-2]
        grad_y[1:-1, :] = heightmap[2:, :] - heightmap[:-2, :]
        
        # Scale gradients
        strength = 2.0
        grad_x *= strength
        grad_y *= strength
        
        # Compute normals
        normal_x = -grad_x
        normal_y = -grad_y
        normal_z = np.ones_like(heightmap)
        
        # Normalize
        length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x /= length
        normal_y /= length
        normal_z /= length
        
        # Convert to 0-1 range for RGB
        normal_map = np.stack([
            (normal_x + 1) * 0.5,
            (normal_y + 1) * 0.5,
            (normal_z + 1) * 0.5
        ], axis=-1)
        
        return normal_map
    
    def _compute_splat_map(self, heightmap: np.ndarray) -> np.ndarray:
        """
        Compute splat map for texture blending.
        Channels: R=water/low, G=grass/mid, B=rock/high, A=snow/peaks
        """
        # Compute slope
        grad_x = np.zeros_like(heightmap)
        grad_y = np.zeros_like(heightmap)
        grad_x[:, 1:-1] = np.abs(heightmap[:, 2:] - heightmap[:, :-2])
        grad_y[1:-1, :] = np.abs(heightmap[2:, :] - heightmap[:-2, :])
        slope = np.sqrt(grad_x**2 + grad_y**2)
        
        # Height thresholds
        water = np.clip(1 - heightmap / 0.3, 0, 1) * (1 - slope * 2)
        grass = np.clip(1 - np.abs(heightmap - 0.4) / 0.2, 0, 1) * (1 - slope * 3)
        rock = np.clip(slope * 5, 0, 1) + np.clip((heightmap - 0.6) / 0.2, 0, 1) * 0.5
        snow = np.clip((heightmap - 0.75) / 0.25, 0, 1) * (1 - slope * 2)
        
        # Normalize
        total = water + grass + rock + snow + 0.001
        splat_map = np.stack([
            water / total,
            grass / total,
            rock / total,
            snow / total
        ], axis=-1)
        
        return splat_map

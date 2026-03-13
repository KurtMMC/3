"""
Terrain Engine - Runtime execution pipeline.

Full 4-phase algorithm:
  Phase I   — Base Noise Map P(x, y)           via fBm (Eq. 1)
  Phase II  — Wave Enhancement ψ(x, y)          (Eq. 2)   [optional]
  Phase III — Combination H_final = P + P·ψ     (Eq. 3)   [optional]
  Phase IV  — Erosion (hydraulic Eq. 4 + thermal Eq. 5)   [optional]
"""

import numpy as np
from typing import Literal, Optional, Dict
from dataclasses import dataclass

from .noise_generators import NoiseGenerator, NoiseParams
from .combiner import NoiseCombiner
from .erosion import ErosionSimulator, ErosionParams


@dataclass
class TerrainConfig:
    """Complete terrain generation configuration"""
    # Basic
    seed: int = 42
    size: int = 256

    # Phase I — fBm base noise (Eq. 1)
    noise_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = "simplex"
    frequency: float = 3.0
    amplitude: float = 1.0
    octaves: int = 6          # k — number of octave layers
    persistence: float = 0.5  # a — amplitude decay per octave
    lacunarity: float = 2.0   # f — frequency growth per octave

    # Fractal post-processing (applied to P before Phase II)
    fractal_type: Literal["none", "fbm", "ridged", "billow"] = "fbm"

    # Phase II & III — Wave Enhancement + Combination (Eq. 2 & 3)
    enable_secondary_noise: bool = False
    secondary_algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = "perlin"
    secondary_frequency: float = 5.0
    secondary_amplitude: float = 0.5
    blend_mode: Literal["add", "multiply", "lerp", "min", "max", "wave_combination"] = "add"
    blend_weight: float = 0.5
    # Eq. 2 specific params — used when blend_mode == "wave_combination"
    wave_count: int = 8           # N — number of superimposed waves
    wave_intensity: float = 0.3   # α — global wave amplitude scalar

    # Phase IV — Erosion (Eq. 4 hydraulic + Eq. 5 thermal)
    enable_hydraulic: bool = False
    enable_thermal: bool = False
    erosion_iterations: int = 30000
    erosion_strength: float = 0.3
    talus_angle: float = 0.5      # T  — slope threshold for thermal slippage
    thermal_rate: float = 0.3     # Kr — thermal material transfer rate


class TerrainEngine:
    """
    Runtime execution engine for terrain generation.
    Orchestrates the full 4-phase pipeline from parameters to output.
    """

    def __init__(self, config: Optional[TerrainConfig] = None):
        self.config = config or TerrainConfig()
        self._setup()

    def _setup(self):
        """Initialise generation components"""
        self.noise_gen = NoiseGenerator(self.config.seed)
        self.combiner  = NoiseCombiner()
        self.erosion   = ErosionSimulator(self.config.seed)

    def generate(self, config: Optional[TerrainConfig] = None) -> Dict[str, np.ndarray]:
        """
        Execute the full 4-phase terrain generation pipeline.

        Returns:
            Dict with keys 'heightmap', 'normal_map', 'splat_map'.
        """
        if config:
            self.config = config
            self._setup()

        # ----------------------------------------------------------------
        # Phase I — Base Noise Map P(x, y)  [Eq. 1]
        # P(x,y) = Σ_{i=0}^{k-1} a^i · noise(f^i · x, f^i · y)
        # ----------------------------------------------------------------
        noise_params = NoiseParams(
            seed=self.config.seed,
            size=self.config.size,
            frequency=self.config.frequency,
            amplitude=self.config.amplitude,
            octaves=self.config.octaves,       # k
            persistence=self.config.persistence, # a
            lacunarity=self.config.lacunarity,   # f
            wave_count=self.config.wave_count,
            wave_intensity=self.config.wave_intensity,
        )

        heightmap = self.noise_gen.generate(
            algorithm=self.config.noise_algorithm,
            params=noise_params,
        )   # P(x,y) — Phase I output

        # ----------------------------------------------------------------
        # Phase I post-processing — optional fractal reshaping of P
        # ----------------------------------------------------------------
        if self.config.fractal_type == "fbm":
            heightmap = self.combiner.fbm(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence,
            )
        elif self.config.fractal_type == "ridged":
            heightmap = self.combiner.ridged(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence,
            )
        elif self.config.fractal_type == "billow":
            heightmap = self.combiner.billow(
                heightmap,
                octaves=min(self.config.octaves, 4),
                persistence=self.config.persistence,
            )

        # ----------------------------------------------------------------
        # Phase II + III — Wave Enhancement & Combination  [Eq. 2 & 3]
        # ----------------------------------------------------------------
        if self.config.enable_secondary_noise:

            if self.config.blend_mode == "wave_combination":
                # Phase II: generate ψ(x, y)  [Eq. 2]
                wave_params = NoiseParams(
                    seed=self.config.seed,
                    size=self.config.size,
                    frequency=self.config.secondary_frequency,
                    wave_count=self.config.wave_count,
                    wave_intensity=self.config.wave_intensity,
                )
                psi = self.noise_gen.generate_wave_enhancement(wave_params)

                # Phase III: H_final = P + P·ψ  [Eq. 3]
                heightmap = self.combiner.wave_combination(heightmap, psi)

            else:
                # Generic secondary noise blend (non-specification modes)
                secondary_params = NoiseParams(
                    seed=self.config.seed + 1000,
                    size=self.config.size,
                    frequency=self.config.secondary_frequency,
                    amplitude=self.config.secondary_amplitude,
                    octaves=self.config.octaves,
                    persistence=self.config.persistence,
                    lacunarity=self.config.lacunarity,
                )
                secondary_heightmap = self.noise_gen.generate(
                    algorithm=self.config.secondary_algorithm,
                    params=secondary_params,
                )
                heightmap = self.combiner.combine(
                    layers=[heightmap, secondary_heightmap],
                    weights=[1.0 - self.config.blend_weight, self.config.blend_weight],
                    mode=self.config.blend_mode,
                )

        # ----------------------------------------------------------------
        # Phase IV — Erosion  [Eq. 4 hydraulic + Eq. 5 thermal]
        # ----------------------------------------------------------------
        if self.config.enable_hydraulic or self.config.enable_thermal:
            erosion_params = ErosionParams(
                iterations=self.config.erosion_iterations,
                erosion=self.config.erosion_strength,          # Ke
                deposition=self.config.erosion_strength,       # Kd
                talus_angle=self.config.talus_angle,           # T  (Eq. 5)
                thermal_rate=self.config.thermal_rate,         # Kr (Eq. 5)
            )
            heightmap = self.erosion.apply(
                heightmap,
                hydraulic=self.config.enable_hydraulic,
                thermal=self.config.enable_thermal,
                hydraulic_params=erosion_params,
                thermal_iterations=30,
            )

        # ----------------------------------------------------------------
        # Derivative maps
        # ----------------------------------------------------------------
        normal_map = self._compute_normal_map(heightmap)
        splat_map  = self._compute_splat_map(heightmap)

        return {
            "heightmap":  heightmap,
            "normal_map": normal_map,
            "splat_map":  splat_map,
        }

    def _compute_normal_map(self, heightmap: np.ndarray) -> np.ndarray:
        """
        Compute normal map from heightmap using Sobel operator.
        RGB encodes XYZ normal direction.
        """
        grad_x = np.zeros_like(heightmap)
        grad_y = np.zeros_like(heightmap)

        grad_x[:, 1:-1] = heightmap[:, 2:] - heightmap[:, :-2]
        grad_y[1:-1, :] = heightmap[2:, :] - heightmap[:-2, :]

        strength = 2.0
        grad_x *= strength
        grad_y *= strength

        normal_x = -grad_x
        normal_y = -grad_y
        normal_z = np.ones_like(heightmap)

        length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x /= length
        normal_y /= length
        normal_z /= length

        normal_map = np.stack([
            (normal_x + 1) * 0.5,
            (normal_y + 1) * 0.5,
            (normal_z + 1) * 0.5,
        ], axis=-1)

        return normal_map

    def _compute_splat_map(self, heightmap: np.ndarray) -> np.ndarray:
        """
        Compute splat map for texture blending.
        Channels: R=water/low, G=grass/mid, B=rock/high, A=snow/peaks
        """
        grad_x = np.zeros_like(heightmap)
        grad_y = np.zeros_like(heightmap)
        grad_x[:, 1:-1] = np.abs(heightmap[:, 2:] - heightmap[:, :-2])
        grad_y[1:-1, :] = np.abs(heightmap[2:, :] - heightmap[:-2, :])
        slope = np.sqrt(grad_x**2 + grad_y**2)

        water = np.clip(1 - heightmap / 0.3, 0, 1) * (1 - slope * 2)
        grass = np.clip(1 - np.abs(heightmap - 0.4) / 0.2, 0, 1) * (1 - slope * 3)
        rock  = np.clip(slope * 5, 0, 1) + np.clip((heightmap - 0.6) / 0.2, 0, 1) * 0.5
        snow  = np.clip((heightmap - 0.75) / 0.25, 0, 1) * (1 - slope * 2)

        total = water + grass + rock + snow + 0.001
        splat_map = np.stack([
            water / total,
            grass / total,
            rock  / total,
            snow  / total,
        ], axis=-1)

        return splat_map

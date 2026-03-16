"""
Noise Combiner for layering and blending multiple noise sources.

Phase III — Multiplicative-Additive Combination (Eq. 3)
    H_final(x, y) = P(x, y) + [P(x, y) · ψ(x, y)]

    P  = Phase I base noise map  (primary topology)
    ψ  = Phase II wave offset     (structural distortion field)
    P·ψ = Contextual scaling term — restricts sharp wave distortions to
          high-elevation areas (P ≈ 1) while preserving smooth valleys (P ≈ 0)

Also supports FBM, Ridged, and Billow post-processing fractal patterns.
"""

import numpy as np
from typing import List, Literal, Optional
from dataclasses import dataclass


@dataclass
class CombineParams:
    """Parameters for noise combination"""
    blend_mode: Literal["add", "multiply", "lerp", "min", "max"] = "add"
    weight: float = 1.0


class NoiseCombiner:
    """Combine and blend multiple noise layers"""
    
    @staticmethod
    def combine(
        layers: List[np.ndarray],
        weights: Optional[List[float]] = None,
        mode: Literal["add", "multiply", "lerp", "min", "max"] = "add"
    ) -> np.ndarray:
        """
        Combine multiple noise layers with specified blend mode.
        
        Args:
            layers: List of heightmap arrays (same shape)
            weights: Optional weights for each layer
            mode: Blending mode
        
        Returns:
            Combined heightmap
        """
        if not layers:
            raise ValueError("At least one layer required")
        
        if weights is None:
            weights = [1.0] * len(layers)
        
        if len(weights) != len(layers):
            raise ValueError("Weights must match number of layers")
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        result = np.zeros_like(layers[0])
        
        if mode == "add":
            for layer, weight in zip(layers, weights):
                result += layer * weight
        
        elif mode == "multiply":
            result = np.ones_like(layers[0])
            for layer, weight in zip(layers, weights):
                result *= (layer * weight + (1 - weight))
        
        elif mode == "lerp":
            # Sequential lerp
            result = layers[0]
            for i in range(1, len(layers)):
                result = result * (1 - weights[i]) + layers[i] * weights[i]
        
        elif mode == "min":
            weighted_layers = [l * w for l, w in zip(layers, weights)]
            result = np.minimum.reduce(weighted_layers)
        
        elif mode == "max":
            weighted_layers = [l * w for l, w in zip(layers, weights)]
            result = np.maximum.reduce(weighted_layers)
        
        # Normalize result to 0-1
        result = (result - result.min()) / (result.max() - result.min() + 1e-10)
        return result

    @staticmethod
    def wave_combination(P: np.ndarray, psi: np.ndarray) -> np.ndarray:
        """
        Phase III — Multiplicative-Additive Combination (Eq. 3).

        H_final(x, y) = P(x, y) + [P(x, y) · ψ(x, y)]

        The critical innovation: multiplying the wave offset ψ by the base
        height P makes structural distortions scale relative to existing
        elevation:
          - P ≈ 1 (mountains)  →  P·ψ ≈ ψ   (full wave distortion, jagged peaks)
          - P ≈ 0 (valleys)    →  P·ψ ≈ 0   (near-zero distortion, smooth plains)

        Args:
            P:   Phase I base noise map, values in [0, 1].
            psi: Phase II wave offset map from generate_wave_enhancement().
                 Signed values — NOT pre-normalised.

        Returns:
            H_final clamped to [0, 1].  We clip rather than min-max normalise
            to preserve the relative magnitude of the contextual scaling effect.
        """
        # Eq. 3: additive + multiplicative mask with smoother power curve
        # P**2 creates a gentler transition into the high elevation regions,
        # preventing the raw offset from causing extreme artificial spikes.
        H = P + ((P ** 2) * psi * 0.5)
        return np.clip(H, 0.0, 1.0)
    
    @staticmethod
    def fbm(
        base_noise: np.ndarray,
        octaves: int = 6,
        persistence: float = 0.5,
        lacunarity: float = 2.0
    ) -> np.ndarray:
        """
        Fractal Brownian Motion - standard octave layering.
        Creates natural-looking terrain with detail at multiple scales.
        """
        from scipy.ndimage import zoom
        
        result = np.zeros_like(base_noise)
        amplitude = 1.0
        total_amplitude = 0.0
        
        current = base_noise.copy()
        
        for _ in range(octaves):
            result += current * amplitude
            total_amplitude += amplitude
            amplitude *= persistence
            
            # Simulate higher frequency by zooming
            if current.shape[0] > 32:
                zoomed = zoom(current, lacunarity, order=1)
                # Crop to original size
                h, w = current.shape
                start_h = (zoomed.shape[0] - h) // 2
                start_w = (zoomed.shape[1] - w) // 2
                current = zoomed[start_h:start_h+h, start_w:start_w+w]
        
        return result / total_amplitude
    
    @staticmethod
    def ridged(
        base_noise: np.ndarray,
        octaves: int = 6,
        persistence: float = 0.5,
        offset: float = 1.0
    ) -> np.ndarray:
        """
        Ridged multifractal noise.
        Creates sharp ridges and mountain-like features.
        """
        from scipy.ndimage import zoom
        
        result = np.zeros_like(base_noise)
        amplitude = 1.0
        total_amplitude = 0.0
        current = base_noise.copy()
        
        for _ in range(octaves):
            # Ridge transformation: abs and invert
            signal = offset - np.abs(current * 2 - 1)
            signal = signal * signal
            
            result += signal * amplitude
            total_amplitude += amplitude
            amplitude *= persistence
            
            # Higher frequency simulation
            if current.shape[0] > 32:
                zoomed = zoom(current, 2.0, order=1)
                h, w = current.shape
                start_h = (zoomed.shape[0] - h) // 2
                start_w = (zoomed.shape[1] - w) // 2
                current = zoomed[start_h:start_h+h, start_w:start_w+w]
        
        result = result / total_amplitude
        return (result - result.min()) / (result.max() - result.min() + 1e-10)
    
    @staticmethod
    def billow(
        base_noise: np.ndarray,
        octaves: int = 6,
        persistence: float = 0.5
    ) -> np.ndarray:
        """
        Billow noise - absolute value creates puffy, cloud-like patterns.
        Good for rolling hills and soft terrain.
        """
        from scipy.ndimage import zoom
        
        result = np.zeros_like(base_noise)
        amplitude = 1.0
        total_amplitude = 0.0
        current = base_noise.copy()
        
        for _ in range(octaves):
            # Billow transformation: abs value
            signal = np.abs(current * 2 - 1)
            
            result += signal * amplitude
            total_amplitude += amplitude
            amplitude *= persistence
            
            if current.shape[0] > 32:
                zoomed = zoom(current, 2.0, order=1)
                h, w = current.shape
                start_h = (zoomed.shape[0] - h) // 2
                start_w = (zoomed.shape[1] - w) // 2
                current = zoomed[start_h:start_h+h, start_w:start_w+w]
        
        return result / total_amplitude

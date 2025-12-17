"""
Noise Generators for Terrain Generation
Includes: Wave Interference, Harmonic Functions, Perlin, Simplex
"""

import numpy as np
from typing import Optional, Literal, Tuple
from dataclasses import dataclass


@dataclass
class NoiseParams:
    """Parameters for noise generation"""
    seed: int = 42
    size: int = 256
    frequency: float = 2.0
    amplitude: float = 1.0
    octaves: int = 6
    persistence: float = 0.5
    lacunarity: float = 2.0
    

class NoiseGenerator:
    """Multi-algorithm noise generator for terrain heightmaps"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self._init_permutation_table()
    
    def _init_permutation_table(self):
        """Initialize permutation table for Perlin/Simplex noise"""
        self.perm = np.arange(256, dtype=np.int32)
        self.rng.shuffle(self.perm)
        self.perm = np.tile(self.perm, 2)
        
        # Gradients for 2D
        self.gradients = np.array([
            [1, 1], [-1, 1], [1, -1], [-1, -1],
            [1, 0], [-1, 0], [0, 1], [0, -1]
        ], dtype=np.float64)
    
    def generate(
        self, 
        algorithm: Literal["wave", "harmonic", "perlin", "simplex"] = "wave",
        params: Optional[NoiseParams] = None
    ) -> np.ndarray:
        """Generate noise using specified algorithm"""
        if params is None:
            params = NoiseParams(seed=self.seed)
        
        algorithms = {
            "wave": self._wave_interference,
            "harmonic": self._harmonic_functions,
            "perlin": self._perlin_noise,
            "simplex": self._simplex_noise
        }
        
        return algorithms[algorithm](params)
    
    def _wave_interference(self, params: NoiseParams) -> np.ndarray:
        """
        Generate terrain using wave interference patterns.
        Superposition of multiple sine/cosine waves at different frequencies and phases.
        """
        size = params.size
        x = np.linspace(0, params.frequency * np.pi * 2, size)
        y = np.linspace(0, params.frequency * np.pi * 2, size)
        xx, yy = np.meshgrid(x, y)
        
        heightmap = np.zeros((size, size), dtype=np.float64)
        
        # Generate random wave parameters
        rng = np.random.default_rng(params.seed)
        
        for octave in range(params.octaves):
            freq_mult = params.lacunarity ** octave
            amp_mult = params.persistence ** octave
            
            # Multiple wave components per octave
            num_waves = 3
            for _ in range(num_waves):
                # Random wave direction and phase
                angle = rng.random() * 2 * np.pi
                phase_x = rng.random() * 2 * np.pi
                phase_y = rng.random() * 2 * np.pi
                
                # Wave components
                wave_x = np.sin(xx * freq_mult + phase_x) * np.cos(angle)
                wave_y = np.cos(yy * freq_mult + phase_y) * np.sin(angle)
                
                # Interference pattern
                interference = (wave_x + wave_y) * amp_mult / num_waves
                heightmap += interference
        
        # Normalize to 0-1 range
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude
    
    def _harmonic_functions(self, params: NoiseParams) -> np.ndarray:
        """
        Generate terrain using spherical harmonics and Fourier series.
        Creates smooth, organic-looking terrain patterns.
        """
        size = params.size
        x = np.linspace(-np.pi, np.pi, size)
        y = np.linspace(-np.pi, np.pi, size)
        xx, yy = np.meshgrid(x, y)
        
        heightmap = np.zeros((size, size), dtype=np.float64)
        rng = np.random.default_rng(params.seed)
        
        # Fourier series with random coefficients
        for octave in range(params.octaves):
            freq = (octave + 1) * params.frequency
            amp = params.persistence ** octave
            
            # Random harmonic coefficients
            for m in range(1, 4):
                a_mn = rng.uniform(-1, 1)
                b_mn = rng.uniform(-1, 1)
                
                # Spherical harmonic-like patterns
                harmonic = (
                    a_mn * np.cos(m * xx * freq / 2) * np.cos(m * yy * freq / 2) +
                    b_mn * np.sin(m * xx * freq / 2) * np.sin(m * yy * freq / 2)
                )
                heightmap += harmonic * amp / 3
        
        # Add radial component for variety
        r = np.sqrt(xx**2 + yy**2)
        theta = np.arctan2(yy, xx)
        radial = np.sin(r * params.frequency) * np.cos(3 * theta)
        heightmap += radial * 0.2
        
        # Normalize
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude
    
    def _fade(self, t: np.ndarray) -> np.ndarray:
        """Smoothstep fade function for Perlin noise"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Linear interpolation"""
        return a + t * (b - a)
    
    def _perlin_noise(self, params: NoiseParams) -> np.ndarray:
        """
        Classic Perlin noise implementation with octave layering (fBm).
        """
        size = params.size
        heightmap = np.zeros((size, size), dtype=np.float64)
        
        for octave in range(params.octaves):
            freq = params.frequency * (params.lacunarity ** octave)
            amp = params.persistence ** octave
            
            # Sample coordinates
            x = np.linspace(0, freq, size)
            y = np.linspace(0, freq, size)
            xx, yy = np.meshgrid(x, y)
            
            # Integer and fractional parts
            xi = xx.astype(np.int32) & 255
            yi = yy.astype(np.int32) & 255
            xf = xx - np.floor(xx)
            yf = yy - np.floor(yy)
            
            # Fade curves
            u = self._fade(xf)
            v = self._fade(yf)
            
            # Hash coordinates
            aa = self.perm[self.perm[xi] + yi]
            ab = self.perm[self.perm[xi] + yi + 1]
            ba = self.perm[self.perm[xi + 1] + yi]
            bb = self.perm[self.perm[xi + 1] + yi + 1]
            
            # Gradient dot products
            def grad(h, x, y):
                g = self.gradients[h & 7]
                return g[..., 0] * x + g[..., 1] * y
            
            x1 = self._lerp(grad(aa, xf, yf), grad(ba, xf - 1, yf), u)
            x2 = self._lerp(grad(ab, xf, yf - 1), grad(bb, xf - 1, yf - 1), u)
            
            octave_noise = self._lerp(x1, x2, v)
            heightmap += octave_noise * amp
        
        # Normalize to 0-1
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude
    
    def _simplex_noise(self, params: NoiseParams) -> np.ndarray:
        """
        Simplex noise - faster and fewer artifacts than Perlin.
        Uses triangular grid instead of square grid.
        """
        size = params.size
        heightmap = np.zeros((size, size), dtype=np.float64)
        
        F2 = 0.5 * (np.sqrt(3.0) - 1.0)
        G2 = (3.0 - np.sqrt(3.0)) / 6.0
        
        for octave in range(params.octaves):
            freq = params.frequency * (params.lacunarity ** octave)
            amp = params.persistence ** octave
            
            x = np.linspace(0, freq, size)
            y = np.linspace(0, freq, size)
            xx, yy = np.meshgrid(x, y)
            
            # Skew input space
            s = (xx + yy) * F2
            i = np.floor(xx + s).astype(np.int32)
            j = np.floor(yy + s).astype(np.int32)
            
            t = (i + j) * G2
            X0 = i - t
            Y0 = j - t
            x0 = xx - X0
            y0 = yy - Y0
            
            # Determine simplex
            i1 = np.where(x0 > y0, 1, 0)
            j1 = np.where(x0 > y0, 0, 1)
            
            x1 = x0 - i1 + G2
            y1 = y0 - j1 + G2
            x2 = x0 - 1.0 + 2.0 * G2
            y2 = y0 - 1.0 + 2.0 * G2
            
            # Hash coordinates
            ii = i & 255
            jj = j & 255
            
            def contrib(gx, gy, dx, dy):
                t = 0.5 - dx*dx - dy*dy
                t = np.maximum(t, 0)
                t = t * t * t * t
                gi = self.perm[self.perm[gx & 255] + (gy & 255)] & 7
                g = self.gradients[gi]
                return t * (g[..., 0] * dx + g[..., 1] * dy)
            
            n0 = contrib(ii, jj, x0, y0)
            n1 = contrib(ii + i1, jj + j1, x1, y1)
            n2 = contrib(ii + 1, jj + 1, x2, y2)
            
            octave_noise = 70.0 * (n0 + n1 + n2)
            heightmap += octave_noise * amp
        
        # Normalize
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude

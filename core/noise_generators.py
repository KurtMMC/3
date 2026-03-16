"""
Noise Generators for Terrain Generation

Algorithm phases implemented here:

Phase I  — Base Noise Map P(x, y) via Fractal Brownian Motion (Eq. 1)
           P(x, y) = Σ_{i=0}^{k-1} a^i · noise(f^i · x, f^i · y)
           where a = persistence, f = lacunarity, k = octaves
           Algorithms: perlin, simplex (fBm), wave, harmonic

Phase II — Wave Enhancement ψ(x, y) (Eq. 2)
           ψ(x, y) = Σ_{j=1}^{N} α · sin(kⱼ · p + δⱼ)
           where α = wave_intensity, N = wave_count,
                 kⱼ = wave vector (direction × spatial frequency),
                 p  = position vector [x, y],
                 δⱼ = random phase shift
"""

import numpy as np
from typing import Optional, Literal
from dataclasses import dataclass, field


@dataclass
class NoiseParams:
    """Parameters for noise generation"""
    # Basic
    seed: int = 42
    size: int = 256
    frequency: float = 2.0
    amplitude: float = 1.0

    # Phase I — fBm (Eq. 1)
    octaves: int = 6       # k  — number of noise layers
    persistence: float = 0.5  # a  — amplitude multiplier per octave (0 < a < 1)
    lacunarity: float = 2.0   # f  — frequency multiplier per octave (f > 1)

    # Phase II — Wave Enhancement (Eq. 2)
    wave_count: int = 8           # N — number of superimposed waves
    wave_intensity: float = 0.3   # α — global wave amplitude scalar


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
        """
        Generate Phase I base noise map P(x, y) using the specified algorithm.
        All algorithms implement the fBm octave summation (Eq. 1).
        """
        if params is None:
            params = NoiseParams(seed=self.seed)

        algorithms = {
            "wave":     self._wave_interference,
            "harmonic": self._harmonic_functions,
            "perlin":   self._perlin_noise,
            "simplex":  self._simplex_noise,
        }

        return algorithms[algorithm](params)

    def generate_wave_enhancement(self, params: Optional[NoiseParams] = None) -> np.ndarray:
        """
        Phase II — Wave-Harmonic Algorithm (Eq. 2).

        Generates the structural offset map ψ(x, y) via deterministic
        wave interference.  Each wave j contributes:

            α · sin(kⱼ · p + δⱼ)

        where:
            α  = wave_intensity  (global height scaling)
            kⱼ = wave vector     = spatial_freq_j × [cos(θⱼ), sin(θⱼ)]
            p  = [xx, yy]        (position vector at each grid cell)
            δⱼ = random phase shift  (prevents artificial symmetry)

        Returns a signed offset map in approximately [-1, 1].
        It is intentionally NOT normalised to [0, 1] so that the
        contextual scaling in Phase III (Eq. 3) works as specified.
        """
        if params is None:
            params = NoiseParams(seed=self.seed)

        size = params.size
        alpha = params.wave_intensity   # α — global wave amplitude
        N = params.wave_count           # N — number of superimposed waves

        # Build coordinate grid (position vector p)
        x = np.linspace(0, 2 * np.pi * params.frequency, size)
        y = np.linspace(0, 2 * np.pi * params.frequency, size)
        xx, yy = np.meshgrid(x, y)   # shape (size, size)

        psi = np.zeros((size, size), dtype=np.float64)

        rng = np.random.default_rng(params.seed)

        for j in range(N):
            # Wave direction θⱼ  →  unit vector [cos θ, sin θ]
            theta_j = rng.random() * 2 * np.pi

            # Spatial frequency of this wave (random spread around base freq)
            spatial_freq_j = params.frequency * (0.5 + rng.random() * 1.5)

            # Wave vector kⱼ = spatial_freq_j × [cos θⱼ, sin θⱼ]
            kx_j = spatial_freq_j * np.cos(theta_j)
            ky_j = spatial_freq_j * np.sin(theta_j)

            # Phase shift δⱼ — random, prevents artificial symmetry
            delta_j = rng.random() * 2 * np.pi

            # Dot product  kⱼ · p  =  kx·x + ky·y  (vectorised over grid)
            dot = kx_j * xx + ky_j * yy

            # Accumulate smoother waves using squared sine for ridges
            wave_val = np.sin(dot + delta_j)
            # Soften the extreme peaks by pulling down the sharp edges
            psi += alpha * (np.sign(wave_val) * (np.abs(wave_val) ** 1.5))

        # Attenuate the overall psi field to prevent runaway spikes
        return psi * 0.6

    # ------------------------------------------------------------------
    # Phase I — fBm Base Noise Algorithms
    # ------------------------------------------------------------------

    def _wave_interference(self, params: NoiseParams) -> np.ndarray:
        """
        Phase I base map via wave-interference fBm (Eq. 1 variant).

        Applies octave summation over sine-wave components:
            P(x, y) = Σ_{i=0}^{k-1} a^i · wave_noise(f^i · x, f^i · y)

        Parameters:  a = persistence,  f = lacunarity,  k = octaves
        """
        size = params.size
        a = params.persistence   # amplitude decay per octave
        f = params.lacunarity    # frequency growth per octave
        k = params.octaves       # total octaves

        x = np.linspace(0, params.frequency * np.pi * 2, size)
        y = np.linspace(0, params.frequency * np.pi * 2, size)
        xx, yy = np.meshgrid(x, y)

        heightmap = np.zeros((size, size), dtype=np.float64)

        rng = np.random.default_rng(params.seed)

        for i in range(k):
            freq_mult = f ** i   # f^i
            amp_mult  = a ** i   # a^i

            # Multiple wave components per octave for richer detail
            num_waves = 3
            for _ in range(num_waves):
                angle   = rng.random() * 2 * np.pi
                phase_x = rng.random() * 2 * np.pi
                phase_y = rng.random() * 2 * np.pi

                wave_x = np.sin(xx * freq_mult + phase_x) * np.cos(angle)
                wave_y = np.cos(yy * freq_mult + phase_y) * np.sin(angle)

                heightmap += (wave_x + wave_y) * amp_mult / num_waves

        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude

    def _harmonic_functions(self, params: NoiseParams) -> np.ndarray:
        """
        Phase I base map via harmonic/Fourier fBm (Eq. 1 variant).

        Applies octave summation using spherical-harmonic-like Fourier terms:
            P(x, y) = Σ_{i=0}^{k-1} a^i · harmonic_noise(f^i · x, f^i · y)

        Parameters:  a = persistence,  f = lacunarity,  k = octaves
        """
        size = params.size
        a = params.persistence
        f_base = params.frequency
        k = params.octaves

        x = np.linspace(-np.pi, np.pi, size)
        y = np.linspace(-np.pi, np.pi, size)
        xx, yy = np.meshgrid(x, y)

        heightmap = np.zeros((size, size), dtype=np.float64)
        rng = np.random.default_rng(params.seed)

        for i in range(k):
            freq  = (i + 1) * f_base   # f^i · base_freq
            amp   = a ** i              # a^i

            for m in range(1, 4):
                a_mn = rng.uniform(-1, 1)
                b_mn = rng.uniform(-1, 1)

                harmonic = (
                    a_mn * np.cos(m * xx * freq / 2) * np.cos(m * yy * freq / 2) +
                    b_mn * np.sin(m * xx * freq / 2) * np.sin(m * yy * freq / 2)
                )
                heightmap += harmonic * amp / 3

        # Radial component for variety
        r     = np.sqrt(xx**2 + yy**2)
        theta = np.arctan2(yy, xx)
        heightmap += np.sin(r * f_base) * np.cos(3 * theta) * 0.2

        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude

    def _fade(self, t: np.ndarray) -> np.ndarray:
        """Smoothstep fade function: 6t⁵ − 15t⁴ + 10t³"""
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Linear interpolation"""
        return a + t * (b - a)

    def _perlin_noise(self, params: NoiseParams) -> np.ndarray:
        """
        Phase I base map — Classic Perlin fBm (Eq. 1).

        P(x, y) = Σ_{i=0}^{k-1} a^i · perlin(f^i · x, f^i · y)

        Parameters:
            a (persistence)  — amplitude multiplier  (0 < a < 1)
            f (lacunarity)   — frequency multiplier  (f > 1)
            k (octaves)      — number of noise layers
        """
        size = params.size
        a = params.persistence   # Eq. 1:  a
        f = params.lacunarity    # Eq. 1:  f
        k = params.octaves       # Eq. 1:  k

        heightmap = np.zeros((size, size), dtype=np.float64)

        for i in range(k):
            freq = params.frequency * (f ** i)   # f^i — spatial frequency
            amp  = a ** i                         # a^i — amplitude weight

            x = np.linspace(0, freq, size)
            y = np.linspace(0, freq, size)
            xx, yy = np.meshgrid(x, y)

            xi = xx.astype(np.int32) & 255
            yi = yy.astype(np.int32) & 255
            xf = xx - np.floor(xx)
            yf = yy - np.floor(yy)

            u = self._fade(xf)
            v = self._fade(yf)

            aa = self.perm[self.perm[xi]     + yi    ]
            ab = self.perm[self.perm[xi]     + yi + 1]
            ba = self.perm[self.perm[xi + 1] + yi    ]
            bb = self.perm[self.perm[xi + 1] + yi + 1]

            def grad(h, x, y):
                g = self.gradients[h & 7]
                return g[..., 0] * x + g[..., 1] * y

            x1 = self._lerp(grad(aa, xf,     yf    ), grad(ba, xf - 1, yf    ), u)
            x2 = self._lerp(grad(ab, xf,     yf - 1), grad(bb, xf - 1, yf - 1), u)

            octave_noise = self._lerp(x1, x2, v)   # noise(f^i · x, f^i · y)
            heightmap += octave_noise * amp          # accumulate  a^i · noise(...)

        # Normalise to [0, 1]
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude

    def _simplex_noise(self, params: NoiseParams) -> np.ndarray:
        """
        Phase I base map — Simplex fBm (Eq. 1).

        P(x, y) = Σ_{i=0}^{k-1} a^i · simplex(f^i · x, f^i · y)

        Faster and with fewer directional artifacts than Perlin;
        uses triangular grid instead of square grid.

        Parameters:
            a (persistence)  — amplitude multiplier  (0 < a < 1)
            f (lacunarity)   — frequency multiplier  (f > 1)
            k (octaves)      — number of noise layers
        """
        size = params.size
        a = params.persistence   # Eq. 1:  a
        f = params.lacunarity    # Eq. 1:  f
        k = params.octaves       # Eq. 1:  k

        heightmap = np.zeros((size, size), dtype=np.float64)

        F2 = 0.5 * (np.sqrt(3.0) - 1.0)
        G2 = (3.0 - np.sqrt(3.0)) / 6.0

        for i in range(k):
            freq = params.frequency * (f ** i)   # f^i
            amp  = a ** i                         # a^i

            x = np.linspace(0, freq, size)
            y = np.linspace(0, freq, size)
            xx, yy = np.meshgrid(x, y)

            s  = (xx + yy) * F2
            gi = np.floor(xx + s).astype(np.int32)
            gj = np.floor(yy + s).astype(np.int32)

            t  = (gi + gj) * G2
            X0 = gi - t
            Y0 = gj - t
            x0 = xx - X0
            y0 = yy - Y0

            i1 = np.where(x0 > y0, 1, 0)
            j1 = np.where(x0 > y0, 0, 1)

            x1 = x0 - i1 + G2
            y1 = y0 - j1 + G2
            x2 = x0 - 1.0 + 2.0 * G2
            y2 = y0 - 1.0 + 2.0 * G2

            ii = gi & 255
            jj = gj & 255

            def contrib(gx, gy, dx, dy):
                t_val = 0.5 - dx*dx - dy*dy
                t_val = np.maximum(t_val, 0)
                t_val = t_val * t_val * t_val * t_val
                gi_idx = self.perm[self.perm[gx & 255] + (gy & 255)] & 7
                g = self.gradients[gi_idx]
                return t_val * (g[..., 0] * dx + g[..., 1] * dy)

            n0 = contrib(ii,      jj,      x0, y0)
            n1 = contrib(ii + i1, jj + j1, x1, y1)
            n2 = contrib(ii + 1,  jj + 1,  x2, y2)

            octave_noise = 70.0 * (n0 + n1 + n2)   # simplex(f^i · x, f^i · y)
            heightmap += octave_noise * amp           # accumulate  a^i · noise(...)

        # Normalise to [0, 1]
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)
        return heightmap * params.amplitude

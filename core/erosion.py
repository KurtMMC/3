"""
Erosion Simulation for realistic terrain weathering.

Phase IV — Erosion (applied after Phase III H_final output).

Two independent sub-models are available:

Eq. 4 — Hydraulic Erosion (Particle Droplet Model)
    Per droplet step:
        C_cap        = max(-Δh, s_min) · v · w · Kc
        Δs (deposit) = (s - C_cap) · Kd          if s > C_cap
        Δs (erode)   = min((C_cap - s) · Ke, |Δh|)  otherwise
        v_{t+1}      = sqrt(max(v_t² + Δh · g, 0))
        w_{t+1}      = w_t · (1 − K_evap)

    Symbols:
        Kc     = capacity    — sediment capacity factor
        Ke     = erosion     — erosion rate
        Kd     = deposition  — deposition rate
        K_evap = evaporation — water evaporation rate
        g      = gravity     — acceleration constant
        s_min  = min_slope   — minimum slope for capacity calculation
        v      = droplet speed (starts at 1.0)
        w      = water volume (starts at 1.0)
        s      = carried sediment (starts at 0.0)

Eq. 5 — Thermal Erosion (Talus-Angle Slippage)
    Per iteration, for each of 8 directional neighbours j of cell i:
        slope_ij    = Δh_ij / d_ij
        transfer_ij = (Δh_ij − T · d_ij) · Kr / 2   if slope_ij > T

    Symbols:
        T   = talus_angle   — slope threshold for material slippage
        Kr  = thermal_rate  — material transfer rate
        d_ij = 1 (cardinal) or √2 (diagonal)
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class ErosionParams:
    """
    Parameters for erosion simulation — covers both Eq. 4 (hydraulic)
    and Eq. 5 (thermal).
    """
    # Shared
    iterations: int = 50000

    # Eq. 4 — Hydraulic erosion parameters
    inertia: float = 0.05       # directional inertia of droplet movement
    capacity: float = 4.0       # Kc — sediment capacity factor
    deposition: float = 0.3     # Kd — deposition rate
    erosion: float = 0.3        # Ke — erosion rate
    evaporation: float = 0.01   # K_evap — water evaporation rate per step
    min_slope: float = 0.01     # s_min — minimum effective slope for capacity
    gravity: float = 4.0        # g   — gravity constant for speed update
    radius: int = 3             # brush radius for sediment distribution

    # Eq. 5 — Thermal erosion parameters
    talus_angle: float = 0.5    # T  — slope threshold (angle) for sliding
    thermal_rate: float = 0.3   # Kr — fraction of excess material transferred


class ErosionSimulator:
    """Simulate erosion processes on heightmaps"""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def hydraulic_erosion(
        self,
        heightmap: np.ndarray,
        params: Optional[ErosionParams] = None
    ) -> np.ndarray:
        """
        Phase IV — Hydraulic Erosion (Eq. 4): Particle Droplet Model.

        Simulates individual water droplets that flow downhill, picking up
        sediment where they accelerate and depositing it where they slow.
        Height changes are computed via bilinear interpolation for smooth,
        artifact-free erosion channels.

        Args:
            heightmap: Phase III H_final output, values in [0, 1].
            params:    ErosionParams (Eq. 4 fields used here).

        Returns:
            Eroded heightmap clipped to [0, 1].
        """
        if params is None:
            params = ErosionParams()

        result = heightmap.copy().astype(np.float64)
        height, width = result.shape

        for _ in range(params.iterations):
            # --- Initialise droplet ---
            pos_x = self.rng.random() * (width - 1)
            pos_y = self.rng.random() * (height - 1)

            dir_x = 0.0
            dir_y = 0.0
            v = 1.0         # droplet speed
            w = 1.0         # water volume
            s = 0.0         # carried sediment

            for _ in range(64):   # max droplet lifetime steps
                cell_x = int(pos_x)
                cell_y = int(pos_y)

                if cell_x < 0 or cell_x >= width - 1 or cell_y < 0 or cell_y >= height - 1:
                    break

                offset_x = pos_x - cell_x
                offset_y = pos_y - cell_y

                # Bilinear sample — Eq. 4: Δh via interpolation
                h00 = result[cell_y,                         cell_x                        ]
                h10 = result[cell_y,                         min(cell_x + 1, width - 1)    ]
                h01 = result[min(cell_y + 1, height - 1),   cell_x                        ]
                h11 = result[min(cell_y + 1, height - 1),   min(cell_x + 1, width - 1)    ]

                grad_x = (h10 - h00) * (1 - offset_y) + (h11 - h01) * offset_y
                grad_y = (h01 - h00) * (1 - offset_x) + (h11 - h10) * offset_x

                # Direction update with inertia
                dir_x = dir_x * params.inertia - grad_x * (1 - params.inertia)
                dir_y = dir_y * params.inertia - grad_y * (1 - params.inertia)

                length = np.sqrt(dir_x * dir_x + dir_y * dir_y)
                if length < 0.0001:
                    dir_x = self.rng.random() * 2 - 1
                    dir_y = self.rng.random() * 2 - 1
                    length = np.sqrt(dir_x * dir_x + dir_y * dir_y)
                dir_x /= length
                dir_y /= length

                new_pos_x = pos_x + dir_x
                new_pos_y = pos_y + dir_y

                if new_pos_x < 0 or new_pos_x >= width - 1 or new_pos_y < 0 or new_pos_y >= height - 1:
                    break

                new_cell_x  = int(new_pos_x)
                new_cell_y  = int(new_pos_y)
                new_off_x   = new_pos_x - new_cell_x
                new_off_y   = new_pos_y - new_cell_y

                nw00 = result[new_cell_y,                        new_cell_x                        ]
                nw10 = result[new_cell_y,                        min(new_cell_x + 1, width - 1)    ]
                nw01 = result[min(new_cell_y + 1, height - 1),  new_cell_x                        ]
                nw11 = result[min(new_cell_y + 1, height - 1),  min(new_cell_x + 1, width - 1)    ]

                old_height = (h00  * (1 - offset_x) * (1 - offset_y) +
                              h10  * offset_x        * (1 - offset_y) +
                              h01  * (1 - offset_x)  * offset_y       +
                              h11  * offset_x        * offset_y)

                new_height = (nw00 * (1 - new_off_x) * (1 - new_off_y) +
                              nw10 * new_off_x        * (1 - new_off_y) +
                              nw01 * (1 - new_off_x)  * new_off_y       +
                              nw11 * new_off_x        * new_off_y)

                delta_h = new_height - old_height   # Δh

                # Eq. 4 — Sediment capacity: C_cap = max(-Δh, s_min) · v · w · Kc
                C_cap = max(-delta_h, params.min_slope) * v * w * params.capacity

                if s > C_cap or delta_h > 0:
                    # Deposit
                    amount = (s - C_cap) * params.deposition if delta_h <= 0 else min(delta_h, s)
                    s -= amount
                    result[cell_y,                         cell_x                        ] += amount * (1 - offset_x) * (1 - offset_y)
                    result[cell_y,                         min(cell_x + 1, width - 1)    ] += amount * offset_x       * (1 - offset_y)
                    result[min(cell_y + 1, height - 1),   cell_x                        ] += amount * (1 - offset_x)  * offset_y
                    result[min(cell_y + 1, height - 1),   min(cell_x + 1, width - 1)    ] += amount * offset_x        * offset_y
                else:
                    # Erode: Δs = min((C_cap − s) · Ke, |Δh|)
                    amount = min((C_cap - s) * params.erosion, -delta_h)
                    s += amount
                    result[cell_y,                         cell_x                        ] -= amount * (1 - offset_x) * (1 - offset_y)
                    result[cell_y,                         min(cell_x + 1, width - 1)    ] -= amount * offset_x       * (1 - offset_y)
                    result[min(cell_y + 1, height - 1),   cell_x                        ] -= amount * (1 - offset_x)  * offset_y
                    result[min(cell_y + 1, height - 1),   min(cell_x + 1, width - 1)    ] -= amount * offset_x        * offset_y

                # Eq. 4 — Speed and water updates
                v = np.sqrt(max(v * v + delta_h * params.gravity, 0.0))   # v_{t+1}
                w *= (1 - params.evaporation)                               # w_{t+1}
                pos_x = new_pos_x
                pos_y = new_pos_y

                if w < 0.01:
                    break

        return np.clip(result, 0.0, 1.0)

    def thermal_erosion(
        self,
        heightmap: np.ndarray,
        params: Optional[ErosionParams] = None,
        iterations: Optional[int] = None,
    ) -> np.ndarray:
        """
        Phase IV — Thermal Erosion (Eq. 5): Talus-Angle Slippage Model.

        Material slides from cell i to neighbour j when the slope exceeds
        the talus angle threshold T:

            slope_ij    = (h_i − h_j) / d_ij
            transfer_ij = (Δh_ij − T · d_ij) · Kr / 2   if slope_ij > T

        Loops over all 8 directional neighbours per iteration.

        Args:
            heightmap:  Input heightmap, values in [0, 1].
            params:     ErosionParams — uses talus_angle (T) and thermal_rate (Kr).
            iterations: Override iteration count (for API backward-compat).

        Returns:
            Eroded heightmap clipped to [0, 1].
        """
        if params is None:
            params = ErosionParams()

        T  = params.talus_angle   # Eq. 5: T
        Kr = params.thermal_rate  # Eq. 5: Kr
        n_iter = iterations if iterations is not None else 50

        result = heightmap.copy().astype(np.float64)

        for _ in range(n_iter):
            padded = np.pad(result, 1, mode='edge')

            # 8 directional neighbours and their grid distances (d_ij)
            neighbors = [
                (padded[:-2, 1:-1], 1.0),          # top
                (padded[2:,  1:-1], 1.0),           # bottom
                (padded[1:-1, :-2], 1.0),           # left
                (padded[1:-1, 2:],  1.0),           # right
                (padded[:-2, :-2],  np.sqrt(2)),    # top-left
                (padded[:-2, 2:],   np.sqrt(2)),    # top-right
                (padded[2:,  :-2],  np.sqrt(2)),    # bottom-left
                (padded[2:,  2:],   np.sqrt(2)),    # bottom-right
            ]

            for neighbor, d_ij in neighbors:
                delta_h = result - neighbor          # Δh_ij = h_i − h_j
                slope   = delta_h / d_ij            # slope_ij = Δh_ij / d_ij

                mask     = slope > T                # cells exceeding talus angle
                # transfer_ij = (Δh_ij − T · d_ij) · Kr / 2
                transfer = np.where(mask, (delta_h - T * d_ij) * Kr * 0.5, 0.0)
                result  -= transfer

        return np.clip(result, 0.0, 1.0)

    def apply(
        self,
        heightmap: np.ndarray,
        hydraulic: bool = True,
        thermal: bool = True,
        hydraulic_params: Optional[ErosionParams] = None,
        thermal_iterations: int = 30,
    ) -> np.ndarray:
        """
        Apply Phase IV erosion pipeline to H_final.

        Hydraulic erosion (Eq. 4) runs first, then thermal (Eq. 5).
        A single ErosionParams instance governs both sub-models;
        thermal_iterations is accepted for backward compatibility.
        """
        result = heightmap.copy()

        if hydraulic:
            result = self.hydraulic_erosion(result, hydraulic_params)

        if thermal:
            # Use the same ErosionParams for thermal so talus_angle / thermal_rate
            # set via the API are forwarded correctly.
            result = self.thermal_erosion(result, params=hydraulic_params,
                                          iterations=thermal_iterations)

        return result

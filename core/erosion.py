"""
Erosion Simulation for realistic terrain weathering.
Includes hydraulic and thermal erosion algorithms.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ErosionParams:
    """Parameters for erosion simulation"""
    iterations: int = 50000
    inertia: float = 0.05
    capacity: float = 4.0
    deposition: float = 0.3
    erosion: float = 0.3
    evaporation: float = 0.01
    min_slope: float = 0.01
    gravity: float = 4.0
    radius: int = 3


class ErosionSimulator:
    """Simulate erosion processes on heightmaps"""
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
    
    def hydraulic_erosion(
        self,
        heightmap: np.ndarray,
        params: ErosionParams = None
    ) -> np.ndarray:
        """
        Simulate water-based erosion.
        Creates valleys, river paths, and natural drainage patterns.
        """
        if params is None:
            params = ErosionParams()
        
        result = heightmap.copy().astype(np.float64)
        height, width = result.shape
        
        for _ in range(params.iterations):
            # Random starting position
            pos_x = self.rng.random() * (width - 1)
            pos_y = self.rng.random() * (height - 1)
            
            dir_x = 0.0
            dir_y = 0.0
            speed = 1.0
            water = 1.0
            sediment = 0.0
            
            for _ in range(64):  # Max droplet lifetime
                cell_x = int(pos_x)
                cell_y = int(pos_y)
                
                # Check bounds
                if cell_x < 0 or cell_x >= width - 1 or cell_y < 0 or cell_y >= height - 1:
                    break
                
                # Bilinear interpolation offsets
                offset_x = pos_x - cell_x
                offset_y = pos_y - cell_y
                
                # Calculate gradient using bilinear interpolation
                h00 = result[cell_y, cell_x]
                h10 = result[cell_y, min(cell_x + 1, width - 1)]
                h01 = result[min(cell_y + 1, height - 1), cell_x]
                h11 = result[min(cell_y + 1, height - 1), min(cell_x + 1, width - 1)]
                
                grad_x = (h10 - h00) * (1 - offset_y) + (h11 - h01) * offset_y
                grad_y = (h01 - h00) * (1 - offset_x) + (h11 - h10) * offset_x
                
                # Update direction with inertia
                dir_x = dir_x * params.inertia - grad_x * (1 - params.inertia)
                dir_y = dir_y * params.inertia - grad_y * (1 - params.inertia)
                
                # Normalize direction
                length = np.sqrt(dir_x * dir_x + dir_y * dir_y)
                if length < 0.0001:
                    dir_x = self.rng.random() * 2 - 1
                    dir_y = self.rng.random() * 2 - 1
                    length = np.sqrt(dir_x * dir_x + dir_y * dir_y)
                
                dir_x /= length
                dir_y /= length
                
                # Move droplet
                new_pos_x = pos_x + dir_x
                new_pos_y = pos_y + dir_y
                
                # Check new bounds
                if new_pos_x < 0 or new_pos_x >= width - 1 or new_pos_y < 0 or new_pos_y >= height - 1:
                    break
                
                # Calculate height difference
                new_cell_x = int(new_pos_x)
                new_cell_y = int(new_pos_y)
                new_offset_x = new_pos_x - new_cell_x
                new_offset_y = new_pos_y - new_cell_y
                
                new_h00 = result[new_cell_y, new_cell_x]
                new_h10 = result[new_cell_y, min(new_cell_x + 1, width - 1)]
                new_h01 = result[min(new_cell_y + 1, height - 1), new_cell_x]
                new_h11 = result[min(new_cell_y + 1, height - 1), min(new_cell_x + 1, width - 1)]
                
                old_height = h00 * (1 - offset_x) * (1 - offset_y) + \
                            h10 * offset_x * (1 - offset_y) + \
                            h01 * (1 - offset_x) * offset_y + \
                            h11 * offset_x * offset_y
                
                new_height = new_h00 * (1 - new_offset_x) * (1 - new_offset_y) + \
                            new_h10 * new_offset_x * (1 - new_offset_y) + \
                            new_h01 * (1 - new_offset_x) * new_offset_y + \
                            new_h11 * new_offset_x * new_offset_y
                
                height_diff = new_height - old_height
                
                # Calculate sediment capacity
                capacity = max(-height_diff, params.min_slope) * speed * water * params.capacity
                
                if sediment > capacity or height_diff > 0:
                    # Deposit sediment
                    amount = (sediment - capacity) * params.deposition if height_diff <= 0 else min(height_diff, sediment)
                    sediment -= amount
                    
                    # Distribute deposit to cell corners
                    result[cell_y, cell_x] += amount * (1 - offset_x) * (1 - offset_y)
                    result[cell_y, min(cell_x + 1, width - 1)] += amount * offset_x * (1 - offset_y)
                    result[min(cell_y + 1, height - 1), cell_x] += amount * (1 - offset_x) * offset_y
                    result[min(cell_y + 1, height - 1), min(cell_x + 1, width - 1)] += amount * offset_x * offset_y
                else:
                    # Erode terrain
                    amount = min((capacity - sediment) * params.erosion, -height_diff)
                    sediment += amount
                    
                    result[cell_y, cell_x] -= amount * (1 - offset_x) * (1 - offset_y)
                    result[cell_y, min(cell_x + 1, width - 1)] -= amount * offset_x * (1 - offset_y)
                    result[min(cell_y + 1, height - 1), cell_x] -= amount * (1 - offset_x) * offset_y
                    result[min(cell_y + 1, height - 1), min(cell_x + 1, width - 1)] -= amount * offset_x * offset_y
                
                # Update droplet
                speed = np.sqrt(max(speed * speed + height_diff * params.gravity, 0))
                water *= (1 - params.evaporation)
                pos_x = new_pos_x
                pos_y = new_pos_y
                
                if water < 0.01:
                    break
        
        # Normalize
        result = np.clip(result, 0, 1)
        return result
    
    def thermal_erosion(
        self,
        heightmap: np.ndarray,
        iterations: int = 50,
        talus_angle: float = 0.5,
        erosion_rate: float = 0.3
    ) -> np.ndarray:
        """
        Simulate thermal weathering based on talus angle.
        Material slides down when slope exceeds threshold.
        """
        result = heightmap.copy().astype(np.float64)
        height, width = result.shape
        
        for _ in range(iterations):
            # Calculate gradients
            padded = np.pad(result, 1, mode='edge')
            
            # Height differences to neighbors (8-directional)
            neighbors = [
                padded[:-2, 1:-1],   # top
                padded[2:, 1:-1],    # bottom
                padded[1:-1, :-2],   # left
                padded[1:-1, 2:],    # right
                padded[:-2, :-2],    # top-left
                padded[:-2, 2:],     # top-right
                padded[2:, :-2],     # bottom-left
                padded[2:, 2:]       # bottom-right
            ]
            
            # Distances for diagonal vs cardinal
            distances = [1, 1, 1, 1, np.sqrt(2), np.sqrt(2), np.sqrt(2), np.sqrt(2)]
            
            for neighbor, dist in zip(neighbors, distances):
                diff = result - neighbor
                slope = diff / dist
                
                # Find cells where slope exceeds talus angle
                mask = slope > talus_angle
                
                # Transfer material
                transfer = (diff - talus_angle * dist) * erosion_rate * 0.5
                transfer = np.where(mask, transfer, 0)
                
                result -= transfer
                # Note: In a full impl, we'd add to neighbors too
        
        return np.clip(result, 0, 1)
    
    def apply(
        self,
        heightmap: np.ndarray,
        hydraulic: bool = True,
        thermal: bool = True,
        hydraulic_params: ErosionParams = None,
        thermal_iterations: int = 30
    ) -> np.ndarray:
        """Apply erosion pipeline to heightmap"""
        result = heightmap.copy()
        
        if hydraulic:
            result = self.hydraulic_erosion(result, hydraulic_params)
        
        if thermal:
            result = self.thermal_erosion(result, thermal_iterations)
        
        return result

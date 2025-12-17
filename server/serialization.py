"""
Serialization utilities for heightmap/image data.
"""

import numpy as np
from PIL import Image
import base64
from io import BytesIO
from typing import Tuple


def heightmap_to_png_base64(heightmap: np.ndarray) -> str:
    """
    Convert heightmap array to base64-encoded PNG.
    Heightmap values should be in 0-1 range.
    """
    # Scale to 0-255 and convert to uint8
    scaled = (np.clip(heightmap, 0, 1) * 255).astype(np.uint8)
    
    # Create grayscale image
    img = Image.fromarray(scaled, mode='L')
    
    # Encode to PNG and base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def normal_map_to_png_base64(normal_map: np.ndarray) -> str:
    """
    Convert normal map array to base64-encoded PNG.
    Normal map should have shape (H, W, 3) with values in 0-1 range.
    """
    # Scale to 0-255
    scaled = (np.clip(normal_map, 0, 1) * 255).astype(np.uint8)
    
    # Create RGB image
    img = Image.fromarray(scaled, mode='RGB')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def splat_map_to_png_base64(splat_map: np.ndarray) -> str:
    """
    Convert splat map array to base64-encoded PNG.
    Splat map should have shape (H, W, 4) with values in 0-1 range.
    """
    # Scale to 0-255
    scaled = (np.clip(splat_map, 0, 1) * 255).astype(np.uint8)
    
    # Create RGBA image
    img = Image.fromarray(scaled, mode='RGBA')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def base64_to_heightmap(b64_string: str) -> np.ndarray:
    """
    Decode base64 PNG back to heightmap array.
    Returns values in 0-1 range.
    """
    buffer = BytesIO(base64.b64decode(b64_string))
    img = Image.open(buffer).convert('L')
    
    return np.array(img).astype(np.float64) / 255.0

"""
Export utilities for terrain data.
Supports OBJ mesh, RAW heightmap, and PNG exports.
"""

import numpy as np
from io import BytesIO
import struct


def heightmap_to_obj(heightmap: np.ndarray, scale: float = 100.0, height_scale: float = 30.0) -> str:
    """
    Convert heightmap to OBJ mesh format.
    Compatible with Blender, Unity, Godot, and most 3D software.
    
    Args:
        heightmap: 2D numpy array with values in 0-1 range
        scale: XZ plane scale
        height_scale: Y (height) scale
    
    Returns:
        OBJ file content as string
    """
    height, width = heightmap.shape
    
    lines = []
    lines.append("# Terrain mesh exported from 3D TerrainGen Studio")
    lines.append(f"# Size: {width}x{height}")
    lines.append("")
    
    # Generate vertices
    for z in range(height):
        for x in range(width):
            # Normalize coordinates to [-0.5, 0.5] range then scale
            vx = ((x / (width - 1)) - 0.5) * scale
            vz = ((z / (height - 1)) - 0.5) * scale
            vy = heightmap[z, x] * height_scale
            lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")
    
    lines.append("")
    
    # Generate texture coordinates
    for z in range(height):
        for x in range(width):
            u = x / (width - 1)
            v = 1 - (z / (height - 1))  # Flip V for most software
            lines.append(f"vt {u:.6f} {v:.6f}")
    
    lines.append("")
    
    # Generate normals (calculate from heightmap gradient)
    normals = []
    for z in range(height):
        for x in range(width):
            # Calculate gradient
            dx = 0.0
            dz = 0.0
            
            if x > 0 and x < width - 1:
                dx = (heightmap[z, x + 1] - heightmap[z, x - 1]) * height_scale
            if z > 0 and z < height - 1:
                dz = (heightmap[z + 1, x] - heightmap[z - 1, x]) * height_scale
            
            # Normal from gradient
            nx = -dx
            ny = 2.0
            nz = -dz
            
            # Normalize
            length = np.sqrt(nx*nx + ny*ny + nz*nz)
            nx /= length
            ny /= length
            nz /= length
            
            lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}")
    
    lines.append("")
    lines.append("# Faces")
    
    # Generate faces (quads split into triangles)
    for z in range(height - 1):
        for x in range(width - 1):
            # Vertex indices (1-based in OBJ)
            v1 = z * width + x + 1
            v2 = z * width + (x + 1) + 1
            v3 = (z + 1) * width + (x + 1) + 1
            v4 = (z + 1) * width + x + 1
            
            # Two triangles per quad, with texture coords and normals
            lines.append(f"f {v1}/{v1}/{v1} {v2}/{v2}/{v2} {v3}/{v3}/{v3}")
            lines.append(f"f {v1}/{v1}/{v1} {v3}/{v3}/{v3} {v4}/{v4}/{v4}")
    
    return "\n".join(lines)


def heightmap_to_raw(heightmap: np.ndarray, bit_depth: int = 16) -> bytes:
    """
    Convert heightmap to RAW format for Unity terrain.
    
    Args:
        heightmap: 2D numpy array with values in 0-1 range
        bit_depth: 8 or 16 bit depth
    
    Returns:
        RAW bytes data
    """
    if bit_depth == 16:
        # Scale to 0-65535 range
        data = (np.clip(heightmap, 0, 1) * 65535).astype(np.uint16)
        # Unity expects little-endian
        return data.tobytes()
    else:
        # 8-bit
        data = (np.clip(heightmap, 0, 1) * 255).astype(np.uint8)
        return data.tobytes()


def heightmap_to_png_bytes(heightmap: np.ndarray) -> bytes:
    """
    Convert heightmap to PNG bytes.
    Compatible with all engines as heightmap texture.
    """
    from PIL import Image
    
    # Scale to 0-255
    data = (np.clip(heightmap, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(data, mode='L')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


def create_export_package(heightmap: np.ndarray, normal_map: np.ndarray, splat_map: np.ndarray) -> dict:
    """
    Create complete export package with all formats.
    
    Returns:
        Dict with base64 encoded exports
    """
    import base64
    
    # Generate exports
    obj_data = heightmap_to_obj(heightmap)
    raw_16bit = heightmap_to_raw(heightmap, 16)
    raw_8bit = heightmap_to_raw(heightmap, 8)
    heightmap_png = heightmap_to_png_bytes(heightmap)
    
    # Normal map PNG
    from PIL import Image
    normal_data = (np.clip(normal_map, 0, 1) * 255).astype(np.uint8)
    normal_img = Image.fromarray(normal_data, mode='RGB')
    normal_buffer = BytesIO()
    normal_img.save(normal_buffer, format='PNG')
    normal_buffer.seek(0)
    normal_png = normal_buffer.read()
    
    return {
        "obj": base64.b64encode(obj_data.encode('utf-8')).decode('utf-8'),
        "raw_16bit": base64.b64encode(raw_16bit).decode('utf-8'),
        "raw_8bit": base64.b64encode(raw_8bit).decode('utf-8'),
        "heightmap_png": base64.b64encode(heightmap_png).decode('utf-8'),
        "normal_png": base64.b64encode(normal_png).decode('utf-8')
    }

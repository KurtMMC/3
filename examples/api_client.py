
import requests
import base64
import json
import os

# Configuration
API_URL = "http://localhost:8000/api"
OUTPUT_DIR = "output"

def save_base64_file(data, path):
    """Decode base64 string and save to file"""
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Saved: {path}")

def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Connecting to {API_URL}...")
    
    # 1. Check Health
    try:
        health = requests.get(f"{API_URL}/health")
        print(f"Server Status: {health.json()}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running?")
        return

    # 2. Define Terrain Parameters
    params = {
        "seed": 12345,
        "size": 512,
        "noise_algorithm": "simplex",
        "frequency": 2.5,
        "amplitude": 1.2,
        "octaves": 6,
        "persistence": 0.5,
        "lacunarity": 2.0,
        "enable_hydraulic": True,
        "erosion_iterations": 5000,
        "erosion_strength": 0.5
    }

    print("\nRequesting terrain export with parameters:")
    print(json.dumps(params, indent=2))
    
    # 3. Request Export
    try:
        response = requests.post(f"{API_URL}/export_terrain", json=params)
        
        if response.status_code == 200:
            data = response.json()
            print("\nSuccess! Saving files...")
            
            # Save all exported formats
            save_base64_file(data["obj"], f"{OUTPUT_DIR}/terrain.obj")
            save_base64_file(data["heightmap_png"], f"{OUTPUT_DIR}/heightmap.png")
            save_base64_file(data["normal_png"], f"{OUTPUT_DIR}/normal_map.png")
            save_base64_file(data["raw_16bit"], f"{OUTPUT_DIR}/terrain_16bit.raw")
            
            print(f"\nAll files saved to ./{OUTPUT_DIR}/")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error during request: {e}")

if __name__ == "__main__":
    main()

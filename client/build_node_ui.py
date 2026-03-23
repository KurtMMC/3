import os

client_dir = os.path.dirname(os.path.abspath(__file__))

index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D TerrainGen Studio</title>

    <script src="https://cdn.babylonjs.com/babylon.js"></script>
    <script src="https://cdn.babylonjs.com/loaders/babylonjs.loaders.min.js"></script>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/litegraph.js/0.7.12/css/litegraph.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/litegraph.js/0.7.12/litegraph.min.js"></script>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="styles.css">
    <style>
        .node-editor-container {
            flex: 1;
            height: 100%;
            background: #111;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            position: relative;
            overflow: hidden;
        }
        #litegraphCanvas {
            width: 100% !important;
            height: 100% !important;
            display: block;
            outline: none;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <header class="header">
            <div class="logo">
                <span class="logo-icon">▲</span>
                <span class="logo-text">3D TerrainGen Studio</span>
            </div>
            <div class="header-subtitle">Interactive Node-Based Generator</div>
        </header>

        <div class="main-content">
            <!-- Node Graph Editor Area -->
            <div class="node-editor-container">
                <canvas id="litegraphCanvas"></canvas>
            </div>

            <!-- Viewport Area -->
            <main class="viewport-area">
                <div class="viewport-container" style="flex: 2;">
                    <canvas id="renderCanvas"></canvas>
                    <div class="viewport-overlay" id="viewportOverlay">
                        <p>Generate terrain from the Node Graph to view it here.</p>
                    </div>
                </div>

                <section class="output-maps" style="flex: 1;">
                    <h3 class="section-title">Output Maps (2D)</h3>
                    <div class="maps-grid">
                        <div class="map-card">
                            <div class="map-preview" id="heightmapPreview"><span class="map-placeholder">Heightmap</span></div>
                            <span class="map-label">Heightmap</span>
                        </div>
                        <div class="map-card">
                            <div class="map-preview" id="normalMapPreview"><span class="map-placeholder">Normal Map</span></div>
                            <span class="map-label">Normal Map</span>
                        </div>
                        <div class="map-card">
                            <div class="map-preview" id="splatMapPreview"><span class="map-placeholder">Splat Map</span></div>
                            <span class="map-label">Splat Map</span>
                        </div>
                    </div>
                </section>
                
                <!-- Export Section -->
                <section class="control-section export-section" id="exportSection" style="display: none; padding: 15px; background: var(--bg-secondary); border-radius: 12px; border: 1px solid var(--border-color); flex-shrink: 0;">
                    <h3 class="section-title">Export Options</h3>
                    <div class="export-buttons" style="flex-direction: row; display: flex; gap: 10px;">
                        <button id="exportOBJ" class="btn-export" title="For Blender, Unity, Godot">📦 OBJ Mesh</button>
                        <button id="exportRAW" class="btn-export" title="For Unity Terrain">🗺️ RAW (Unity)</button>
                        <button id="exportPNG" class="btn-export" title="Heightmap + Normal Map">🖼️ PNG Maps</button>
                    </div>
                </section>
            </main>
        </div>
    </div>

    <!-- The viewer configures the Babylon canvas -->
    <script src="terrain-viewer.js"></script>
    <!-- Define custom LiteGraph nodes -->
    <script src="nodes.js"></script>
    <!-- Set up app and graph -->
    <script src="app.js"></script>
</body>
</html>
"""

with open(os.path.join(client_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

print("Created index.html")

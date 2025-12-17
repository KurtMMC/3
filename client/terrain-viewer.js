/**
 * Terrain Viewer - Babylon.js 3D terrain rendering
 */

class TerrainViewer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.engine = null;
        this.scene = null;
        this.camera = null;
        this.light = null;
        this.terrainMesh = null;
        this.heightmapData = null;

        this.init();
    }

    init() {
        // Create Babylon engine
        this.engine = new BABYLON.Engine(this.canvas, true, {
            preserveDrawingBuffer: true,
            stencil: true
        });

        // Create scene
        this.scene = new BABYLON.Scene(this.engine);
        this.scene.clearColor = new BABYLON.Color4(0.05, 0.05, 0.05, 1);

        // Create camera
        this.camera = new BABYLON.ArcRotateCamera(
            "camera",
            -Math.PI / 2,
            Math.PI / 3,
            150,
            new BABYLON.Vector3(0, 0, 0),
            this.scene
        );
        this.camera.attachControl(this.canvas, true);
        this.camera.wheelPrecision = 10;
        this.camera.minZ = 0.1;
        this.camera.lowerRadiusLimit = 20;
        this.camera.upperRadiusLimit = 400;
        this.camera.panningSensibility = 50;

        // Create lights
        this.light = new BABYLON.HemisphericLight(
            "light",
            new BABYLON.Vector3(0.5, 1, 0.25),
            this.scene
        );
        this.light.intensity = 1.0;
        this.light.groundColor = new BABYLON.Color3(0.2, 0.2, 0.25);

        // Additional directional light for shadows/depth
        const dirLight = new BABYLON.DirectionalLight(
            "dirLight",
            new BABYLON.Vector3(-0.5, -1, -0.5),
            this.scene
        );
        dirLight.intensity = 0.5;

        // Start render loop
        this.engine.runRenderLoop(() => {
            this.scene.render();
        });

        // Handle resize
        window.addEventListener("resize", () => {
            this.engine.resize();
        });
    }

    /**
     * Create terrain mesh from heightmap data
     * @param {Float32Array|number[][]} heightmapData - 2D heightmap array
     * @param {number} size - Grid size
     * @param {Object} options - Additional options
     */
    createTerrain(heightmapData, size, options = {}) {
        const {
            heightScale = 30,
            subdivisions = size - 1,
            width = 100,
            depth = 100
        } = options;

        // Remove existing terrain
        if (this.terrainMesh) {
            this.terrainMesh.dispose();
        }

        // Store heightmap data
        this.heightmapData = heightmapData;

        // Create ground mesh
        this.terrainMesh = BABYLON.MeshBuilder.CreateGround(
            "terrain",
            {
                width: width,
                height: depth,
                subdivisions: Math.min(subdivisions, 256),
                updatable: true
            },
            this.scene
        );

        // Get vertex data
        const positions = this.terrainMesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
        const indices = this.terrainMesh.getIndices();

        // Calculate vertices per row
        const verticesPerRow = Math.min(subdivisions + 1, 257);

        // Apply heightmap to vertices
        for (let i = 0; i < positions.length / 3; i++) {
            const x = i % verticesPerRow;
            const z = Math.floor(i / verticesPerRow);

            // Map to heightmap coordinates
            const hx = Math.floor((x / (verticesPerRow - 1)) * (size - 1));
            const hz = Math.floor((z / (verticesPerRow - 1)) * (size - 1));

            // Get height from heightmap (handle both array and typed array)
            let height;
            if (Array.isArray(heightmapData)) {
                height = heightmapData[hz] ? heightmapData[hz][hx] || 0 : 0;
            } else {
                height = heightmapData[hz * size + hx] || 0;
            }

            // Set Y position (height)
            positions[i * 3 + 1] = height * heightScale;
        }

        // Update mesh
        this.terrainMesh.updateVerticesData(BABYLON.VertexBuffer.PositionKind, positions);

        // Recalculate normals
        const normals = [];
        BABYLON.VertexData.ComputeNormals(positions, indices, normals);
        this.terrainMesh.updateVerticesData(BABYLON.VertexBuffer.NormalKind, normals);

        // Create and apply material
        this.applyTerrainMaterial();

        // Reset camera
        this.resetCamera();
    }

    /**
     * Apply gradient material based on height
     */
    applyTerrainMaterial() {
        const material = new BABYLON.StandardMaterial("terrainMat", this.scene);

        // Enable vertex colors for height-based coloring
        material.diffuseColor = new BABYLON.Color3(0.4, 0.6, 0.3);
        material.specularColor = new BABYLON.Color3(0.1, 0.1, 0.1);
        material.specularPower = 32;

        // Custom shader for height-based coloring
        BABYLON.Effect.ShadersStore["terrainVertexShader"] = `
            precision highp float;
            
            attribute vec3 position;
            attribute vec3 normal;
            
            uniform mat4 worldViewProjection;
            uniform mat4 world;
            
            varying vec3 vPosition;
            varying vec3 vNormal;
            varying float vHeight;
            
            void main() {
                vec4 worldPos = world * vec4(position, 1.0);
                vPosition = worldPos.xyz;
                vNormal = normalize(mat3(world) * normal);
                vHeight = position.y;
                gl_Position = worldViewProjection * vec4(position, 1.0);
            }
        `;

        BABYLON.Effect.ShadersStore["terrainFragmentShader"] = `
            precision highp float;
            
            varying vec3 vPosition;
            varying vec3 vNormal;
            varying float vHeight;
            
            uniform vec3 lightDirection;
            
            void main() {
                // Height-based colors
                vec3 waterColor = vec3(0.1, 0.3, 0.5);
                vec3 sandColor = vec3(0.76, 0.7, 0.5);
                vec3 grassColor = vec3(0.2, 0.5, 0.2);
                vec3 rockColor = vec3(0.4, 0.35, 0.3);
                vec3 snowColor = vec3(0.95, 0.95, 1.0);
                
                // Normalize height (assuming 0-30 range from heightScale)
                float h = clamp(vHeight / 30.0, 0.0, 1.0);
                
                // Blend colors based on height
                vec3 color;
                if (h < 0.1) {
                    color = mix(waterColor, sandColor, h / 0.1);
                } else if (h < 0.3) {
                    color = mix(sandColor, grassColor, (h - 0.1) / 0.2);
                } else if (h < 0.6) {
                    color = mix(grassColor, rockColor, (h - 0.3) / 0.3);
                } else {
                    color = mix(rockColor, snowColor, (h - 0.6) / 0.4);
                }
                
                // Add slope-based rock
                float slope = 1.0 - abs(dot(vNormal, vec3(0.0, 1.0, 0.0)));
                if (slope > 0.4) {
                    color = mix(color, rockColor, (slope - 0.4) * 2.0);
                }
                
                // Simple lighting
                float light = max(dot(vNormal, normalize(lightDirection)), 0.0) * 0.6 + 0.4;
                
                gl_FragColor = vec4(color * light, 1.0);
            }
        `;

        const shaderMaterial = new BABYLON.ShaderMaterial(
            "terrainShader",
            this.scene,
            { vertex: "terrain", fragment: "terrain" },
            {
                attributes: ["position", "normal"],
                uniforms: ["worldViewProjection", "world", "lightDirection"]
            }
        );

        shaderMaterial.setVector3("lightDirection", new BABYLON.Vector3(0.5, 1, 0.25));
        shaderMaterial.backFaceCulling = false;

        this.terrainMesh.material = shaderMaterial;
    }

    /**
     * Reset camera to view entire terrain
     */
    resetCamera() {
        this.camera.setPosition(new BABYLON.Vector3(80, 60, 80));
        this.camera.setTarget(BABYLON.Vector3.Zero());
    }

    /**
     * Load terrain from base64 heightmap image
     * @param {string} base64Image - Base64 encoded PNG heightmap
     */
    loadFromBase64(base64Image, size) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                // Create canvas to read pixel data
                const canvas = document.createElement('canvas');
                canvas.width = size;
                canvas.height = size;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, size, size);

                // Get pixel data
                const imageData = ctx.getImageData(0, 0, size, size);
                const pixels = imageData.data;

                // Convert to heightmap array (use red channel, normalized to 0-1)
                const heightmap = [];
                for (let y = 0; y < size; y++) {
                    const row = [];
                    for (let x = 0; x < size; x++) {
                        const idx = (y * size + x) * 4;
                        row.push(pixels[idx] / 255);
                    }
                    heightmap.push(row);
                }

                // Create terrain
                this.createTerrain(heightmap, size);
                resolve();
            };
            img.onerror = reject;
            img.src = `data:image/png;base64,${base64Image}`;
        });
    }

    /**
     * Dispose resources
     */
    dispose() {
        if (this.terrainMesh) {
            this.terrainMesh.dispose();
        }
        this.scene.dispose();
        this.engine.dispose();
    }
}

// Export for use
window.TerrainViewer = TerrainViewer;

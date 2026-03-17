/**
 * Main Application - Connects UI controls to terrain viewer via API
 */

const API_BASE_URL = window.location.origin + '/api';

class App {
    constructor() {
        this.viewer = null;
        this.controls = null;
        this.lastExportData = null;

        this.init();
    }

    init() {
        // Initialize terrain viewer
        this.viewer = new TerrainViewer('renderCanvas');

        // Initialize controls
        this.controls = new Controls();

        // Set up generate callback
        this.controls.onGenerate(async (params) => {
            await this.generateTerrain(params);
        });

        // Set up export buttons
        this.bindExportButtons();

        console.log('3D TerrainGen Studio initialized');
    }

    bindExportButtons() {
        document.getElementById('exportOBJ')?.addEventListener('click', () => this.exportOBJ());
        document.getElementById('exportRAW')?.addEventListener('click', () => this.exportRAW());
        document.getElementById('exportPNG')?.addEventListener('click', () => this.exportPNG());
    }

    /**
     * Generate terrain via API
     */
    async generateTerrain(params) {
        this.controls.setLoading(true);
        this.controls.showStatus('Generating terrain...');

        try {
            const response = await fetch(`${API_BASE_URL}/generate_terrain`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Generation failed');
            }

            const data = await response.json();

            // Update 3D viewer
            await this.viewer.loadFromBase64(data.heightmap, data.size);

            // Update output map previews
            this.updateMapPreviews(data);

            // Hide overlay
            const overlay = document.getElementById('viewportOverlay');
            if (overlay) {
                overlay.classList.add('hidden');
            }

            // Show export section
            const exportSection = document.getElementById('exportSection');
            if (exportSection) {
                exportSection.style.display = 'block';
            }

            // Show success
            this.controls.showStatus(
                `Generated in ${data.generation_time_ms.toFixed(0)}ms`,
                'success'
            );

        } catch (error) {
            console.error('Generation error:', error);
            this.controls.showStatus(
                error.message || 'Failed to generate terrain. Check server connection.',
                'error'
            );
        } finally {
            this.controls.setLoading(false);
        }
    }

    /**
     * Update the 2D map preview images
     */
    updateMapPreviews(data) {
        const previews = [
            { id: 'heightmapPreview', data: data.heightmap },
            { id: 'normalMapPreview', data: data.normal_map },
            { id: 'splatMapPreview', data: data.splat_map }
        ];

        previews.forEach(({ id, data: imgData }) => {
            const container = document.getElementById(id);
            if (container && imgData) {
                // Clear placeholder
                container.innerHTML = '';

                // Create image
                const img = document.createElement('img');
                img.src = `data:image/png;base64,${imgData}`;
                img.alt = id.replace('Preview', '');
                container.appendChild(img);
            }
        });
    }

    /**
     * Fetch export data from API
     */
    async fetchExportData() {
        const params = this.controls.getRequestParams();

        this.controls.showStatus('Preparing export...');

        const response = await fetch(`${API_BASE_URL}/export_terrain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Export failed');
        }

        return await response.json();
    }

    /**
     * Download a file from base64 data
     */
    downloadFile(base64Data, filename, mimeType) {
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        const blob = new Blob([bytes], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Export OBJ mesh file
     */
    async exportOBJ() {
        try {
            const data = await this.fetchExportData();
            this.downloadFile(data.obj, 'terrain.obj', 'model/obj');
            this.controls.showStatus('OBJ exported successfully!', 'success');
        } catch (error) {
            this.controls.showStatus('Export failed: ' + error.message, 'error');
        }
    }

    /**
     * Export RAW heightmap for Unity
     */
    async exportRAW() {
        try {
            const data = await this.fetchExportData();
            this.downloadFile(data.raw_16bit, 'terrain.raw', 'application/octet-stream');
            this.controls.showStatus('RAW exported for Unity!', 'success');
        } catch (error) {
            this.controls.showStatus('Export failed: ' + error.message, 'error');
        }
    }

    /**
     * Export PNG heightmap and normal map
     */
    async exportPNG() {
        try {
            const data = await this.fetchExportData();

            // Download heightmap
            this.downloadFile(data.heightmap_png, 'terrain_heightmap.png', 'image/png');

            // Download normal map after short delay
            setTimeout(() => {
                this.downloadFile(data.normal_png, 'terrain_normalmap.png', 'image/png');
            }, 500);

            this.controls.showStatus('PNG maps exported!', 'success');
        } catch (error) {
            this.controls.showStatus('Export failed: ' + error.message, 'error');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});


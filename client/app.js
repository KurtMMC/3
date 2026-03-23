const API_BASE_URL = window.location.port === '3000' ? 'http://localhost:8000/api' : window.location.origin + '/api';

class App {
    constructor() {
        this.viewer = null;
        this.graph = null;
        this.canvas = null;
        this.lastExportData = null;
        this.currentConfig = {};

        this.init();
    }

    init() {
        this.viewer = new TerrainViewer('renderCanvas');
        this.bindExportButtons();
        this.bindFullscreen();
        this.initNodeEditor();
        console.log('3D TerrainGen Studio initialized (Node-Based)');
    }

    initNodeEditor() {
        this.graph = new LGraph();
        this.canvas = new LGraphCanvas("#litegraphCanvas", this.graph);
        
        // Ensure canvas resizes correctly
        window.addEventListener("resize", () => {
            const container = document.querySelector('.node-editor-container');
            this.canvas.resize(container.clientWidth, container.clientHeight);
        });
        setTimeout(() => {
            const container = document.querySelector('.node-editor-container');
            this.canvas.resize(container.clientWidth, container.clientHeight);
        }, 100);

        // Create Default Graph
        const globalNode = LiteGraph.createNode("terrain/global_settings");
        globalNode.pos = [50, 200];
        this.graph.add(globalNode);

        const baseNoiseNode = LiteGraph.createNode("terrain/base_noise");
        baseNoiseNode.pos = [350, 150];
        this.graph.add(baseNoiseNode);

        const secondaryNode = LiteGraph.createNode("terrain/secondary_noise");
        secondaryNode.pos = [650, 150];
        // match default settings (disabled)
        secondaryNode.properties.enable_secondary_noise = false;
        secondaryNode.widgets[0].value = false;
        this.graph.add(secondaryNode);

        const erosionNode = LiteGraph.createNode("terrain/erosion");
        erosionNode.pos = [950, 200];
        erosionNode.properties.enable_hydraulic = false;
        erosionNode.widgets[0].value = false;
        erosionNode.properties.enable_thermal = false;
        erosionNode.widgets[1].value = false;
        this.graph.add(erosionNode);

        const outputNode = LiteGraph.createNode("terrain/output");
        outputNode.pos = [1250, 250];
        this.graph.add(outputNode);

        // Connect them
        globalNode.connect(0, baseNoiseNode, 0);
        baseNoiseNode.connect(0, secondaryNode, 0);
        secondaryNode.connect(0, erosionNode, 0);
        erosionNode.connect(0, outputNode, 0);

        this.graph.start();
    }

    bindExportButtons() {
        document.getElementById('exportOBJ')?.addEventListener('click', () => this.exportOBJ());
        document.getElementById('exportRAW')?.addEventListener('click', () => this.exportRAW());
        document.getElementById('exportPNG')?.addEventListener('click', () => this.exportPNG());
        
        document.getElementById('btnSaveGraph')?.addEventListener('click', () => this.saveGraph());
        document.getElementById('btnLoadGraph')?.addEventListener('click', () => {
            document.getElementById('importGraphFile').click();
        });
        document.getElementById('importGraphFile')?.addEventListener('change', (e) => this.loadGraph(e));
    }

    bindFullscreen() {
        const btn = document.getElementById('btnFullscreen');
        if (btn) {
            btn.addEventListener('click', () => {
                const container = document.querySelector('.viewport-container');
                if (!document.fullscreenElement) {
                    if (container.requestFullscreen) {
                        container.requestFullscreen().catch(err => console.error(err));
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    }
                }
            });
            document.addEventListener('fullscreenchange', () => {
                if (document.fullscreenElement) {
                    btn.innerHTML = '🗗 Exit Fullscreen';
                } else {
                    btn.innerHTML = '⛶ Fullscreen';
                }
                setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
            });
        }
    }

    async generateTerrainFromNode(params) {
        this.currentConfig = params;
        this.showStatus('Generating terrain...', 'info');
        
        try {
            const response = await fetch(`${API_BASE_URL}/generate_terrain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Generation failed');
            }

            const data = await response.json();
            await this.viewer.loadFromBase64(data.heightmap, data.size);
            this.updateMapPreviews(data);

            const overlay = document.getElementById('viewportOverlay');
            if (overlay) overlay.classList.add('hidden');

            const exportSection = document.getElementById('exportSection');
            if (exportSection) exportSection.style.display = 'block';

            this.showStatus(`Generated in ${data.generation_time_ms.toFixed(0)}ms`, 'success');
        } catch (error) {
            console.error('Generation error:', error);
            this.showStatus(error.message || 'Failed to generate terrain', 'error');
        }
    }

    showStatus(msg, type) {
        const overlay = document.getElementById('viewportOverlay');
        const indicator = document.getElementById('statusIndicator');
        if (overlay && type !== 'success') {
            overlay.classList.remove('hidden');
            overlay.innerHTML = `<p style="color: ${type === 'error' ? '#ef4444' : 'white'}">${msg}</p>`;
        }
        if (type === 'success') {
            if (overlay) overlay.classList.add('hidden');
            if (indicator) {
                indicator.innerHTML = `✅ ${msg}`;
                indicator.style.opacity = '1';
                setTimeout(() => { indicator.style.opacity = '0'; }, 3000);
            }
        }
    }

    saveGraph() {
        if (!this.graph) return;
        const data = JSON.stringify(this.graph.serialize());
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'terrain_graph.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        this.showStatus('Project Config Saved!', 'success');
    }

    loadGraph(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.graph.configure(data);
                this.showStatus('Project Config Loaded!', 'success');
            } catch (err) {
                console.error(err);
                this.showStatus('Failed to load config file', 'error');
            }
        };
        reader.readAsText(file);
        event.target.value = ''; // Reset file input
    }

    updateMapPreviews(data) {
        const previews = [
            { id: 'heightmapPreview', data: data.heightmap },
            { id: 'normalMapPreview', data: data.normal_map },
            { id: 'splatMapPreview', data: data.splat_map }
        ];

        previews.forEach(({ id, data: imgData }) => {
            const container = document.getElementById(id);
            if (container && imgData) {
                container.innerHTML = '';
                const img = document.createElement('img');
                img.src = `data:image/png;base64,${imgData}`;
                img.alt = id.replace('Preview', '');
                container.appendChild(img);
            }
        });
    }

    async fetchExportData() {
        const params = this.currentConfig;
        const response = await fetch(`${API_BASE_URL}/export_terrain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Export failed');
        }
        return await response.json();
    }

    downloadFile(base64Data, filename, mimeType) {
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);

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

    async exportOBJ() {
        try {
            const data = await this.fetchExportData();
            this.downloadFile(data.obj, 'terrain.obj', 'model/obj');
        } catch (error) { console.error(error); }
    }

    async exportRAW() {
        try {
            const data = await this.fetchExportData();
            this.downloadFile(data.raw_16bit, 'terrain.raw', 'application/octet-stream');
        } catch (error) { console.error(error); }
    }

    async exportPNG() {
        try {
            const data = await this.fetchExportData();
            this.downloadFile(data.heightmap_png, 'terrain_heightmap.png', 'image/png');
            setTimeout(() => {
                this.downloadFile(data.normal_png, 'terrain_normalmap.png', 'image/png');
            }, 500);
        } catch (error) { console.error(error); }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

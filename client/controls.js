/**
 * UI Controls - Handles all sidebar control interactions
 */

class Controls {
    constructor() {
        this.values = this.getDefaultValues();
        this.callbacks = {};

        this.init();
    }

    getDefaultValues() {
        return {
            // Basic
            mapSize: 256,
            seed: 42,

            // Noise
            noiseAlgorithm: 'simplex',
            fractalType: 'fbm',
            octaves: 6,
            frequency: 3.0,
            persistence: 0.5,
            lacunarity: 2.0,
            amplitude: 1.0,

            // Erosion
            enableHydraulic: false,
            enableThermal: false,
            erosionIterations: 30000,
            erosionStrength: 0.3,

            // Layer Mixing
            enableSecondaryNoise: false,
            secondaryAlgorithm: 'perlin',
            secondaryFrequency: 5.0,
            secondaryAmplitude: 0.5,
            blendMode: 'add',
            blendWeight: 0.5,

            // Phase II — Wave Enhancement (Eq. 2)
            waveCount: 8,
            waveIntensity: 0.3,

            // Phase IV — Thermal Erosion (Eq. 5)
            talusAngle: 0.5,
            thermalRate: 0.3
        };
    }

    init() {
        this.bindSliders();
        this.bindSelects();
        this.bindInputs();
        this.bindToggles();
        this.bindButtons();
        this.bindLayerMixing();
    }

    bindSliders() {
        const sliders = [
            { id: 'octaves', prop: 'octaves', format: v => parseInt(v) },
            { id: 'frequency', prop: 'frequency', format: v => parseFloat(v).toFixed(1) },
            { id: 'persistence', prop: 'persistence', format: v => parseFloat(v).toFixed(2) },
            { id: 'lacunarity', prop: 'lacunarity', format: v => parseFloat(v).toFixed(1) },
            { id: 'amplitude', prop: 'amplitude', format: v => parseFloat(v).toFixed(1) },
            { id: 'erosionIterations', prop: 'erosionIterations', format: v => parseInt(v) },
            { id: 'erosionStrength', prop: 'erosionStrength', format: v => parseFloat(v).toFixed(1) },
            // Layer mixing sliders
            { id: 'secondaryFrequency', prop: 'secondaryFrequency', format: v => parseFloat(v).toFixed(1) },
            { id: 'secondaryAmplitude', prop: 'secondaryAmplitude', format: v => parseFloat(v).toFixed(1) },
            { id: 'blendWeight', prop: 'blendWeight', format: v => parseFloat(v).toFixed(2) },
            // Phase II sliders
            { id: 'waveCount',     prop: 'waveCount',     format: v => parseInt(v) },
            { id: 'waveIntensity', prop: 'waveIntensity', format: v => parseFloat(v).toFixed(2) },
            // Phase IV thermal sliders
            { id: 'talusAngle',   prop: 'talusAngle',   format: v => parseFloat(v).toFixed(2) },
            { id: 'thermalRate',  prop: 'thermalRate',  format: v => parseFloat(v).toFixed(2) }
        ];

        sliders.forEach(({ id, prop, format }) => {
            const slider = document.getElementById(id);
            const display = document.getElementById(`${id}Value`);

            if (slider) {
                slider.addEventListener('input', (e) => {
                    const value = format(e.target.value);
                    this.values[prop] = parseFloat(value);
                    if (display) {
                        display.textContent = value;
                    }
                });
            }
        });
    }

    bindSelects() {
        const selects = [
            { id: 'mapSize', prop: 'mapSize', parse: parseInt },
            { id: 'noiseAlgorithm', prop: 'noiseAlgorithm', parse: v => v },
            { id: 'fractalType', prop: 'fractalType', parse: v => v },
            // Layer mixing selects
            { id: 'secondaryAlgorithm', prop: 'secondaryAlgorithm', parse: v => v },
            { id: 'blendMode', prop: 'blendMode', parse: v => v }
        ];

        selects.forEach(({ id, prop, parse }) => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', (e) => {
                    this.values[prop] = parse(e.target.value);

                    // Show Phase II controls only when wave_combination selected
                    if (id === 'blendMode') {
                        const waveOpts = document.getElementById('waveEnhancementOptions');
                        if (waveOpts) {
                            waveOpts.style.display = (e.target.value === 'wave_combination') ? 'block' : 'none';
                        }
                    }
                });
            }
        });
    }

    bindInputs() {
        const seedInput = document.getElementById('seed');
        if (seedInput) {
            seedInput.addEventListener('change', (e) => {
                this.values.seed = parseInt(e.target.value) || 42;
            });
        }
    }

    bindToggles() {
        const hydraulicBtn = document.getElementById('toggleHydraulic');
        const thermalBtn = document.getElementById('toggleThermal');
        const erosionOptions = document.getElementById('erosionOptions');

        const updateErosionUI = () => {
            const hasErosion = this.values.enableHydraulic || this.values.enableThermal;
            if (erosionOptions) {
                erosionOptions.style.display = hasErosion ? 'block' : 'none';
            }
        };

        if (hydraulicBtn) {
            hydraulicBtn.addEventListener('click', () => {
                this.values.enableHydraulic = !this.values.enableHydraulic;
                hydraulicBtn.classList.toggle('active', this.values.enableHydraulic);
                updateErosionUI();
            });
        }

        if (thermalBtn) {
            thermalBtn.addEventListener('click', () => {
                this.values.enableThermal = !this.values.enableThermal;
                thermalBtn.classList.toggle('active', this.values.enableThermal);
                updateErosionUI();
            });
        }
    }

    bindLayerMixing() {
        const checkbox = document.getElementById('enableSecondaryNoise');
        const optionsDiv = document.getElementById('layerMixingOptions');

        if (checkbox && optionsDiv) {
            checkbox.addEventListener('change', (e) => {
                this.values.enableSecondaryNoise = e.target.checked;
                optionsDiv.style.display = e.target.checked ? 'block' : 'none';
            });
        }
    }

    bindButtons() {
        const randomBtn = document.getElementById('randomSeed');
        const seedInput = document.getElementById('seed');

        if (randomBtn && seedInput) {
            randomBtn.addEventListener('click', () => {
                const newSeed = Math.floor(Math.random() * 100000);
                seedInput.value = newSeed;
                this.values.seed = newSeed;
            });
        }
    }

    /**
     * Get current control values as API request format
     */
    getRequestParams() {
        return {
            seed: this.values.seed,
            size: this.values.mapSize,
            noise_algorithm: this.values.noiseAlgorithm,
            fractal_type: this.values.fractalType,
            octaves: this.values.octaves,
            frequency: this.values.frequency,
            persistence: this.values.persistence,
            lacunarity: this.values.lacunarity,
            amplitude: this.values.amplitude,
            enable_hydraulic: this.values.enableHydraulic,
            enable_thermal: this.values.enableThermal,
            erosion_iterations: this.values.erosionIterations,
            erosion_strength: this.values.erosionStrength,
            // Layer mixing
            enable_secondary_noise: this.values.enableSecondaryNoise,
            secondary_algorithm: this.values.secondaryAlgorithm,
            secondary_frequency: this.values.secondaryFrequency,
            secondary_amplitude: this.values.secondaryAmplitude,
            blend_mode: this.values.blendMode,
            blend_weight: this.values.blendWeight,
            // Phase II — Wave Enhancement (Eq. 2)
            wave_count: this.values.waveCount,
            wave_intensity: this.values.waveIntensity,
            // Phase IV — Thermal Erosion (Eq. 5)
            talus_angle: this.values.talusAngle,
            thermal_rate: this.values.thermalRate
        };
    }

    /**
     * Register callback for generate button
     */
    onGenerate(callback) {
        this.callbacks.generate = callback;

        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                if (this.callbacks.generate) {
                    this.callbacks.generate(this.getRequestParams());
                }
            });
        }
    }

    /**
     * Set loading state for generate button
     */
    setLoading(loading) {
        const generateBtn = document.getElementById('generateBtn');
        const btnText = generateBtn?.querySelector('.btn-text');
        const btnLoading = generateBtn?.querySelector('.btn-loading');

        if (generateBtn) {
            generateBtn.disabled = loading;
        }
        if (btnText) {
            btnText.style.display = loading ? 'none' : 'inline';
        }
        if (btnLoading) {
            btnLoading.style.display = loading ? 'flex' : 'none';
        }
    }

    /**
     * Show status message
     */
    showStatus(message, type = '') {
        const status = document.getElementById('status');
        if (status) {
            status.textContent = message;
            status.className = 'status-message' + (type ? ` ${type}` : '');
        }
    }
}

// Export for use
window.Controls = Controls;

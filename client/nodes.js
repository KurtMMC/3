// Register LiteGraph Nodes for Terrain Generation
(function() {
    if (LiteGraph.clearRegisteredTypes) {
        LiteGraph.clearRegisteredTypes();
    } else {
        LiteGraph.registered_node_types = {};
    }
    
    function mergeConfig(base, addition) {
        return Object.assign({}, base, addition);
    }

    class GlobalSettingsNode {
        constructor() {
            this.addOutput("Config", "object");
            this.properties = { seed: 42, size: 256 };
            this.addWidget("number", "Seed", this.properties.seed, (v) => { this.properties.seed = Math.floor(v); }, { min: 0, max: 99999, step: 1, precision: 0 });
            this.addWidget("combo", "Size", this.properties.size.toString(), (v) => { this.properties.size = parseInt(v); }, { values: ["64", "128", "256", "512", "1024", "2048"] });
        }
        onExecute() {
            this.setOutputData(0, { seed: this.properties.seed, size: this.properties.size });
        }
    }
    GlobalSettingsNode.title = "Global Settings";
    LiteGraph.registerNodeType("terrain/global_settings", GlobalSettingsNode);

    class BaseNoiseNode {
        constructor() {
            this.addInput("Config", "object");
            this.addOutput("Config", "object");
            this.properties = { noise_algorithm: "simplex", fractal_type: "fbm", octaves: 6, frequency: 3.0, persistence: 0.5, lacunarity: 2.0, amplitude: 1.0 };
            this.addWidget("combo", "Algorithm", this.properties.noise_algorithm, (v) => { this.properties.noise_algorithm = v; }, { values: ["wave", "harmonic", "perlin", "simplex"] });
            this.addWidget("combo", "Fractal Type", this.properties.fractal_type, (v) => { this.properties.fractal_type = v; }, { values: ["none", "fbm", "ridged", "billow"] });
            this.addWidget("slider", "Octaves", this.properties.octaves, (v) => { this.properties.octaves = Math.floor(v); }, { min: 1, max: 10, step: 1, precision: 0 });
            this.addWidget("slider", "Frequency", this.properties.frequency, (v) => { this.properties.frequency = v; }, { min: 0.1, max: 20.0 });
            this.addWidget("slider", "Persistence", this.properties.persistence, (v) => { this.properties.persistence = v; }, { min: 0.1, max: 1.0 });
            this.addWidget("slider", "Lacunarity", this.properties.lacunarity, (v) => { this.properties.lacunarity = v; }, { min: 1.0, max: 4.0 });
            this.addWidget("slider", "Amplitude", this.properties.amplitude, (v) => { this.properties.amplitude = v; }, { min: 0.1, max: 2.0 });
            this.size = [260, 200];
        }
        onExecute() {
            let config = this.getInputData(0) || {};
            this.setOutputData(0, mergeConfig(config, this.properties));
        }
    }
    BaseNoiseNode.title = "Base Noise";
    LiteGraph.registerNodeType("terrain/base_noise", BaseNoiseNode);

    class SecondaryNoiseNode {
        constructor() {
            this.addInput("Config", "object");
            this.addOutput("Config", "object");
            this.properties = { enable_secondary_noise: true, secondary_algorithm: "perlin", secondary_frequency: 2.5, secondary_amplitude: 0.5, blend_mode: "add", blend_weight: 0.5 };
            this.addWidget("toggle", "Enable", this.properties.enable_secondary_noise, (v) => { this.properties.enable_secondary_noise = v; });
            this.addWidget("combo", "Algorithm", this.properties.secondary_algorithm, (v) => { this.properties.secondary_algorithm = v; }, { values: ["wave", "harmonic", "perlin", "simplex"] });
            this.addWidget("slider", "Frequency", this.properties.secondary_frequency, (v) => { this.properties.secondary_frequency = v; }, { min: 0.1, max: 3.0 });
            this.addWidget("slider", "Amplitude", this.properties.secondary_amplitude, (v) => { this.properties.secondary_amplitude = v; }, { min: 0.1, max: 2.0 });
            this.addWidget("combo", "Blend Mode", this.properties.blend_mode, (v) => { this.properties.blend_mode = v; }, { values: ["add", "multiply", "lerp", "min", "max", "wave_combination"] });
            this.addWidget("slider", "Blend Weight", this.properties.blend_weight, (v) => { this.properties.blend_weight = v; }, { min: 0.0, max: 1.0 });
            this.size = [260, 180];
        }
        onExecute() {
            let config = this.getInputData(0) || {};
            this.setOutputData(0, mergeConfig(config, this.properties));
        }
    }
    SecondaryNoiseNode.title = "Secondary Noise";
    LiteGraph.registerNodeType("terrain/secondary_noise", SecondaryNoiseNode);

    class ErosionNode {
        constructor() {
            this.addInput("Config", "object");
            this.addOutput("Config", "object");
            this.properties = { enable_hydraulic: true, enable_thermal: true, erosion_iterations: 30000, erosion_strength: 0.3 };
            this.addWidget("toggle", "Hydraulic", this.properties.enable_hydraulic, (v) => { this.properties.enable_hydraulic = v; });
            this.addWidget("toggle", "Thermal", this.properties.enable_thermal, (v) => { this.properties.enable_thermal = v; });
            this.addWidget("slider", "Iterations", this.properties.erosion_iterations, (v) => { this.properties.erosion_iterations = Math.floor(v); }, { min: 1000, max: 100000, step: 1000, precision: 0 });
            this.addWidget("slider", "Strength", this.properties.erosion_strength, (v) => { this.properties.erosion_strength = v; }, { min: 0.1, max: 1.0 });
        }
        onExecute() {
            let config = this.getInputData(0) || {};
            this.setOutputData(0, mergeConfig(config, this.properties));
        }
    }
    ErosionNode.title = "Erosion Filter";
    LiteGraph.registerNodeType("terrain/erosion", ErosionNode);

    class OutputNode {
        constructor() {
            this.addInput("Config", "object");
            this.addWidget("button", "GENERATE TERRAIN", null, () => {
                let config = this.getInputData(0);
                if (window.app) {
                    if (!config) config = {};
                    window.app.generateTerrainFromNode(config);
                } else {
                    console.error("Missing app reference");
                }
            });
            this.size = [200, 80];
        }
        onExecute() {
        }
    }
    OutputNode.title = "Final Output";
    LiteGraph.registerNodeType("terrain/output", OutputNode);
})();

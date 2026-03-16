"""
Plot Metrics Script

Generates matplotlib figures to visualize the 3.6 Evaluation Metrics:
1. PSD Log-Log Plot (Spectral Analysis)
2. Feature Diversity Bar Chart (Roughness Index)
3. Terrain Heightmap Visual Comparison
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from scipy.ndimage import laplace

def configure_plot_style():
    """Set standard aesthetics for the presentation graphs"""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.titlesize': 18,
        'grid.alpha': 0.3
    })
    
def get_psd(heightmap):
    """Calculate 1D radially averaged PSD"""
    fft = np.fft.fft2(heightmap)
    power_spectrum = np.abs(np.fft.fftshift(fft)) ** 2
    
    h, w = heightmap.shape
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)
    
    max_radius = min(cx, cy)
    radial_power = np.zeros(max_radius)
    counts = np.zeros(max_radius)
    
    for i in range(h):
        for j in range(w):
            radius = r[i, j]
            if radius < max_radius:
                radial_power[radius] += power_spectrum[i, j]
                counts[radius] += 1
                
    mask = counts > 0
    radial_power[mask] /= counts[mask]
    return np.arange(max_radius)[mask], radial_power[mask]

def compute_roughness(heightmap, split=0.5):
    curvature = np.abs(laplace(heightmap))
    low_mask = heightmap <= split
    high_mask = heightmap > split
    
    rl = np.mean(curvature[low_mask]) if np.any(low_mask) else 0.0
    rh = np.mean(curvature[high_mask]) if np.any(high_mask) else 0.0
    return rl, rh

def create_visualizations(sample_dir: str):
    out_dir = Path(sample_dir)
    fbm_dir = out_dir / "baseline_fbm"
    wave_dir = out_dir / "wave_harmonic"
    graphs_dir = out_dir / "graphs"
    graphs_dir.mkdir(exist_ok=True)
    
    configure_plot_style()
    
    fbm_files = sorted(list(fbm_dir.glob("*.npy")))
    wave_files = sorted(list(wave_dir.glob("*.npy")))
    num_samples = min(len(fbm_files), len(wave_files))
    
    if num_samples == 0:
        print("No samples found.")
        return
        
    print(f"Generating figures for {num_samples} paired samples...")
    
    # Analyze all for averages
    fbm_psd_avg, wave_psd_avg = None, None
    fbm_rl_all, fbm_rh_all = [], []
    wave_rl_all, wave_rh_all = [], []
    
    for i in range(num_samples):
        h_fbm = np.load(fbm_files[i])
        h_wv = np.load(wave_files[i])
        
        freqs, p_fbm = get_psd(h_fbm)
        _, p_wv = get_psd(h_wv)
        
        if fbm_psd_avg is None:
            fbm_psd_avg = np.zeros_like(p_fbm)
            wave_psd_avg = np.zeros_like(p_wv)
            
        # Add to average (skip 0 freq for log log plot safely)
        fbm_psd_avg[:len(p_fbm)] += p_fbm
        wave_psd_avg[:len(p_wv)] += p_wv
        
        rl_f, rh_f = compute_roughness(h_fbm)
        rl_w, rh_w = compute_roughness(h_wv)
        
        fbm_rl_all.append(rl_f); fbm_rh_all.append(rh_f)
        wave_rl_all.append(rl_w); wave_rh_all.append(rh_w)
        
    fbm_psd_avg /= num_samples
    wave_psd_avg /= num_samples
    
    # -----------------------------------------------------------------
    # Figure 1: Structural Complexity (PSD Log-Log)
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    
    valid = (freqs > 1) & (fbm_psd_avg > 0) & (wave_psd_avg > 0)
    f_valid = freqs[valid]
    
    plt.loglog(f_valid, fbm_psd_avg[valid], label='fBm Baseline', color='#00d2ff', alpha=0.8, linewidth=2)
    plt.loglog(f_valid, wave_psd_avg[valid], label='Wave-Harmonic Model', color='#ff3366', alpha=0.8, linewidth=2)
    
    # High Frequency Energy fill (visualize the deviation)
    mid_idx = len(f_valid) // 4
    plt.fill_between(f_valid[mid_idx:], fbm_psd_avg[valid][mid_idx:], wave_psd_avg[valid][mid_idx:], 
                     color='#ff3366', alpha=0.2, label='High-Frequency Energy Increase')

    plt.title('Structural Complexity: Power Spectrum Density')
    plt.xlabel('Spatial Frequency (f)')
    plt.ylabel('Power P(f)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    psd_path = graphs_dir / "fig1_psd_slope.png"
    plt.savefig(psd_path, dpi=300)
    plt.close()
    print(f"Saved: {psd_path}")

    # -----------------------------------------------------------------
    # Figure 2: Feature Diversity (Roughness Bar Chart)
    # -----------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    
    labels = ['Low-Elevation Plains\n(P ≤ 0.5)', 'High-Elevation Peaks\n(P > 0.5)']
    fbm_means = [np.mean(fbm_rl_all), np.mean(fbm_rh_all)]
    wave_means = [np.mean(wave_rl_all), np.mean(wave_rh_all)]
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, fbm_means, width, label='fBm Baseline', color='#00d2ff')
    rects2 = ax.bar(x + width/2, wave_means, width, label='Wave-Harmonic Model', color='#ff3366')
    
    ax.set_ylabel('Mean Laplacian Roughness ($\Delta$∇)')
    ax.set_title('Feature Diversity: Differential Roughness Validation')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    # Add data labels
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.4f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11)
            
    autolabel(rects1)
    autolabel(rects2)
    
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    roughness_path = graphs_dir / "fig2_roughness_diff.png"
    plt.savefig(roughness_path, dpi=300)
    plt.close()
    print(f"Saved: {roughness_path}")
    
    # -----------------------------------------------------------------
    # Figure 3: Example Terrain Comparison (Heatmap)
    # -----------------------------------------------------------------
    plt.figure(figsize=(14, 6))
    
    # Pick a good visual sample (e.g. seed 2)
    idx_plot = 1 if num_samples > 1 else 0
    h_fbm_ex = np.load(fbm_files[idx_plot])
    h_wv_ex = np.load(wave_files[idx_plot])
    
    # Custom colormap for terrain
    colors = ["#1a2a4b", "#2c4875", "#6c8c51", "#8ba85a", "#b5a682", "#d8d3c1", "#ffffff"]
    cmap = LinearSegmentedColormap.from_list("terrain", colors)
    
    plt.subplot(1, 2, 1)
    plt.title('Baseline: fBm (Standard Noise)')
    im1 = plt.imshow(h_fbm_ex, cmap=cmap, vmin=0, vmax=1)
    plt.colorbar(im1, fraction=0.046, pad=0.04)
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.title('Wave-Harmonic (Phase II & III applied)')
    im2 = plt.imshow(h_wv_ex, cmap=cmap, vmin=0, vmax=1)
    plt.colorbar(im2, fraction=0.046, pad=0.04)
    plt.axis('off')
    
    plt.tight_layout()
    terrain_path = graphs_dir / "fig3_terrain_compare.png"
    plt.savefig(terrain_path, dpi=300)
    plt.close()
    print(f"Saved: {terrain_path}")

if __name__ == "__main__":
    create_visualizations("output/validation_samples")

# plot_utils.py
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import rasterio.plot
import plotly.graph_objects as go
import itertools
import numpy as np


def plot_mcda_overlay(composite_norm, extent, selected_geometries, patch_grid=None):
    """
    Plot MCDA composite with optional patch grid and selected NSGA-II patches
    Args:
        composite_norm (np.ndarray): normalized suitability array
        extent (tuple): rasterio.plot.plotting_extent for base map
        selected_geometries (list): list of shapely geometries (polygons)
        patch_grid (GeoDataFrame): optional full patch grid
    """
    plt.figure(figsize=(8, 8))
    im = plt.imshow(composite_norm, cmap='viridis', vmin=0, vmax=1, extent=extent)
    plt.title("Composite Suitability (MCDA + NSGA-II)")
    plt.axis('on')
    cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
    cbar.set_label('Suitability Score')

    # Plot full grid if provided
    if patch_grid is not None:
        for geom in patch_grid.geometry:
            if geom is not None:
                x, y = geom.exterior.xy
                plt.plot(x, y, color='red', linewidth=0.5, alpha=0.2)

    # Highlight selected patches
    for geom in selected_geometries:
        if geom is not None:
            x, y = geom.exterior.xy
            plt.fill(x, y, facecolor='none', edgecolor='white', linewidth=2)

    legend_elements = [
        Patch(facecolor='none', edgecolor='white', linewidth=2, label='Selected Patches'),
        Patch(facecolor='none', edgecolor='red', linewidth=0.5, alpha=0.2, label='Patch Grid')
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.show()


def plot_2d_pareto_fronts(hof_all_runs, valid_patches, objective_cols):
    """
    Plot 2D Pareto front projections for all objective pairs across multiple runs.
    """
    pairs = list(itertools.combinations(objective_cols, 2))
    num_runs = len(hof_all_runs)
    colors = plt.cm.tab10(np.linspace(0, 1, num_runs))
    n = len(objective_cols)
    fig, axes = plt.subplots(n - 1, n - 1, figsize=(20, 20), squeeze=False)
    fig.suptitle("2D Pareto Front Projections", fontsize=20)

    for i, obj1 in enumerate(objective_cols[:-1]):
        for j, obj2 in enumerate(objective_cols[1:], start=1):
            if i < j:
                ax = axes[j - 1, i]
                for run_idx, hof in enumerate(hof_all_runs):
                    vals1 = [valid_patches.iloc[p][obj1] for p in hof]
                    vals2 = [valid_patches.iloc[p][obj2] for p in hof]
                    ax.scatter(vals1, vals2, color=colors[run_idx], s=40, label=f'Run {run_idx + 1}', alpha=0.7)
                ax.set_xlabel(obj1)
                ax.set_ylabel(obj2)
                if i == 0 and j == 1:
                    ax.legend()
            else:
                axes[j - 1, i].axis('off')
    plt.tight_layout()
    plt.show()


def plot_3d_pareto_front_interactive(hof_all_runs, valid_patches, obj1, obj2, obj3):
    """
    Create an interactive 3D plot of Pareto fronts across selected objectives.
    """
    fig = go.Figure()
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'grey', 'olive', 'cyan']
    for run_idx, hof in enumerate(hof_all_runs):
        vals1 = [valid_patches.iloc[p[0]][obj1] for p in hof]
        vals2 = [valid_patches.iloc[p[0]][obj2] for p in hof]
        vals3 = [valid_patches.iloc[p[0]][obj3] for p in hof]
        patch_ids = [p[0] for p in hof]
        lons = [valid_patches.iloc[p[0]]['centroid_x'] for p in hof]
        lats = [valid_patches.iloc[p[0]]['centroid_y'] for p in hof]
        hover_text = [
            f"Run: {run_idx + 1}<br>Patch ID: {patch_ids[i]}<br>{obj1}: {vals1[i]:.3f}<br>{obj2}: {vals2[i]:.3f}<br>{obj3}: {vals3[i]:.3f}<br>Lon: {lons[i]:.5f}<br>Lat: {lats[i]:.5f}"
            for i in range(len(patch_ids))
        ]
        fig.add_trace(go.Scatter3d(
            x=vals1, y=vals2, z=vals3,
            mode='markers',
            marker=dict(size=5, color=colors[run_idx % len(colors)], opacity=0.7),
            name=f'Run {run_idx + 1}',
            text=hover_text,
            hoverinfo='text'
        ))
    fig.update_layout(
        title=f'3D Pareto Front: {obj1} vs {obj2} vs {obj3}',
        scene=dict(
            xaxis_title=obj1,
            yaxis_title=obj2,
            zaxis_title=obj3,
            aspectmode='cube'
        ),
        legend=dict(itemsizing='constant')
    )
    fig.show()

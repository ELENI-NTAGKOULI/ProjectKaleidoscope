# export_utils.py
import os
import geopandas as gpd
import pandas as pd

def save_results(results_df, selected_patches, patch_data, output_dir='results'):
    os.makedirs(output_dir, exist_ok=True)

    # Save CSV
    csv_path = os.path.join(output_dir, 'selected_patches_results.csv')
    results_df.to_csv(csv_path, index=False)
    print(f"📄 Saved CSV: {csv_path}")

    # GeoDataFrame for GeoJSON export
    geoms = [patch_data.iloc[ind[0]].geometry for ind in selected_patches]
    gdf = gpd.GeoDataFrame(results_df.copy(), geometry=geoms, crs=patch_data.crs)

    # Save GeoJSON
    geojson_path = os.path.join(output_dir, 'selected_patches.geojson')
    gdf.to_file(geojson_path, driver='GeoJSON')
    print(f"🌍 Saved GeoJSON: {geojson_path}")

    # Save bounding boxes text
    bbox_path = os.path.join(output_dir, 'bbox_export.txt')
    with open(bbox_path, 'w') as f:
        f.write("# Bounding Box Coordinates (EPSG:25831)\n")
        for _, row in gdf.iterrows():
            bounds = row.geometry.bounds
            coords = f"{bounds[0]:.2f},{bounds[1]:.2f},{bounds[2]:.2f},{bounds[3]:.2f}"
            f.write(f"Patch {row['patch_id']} (Rank {row['rank']}): {coords}\n")
    print(f"🧭 Saved bounding boxes: {bbox_path}")

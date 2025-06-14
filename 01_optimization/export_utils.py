# export_utils.py
import os
import pandas as pd
import geopandas as gpd

def save_results(results_df, selected_patches, patch_data, output_dir='results'):
    os.makedirs(output_dir, exist_ok=True)

    # Save results to CSV
    csv_path = os.path.join(output_dir, 'selected_patches.csv')
    results_df.to_csv(csv_path, index=False)
    print(f"📄 CSV saved: {csv_path}")

    # Save GeoJSON of selected patches
    selected_geoms = [patch_data.iloc[patch[0]].geometry for patch in selected_patches]
    gdf = gpd.GeoDataFrame(results_df, geometry=selected_geoms, crs=patch_data.crs)
    geojson_path = os.path.join(output_dir, 'selected_patches.geojson')
    gdf.to_file(geojson_path, driver='GeoJSON')
    print(f"🗺️ GeoJSON saved: {geojson_path}")

    # Optional: Save bounding boxes
    bbox_txt_path = os.path.join(output_dir, 'bounding_boxes.txt')
    with open(bbox_txt_path, 'w') as f:
        for _, row in results_df.iterrows():
            f.write(f"{row['bbox_coordinates_utm31n']}\n")
    print(f"📐 Bounding boxes saved: {bbox_txt_path}")


import argparse
import warnings
import os
import geopandas as gpd
import pandas as pd
from nsga import run_nsga_pipeline, create_results_dataframe
import export_utils
from supabase import create_client
from datetime import datetime, timezone
import pickle

warnings.filterwarnings("ignore")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="05_results")
    args = parser.parse_args()

    print("\n🔹 Step 2: NSGA-II Optimization")

    os.makedirs(args.output, exist_ok=True)

    # Load valid patches
    valid_path = os.path.join(args.output, "valid_patches.geojson")
    valid_patches = gpd.read_file(valid_path)

    # Run NSGA-II
    results_df, raw_selected = run_nsga_pipeline(valid_patches)

    # Create full results dataframe
    final_df = create_results_dataframe(raw_selected, valid_patches)

    final_df = final_df.drop_duplicates(subset="patch_id", keep="first")

    # Export to CSV + GeoJSON
    csv_path = os.path.join(args.output, "selected_patches.csv")
    final_df.to_csv(csv_path, index=False)
    print(f"📤 Saved CSV to {csv_path}")

    geojson_path = os.path.join(args.output, "selected_patches.geojson")
    gdf = gpd.GeoDataFrame(final_df, geometry=valid_patches.geometry.iloc[final_df['patch_id']], crs=valid_patches.crs)
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"📤 Saved GeoJSON to {geojson_path}")

    # Optional: upload top 5 to Supabase
    upload_to_supabase(final_df)

    print("✅ Optimization and export complete.")

    hof_path = os.path.join(args.output, "hof_all_runs.pkl")
    with open(hof_path, "wb") as f:
        pickle.dump(raw_selected, f)
    print(f"💾 Saved HOF to {hof_path}")

def upload_to_supabase(df):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    table = os.environ.get("SUPABASE_RESULTS_TABLE", "results")
    client = create_client(url, key)

    top5 = df.sort_values("overall_score", ascending=False).drop_duplicates("patch_id").head(5)

    rows = []
    for _, row in top5.iterrows():
        rows.append({
            "patch_id": int(row["patch_id"]),
            "centroid_latitude": float(row["centroid_latitude"]),
            "centroid_longitude": float(row["centroid_longitude"]),
            "bbox_coordinates_utm31n": row["bbox_coordinates_utm31n"],
            "landcoverSuitability": float(row["landcoverSuitability"]),
            "slope": float(row["slope"]),
            "soil": float(row["soil"]),
            "floodRisk": float(row["floodRisk"]),
            "urbanProximity": float(row["urbanProximity"]),
            "overall_score": float(row["overall_score"]),
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    client.table(table).insert(rows).execute()
    print("🟢 Uploaded top 5 to Supabase.")

if __name__ == "__main__":
    main()

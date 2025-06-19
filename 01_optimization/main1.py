import argparse
import os
import gee_fetch, grid, mcda
import warnings
from utils import get_latest_coordinates

warnings.filterwarnings("ignore")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--buffer_km", type=int, default=10)
    parser.add_argument("--output", type=str, default="05_results")
    args = parser.parse_args()

    print("\n🔹 Step 1: GEE Fetch + Grid + MCDA")

    center_lon, center_lat = get_latest_coordinates()

    files, _ = gee_fetch.setup_data_automatically(
        center_lon=center_lon,
        center_lat=center_lat,
        buffer_km=args.buffer_km,
        output_folder=args.output
    )

    rasters = grid.load_and_check_rasters(files)

    patch_grid = grid.create_patch_grid(rasters["study_area"], grid_size=1000)
    valid_patches = grid.extract_patch_statistics(patch_grid, rasters)

    # Export valid patches for next step
    valid_path = os.path.join(args.output, "valid_patches.geojson")
    valid_patches.to_file(valid_path, driver="GeoJSON")
    print(f"📤 Saved valid patches to {valid_path}")

    # Run MCDA and export composite (automatically handled in mcda)
    mcda.compute_composite(rasters)

    print("✅ Preprocessing complete.")

if __name__ == "__main__":
    main()

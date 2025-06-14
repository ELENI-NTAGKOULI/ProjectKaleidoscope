# main.py
# This is the CLI entry point to run the full optimization pipeline

import argparse
from optimization import gee_fetch, grid, mcda, nsga, export_utils
import warnings
warnings.filterwarnings("ignore")

def main():
    parser = argparse.ArgumentParser(description="Run NSGA-II Flood Mitigation Optimization")
    parser.add_argument("--lon", type=float, default=2.9862, help="Longitude of study area center")
    parser.add_argument("--lat", type=float, default=42.0553, help="Latitude of study area center")
    parser.add_argument("--buffer_km", type=int, default=10, help="Buffer radius in km")
    parser.add_argument("--output", type=str, default="results", help="Output folder")
    args = parser.parse_args()

    print("\n🚀 Starting optimization pipeline...")

    # Step 1: Authenticate and download GEE data
    files, region_geojson = gee_fetch.setup_data_automatically(
        center_lon=args.lon, center_lat=args.lat, buffer_km=args.buffer_km, output_folder=args.output
    )

    # Step 2: Load and validate rasters
    rasters = grid.load_and_check_rasters(files)

    # Step 3: Generate patch grid and extract stats
    patch_grid = grid.create_patch_grid(rasters['study_area'], grid_size=1000)
    valid_patches = grid.extract_patch_statistics(patch_grid, rasters)

    # Step 4: Run MCDA to create composite suitability
    composite, composite_norm = mcda.compute_composite(rasters)

    # Step 5: Normalize for NSGA-II and run optimization
    results_df, selected_patches = nsga.run_nsga_pipeline(valid_patches)

    # Step 6: Export results
    export_utils.save_results(results_df, selected_patches, valid_patches, output_dir=args.output)

    print("\n✅ Optimization complete. Results saved to:", args.output)

if __name__ == "__main__":
    main()
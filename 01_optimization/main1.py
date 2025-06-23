import argparse
import os
import warnings
import gee_fetch, grid, mcda
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from utils import get_latest_coordinates, get_supabase_client
import subprocess
import time
import requests
import json
import numpy as np

warnings.filterwarnings("ignore")

def reproject_to_web_mercator(input_path, output_path):
    with rasterio.open(input_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, "EPSG:3857", src.width, src.height, *src.bounds)

        kwargs = src.meta.copy()
        kwargs.update({
            "crs": "EPSG:3857",
            "transform": transform,
            "width": width,
            "height": height
        })

        with rasterio.open(output_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs="EPSG:3857",
                    resampling=Resampling.nearest
                )
    print(f"🌍 Reprojected {input_path} ➜ {output_path}")

def upload_rasters_to_supabase(files_dict, project_id):
    client = get_supabase_client()
    bucket = "raster-exports"
    urls = {}

    for name, path in files_dict.items():
        if not os.path.exists(path):
            continue
        supabase_path = f"{project_id}/{name}.tif"
        with open(path, "rb") as f:
            client.storage.from_(bucket).upload(
                supabase_path,
                f,
                {
                    "content-type": "image/tiff",
                    "x-upsert": "true"
                }
            )
        public_url = f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/{bucket}/{supabase_path}"
        urls[name] = public_url
        print(f"🟢 Uploaded {name}.tif to Supabase: {public_url}")

    update_fields = {f"{name}_url": url for name, url in urls.items()}
    client.table("projects").update(update_fields).eq("id", project_id).execute()
    print("📡 Updated project with raster URLs.")

def wait_until_server_ready(url, timeout=60):
    print("⏳ Waiting for tile server to be ready...")
    for _ in range(timeout):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ Tile server is ready")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("❌ Tile server did not start in time")
    return False

def main():
    RESULTS_DIR = "05_results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

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

    # Reproject downloaded TIFFs to EPSG:3857 for web map use
    web_files = {}
    for name, path in files.items():
        web_path = path.replace(".tif", "_web.tif")
        reproject_to_web_mercator(path, web_path)
        web_files[name] = web_path

    # Fetch project_id from latest row
    client = get_supabase_client()
    response = client.table("projects").select("id").order("created_at", desc=True).limit(1).execute()
    project_id = response.data[0]["id"]

    upload_rasters_to_supabase(web_files, project_id)

    rasters = grid.load_and_check_rasters(files)

    patch_grid = grid.create_patch_grid(rasters["study_area"], grid_size=1000)
    valid_patches = grid.extract_patch_statistics(patch_grid, rasters)

    # Export valid patches for next step
    valid_path = os.path.join(args.output, "valid_patches.geojson")
    valid_patches.to_file(valid_path, driver="GeoJSON")
    print(f"📤 Saved valid patches to {valid_path}")

    # Run MCDA and export composite (automatically handled in mcda)
    composite, composite_norm, extent = mcda.compute_composite(rasters)



    print("✅ Preprocessing complete.")

    # ➕ Launch tile server temporarily for tiling and upload
    os.environ["PROJECT_ID"] = project_id
    process = subprocess.Popen(
    ["gunicorn", "app:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"],
    cwd="tile_server"
    )


    if wait_until_server_ready("http://localhost:8000/health"):
        response = requests.post("http://localhost:8000/run-tiling", json={"project_id": project_id})
        print(f"🔁 Response: {response.status_code} {response.reason}")
    else:
        print("🛑 Tiling skipped due to server startup failure")

    process.terminate()
    print("🛑 Tile server stopped")

    # Save valid_patches
    valid_patches.to_file(os.path.join(RESULTS_DIR, "valid_patches.geojson"), driver="GeoJSON")

    # Save composite_norm
    np.save(os.path.join(RESULTS_DIR, "composite_norm.npy"), composite_norm)

    # Ensure extent is float-serializable
    extent = {k: float(v) for k, v in extent.items()}

    # Save extent as JSON
    extent_dict = {
        "left": extent[2],
        "right": extent[3],
        "bottom": extent[0],
        "top": extent[1]
    }
    with open(os.path.join(RESULTS_DIR, "extent.json"), "w") as f:
        json.dump(extent_dict, f)


    print("📁 Saved preprocessing results to 05_results/")

if __name__ == "__main__":
    main()

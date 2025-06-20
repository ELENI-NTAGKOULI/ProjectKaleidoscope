import argparse
import os
import warnings
import gee_fetch, grid, mcda
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from utils import get_latest_coordinates, get_supabase_client

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
        client.storage.from_(bucket).upload_from_path(
            supabase_path,
            path,
            file_options={
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
    mcda.compute_composite(rasters)

    print("✅ Preprocessing complete.")

if __name__ == "__main__":
    main()

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
import os
import tempfile
import requests
from utils import get_supabase_client

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-tiling")
def run_tiling(req: Request):
    data = req.json()
    project_id = data.get("project_id")
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "project_id missing"})

    # Example: For each layer, fetch tif from Supabase and upload a single PNG tile (simplified)
    layers = ["floodRisk", "landcoverSuitability", "slope", "soil", "study_area", "urbanProximity"]
    supabase = get_supabase_client()
    bucket = "raster-exports"

    for layer in layers:
        url = f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/{bucket}/{project_id}/{layer}.tif"
        response = requests.get(url)
        with MemoryFile(response.content) as memfile:
            with memfile.open() as dataset:
                # Here you'd use rio_tiler to generate tiles and upload each tile to Supabase
                # Simulated example below (not actual tiling!)
                temp_path = f"/tmp/{layer}_sample.png"
                # e.g. use dataset.read(...) to save one tile
                # upload to Supabase in: f"{project_id}/tiles/{layer}/14/8571/5670.png"

                with open(temp_path, "wb") as f:
                    f.write(b"fake_png_tile_data")  # 👈 placeholder

                with open(temp_path, "rb") as f:
                    supabase.storage.from_("raster-exports").upload(
                        f"{project_id}/tiles/{layer}/14/8571/5670.png", f, {
                            "content-type": "image/png",
                            "x-upsert": "true"
                        }
                    )
                print(f"🟢 Uploaded tile for layer: {layer}")

    return {"status": "tiling complete"}

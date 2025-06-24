from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from utils import get_supabase_client
import os
import requests
from rio_tiler.io import COGReader
from mercantile import tiles
from tempfile import NamedTemporaryFile
from utils import tile_exists
from mercantile import bounds as tile_bounds

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-tiling")
async def run_tiling(request: Request):
    data = await request.json()
    project_id = data.get("project_id")
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "Missing project_id"})

    supabase = get_supabase_client()
    bucket = "tile-exports"

    # Τα layers που θες να κάνεις tiling
    layers = ["study_area", "urbanProximity", "slope", "soil", "landcoverSuitability", "floodRisk"]

    for layer in layers:
        print(f"\n🟡 Tiling {layer}...")

        tif_url = f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/{bucket}/{project_id}/{layer}.tif"
        print(f"📥 Fetching from: {tif_url}")
        
        tif_resp = requests.get(tif_url)
        print(f"📦 Response code: {tif_resp.status_code}")

        if tif_resp.status_code != 200:
            print(f"❌ Could not fetch {layer}.tif")
            continue

        with NamedTemporaryFile(suffix=".tif") as tmp:
            tmp.write(tif_resp.content)
            tmp.flush()
            print(f"📄 Saved temp .tif at {tmp.name}")

            try:
                with COGReader(tmp.name) as cog:
                    print(f"✅ Opened {layer}.tif as COG")
                    bounds = cog.bounds
                    min_zoom = 13
                    max_zoom = 14

                    for z in range(min_zoom, max_zoom + 1):
                        for tile in tiles(*bounds, z):
                            if not tile_exists(tile_bounds(tile.x, tile.y, tile.z), bounds):
                                continue

                            try:
                                img = cog.tile(tile.x, tile.y, tile.z)
                                data = img.render(img_format="PNG")
                                path = f"{project_id}/tiles/{layer}/{z}/{tile.x}/{tile.y}.png"
                                print(f"🧭 Uploading tile to: {path}")

                                supabase.storage.from_("tile-exports").upload(
                                    path,
                                    data,
                                    {"content-type": "image/png", "x-upsert": "true"}
                                )
                                print(f"✅ Uploaded tile {path}")
                            except Exception as e:
                                print(f"⚠️ Skipped tile z{z}/{tile.x}/{tile.y}: {e}")
            except Exception as e:
                print(f"❌ Could not open {layer}.tif with COGReader: {e}")

    return {"status": "tiling complete"}

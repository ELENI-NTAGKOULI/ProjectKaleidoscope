from flask import Flask, send_file, abort
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles
import os
from io import BytesIO

app = Flask(__name__)
DATA_FOLDER = "data"  # Or mount Supabase download path

@app.route("/tiles/<layer>/<int:z>/<int:x>/<int:y>.png")
def get_tile(layer, z, x, y):
    tif_path = os.path.join(DATA_FOLDER, f"{layer}.tif")

    if not os.path.exists(tif_path):
        abort(404, f"No such layer: {layer}")

    try:
        with Reader(tif_path) as src:
            tile_data, _ = src.tile(x, y, z)
            img = BytesIO()
            tile_data.save(img, format="PNG", **img_profiles["png"])
            img.seek(0)
            return send_file(img, mimetype="image/png")
    except Exception as e:
        abort(500, f"Tile rendering error: {e}")

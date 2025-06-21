from flask import Flask, send_file, abort
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles
import os
from io import BytesIO
import requests
from supabase import create_client
from dotenv import load_dotenv

# 🔹 Init
load_dotenv()
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# 🔹 Connect to Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔹 Get latest raster URLs from 'projects' table
response = client.table("projects").select("*").order("created_at", desc=True).limit(1).execute()
project = response.data[0]

# 🔹 Download the .tif files locally
for key, url in project.items():
    if key.endswith("_url"):
        layer = key.replace("_url", "")
        local_path = os.path.join(DATA_FOLDER, f"{layer}.tif")
        print(f"⬇️ Downloading {layer}.tif...")
        r = requests.get(url)
        with open(local_path, "wb") as f:
            f.write(r.content)
        print(f"✅ Saved {layer}.tif to {local_path}")

# 🔹 Create the Flask app
app = Flask(__name__)

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

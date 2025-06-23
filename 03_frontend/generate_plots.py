import os
import json
import pickle
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from plot_utils import plot_mcda_overlay, plot_2d_pareto_fronts
from supabase import create_client
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PROJECT_ID = os.getenv("PROJECT_ID") or "default_project"
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === CONFIG ===
RESULTS_DIR = "05_results"
EXPORT_DIR = "09_reports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# === LOAD DATA ===
print("🔹 Loading data from", RESULTS_DIR)

valid_patches_path = os.path.join(RESULTS_DIR, "valid_patches.geojson")
composite_path = os.path.join(RESULTS_DIR, "composite_norm.npy")
extent_path = os.path.join(RESULTS_DIR, "extent.json")
hof_path = os.path.join(RESULTS_DIR, "hof_all_runs.pkl")

valid_patches = gpd.read_file(valid_patches_path)
composite_norm = np.load(composite_path)
with open(extent_path) as f:
    extent_dict = json.load(f)
    extent = [extent_dict["left"], extent_dict["right"], extent_dict["bottom"], extent_dict["top"]]
with open(hof_path, "rb") as f:
    hof_all_runs = pickle.load(f)

# === GENERATE PLOTS ===
print("🖼️ Generating MCDA overlay plot...")
plot_mcda_overlay(
    composite_norm=composite_norm,
    extent=extent,
    selected_geometries = [valid_patches.geometry.iloc[p] for p in hof_all_runs[0]],
    patch_grid=valid_patches
)
mcda_path = os.path.join(EXPORT_DIR, "mcda_overlay.png")
plt.savefig(mcda_path, dpi=300)
plt.close()

print("🖼️ Generating 2D Pareto fronts plot...")
plot_2d_pareto_fronts(
    hof_all_runs=hof_all_runs,
    valid_patches=valid_patches,
    objective_cols=['landcoverSuitability', 'slope', 'soil', 'floodRisk', 'urbanProximity']
)
pareto_path = os.path.join(EXPORT_DIR, "pareto_fronts.png")
plt.savefig(pareto_path, dpi=300)
plt.close()

# === UPLOAD TO SUPABASE ===
def upload_file_to_supabase(path, remote_path, bucket="plots"):
    with open(path, "rb") as f:
        client.storage.from_(bucket).upload(remote_path, f, {"content-type": "image/png", "x-upsert": "true"})
    print(f"🟢 Uploaded {remote_path} to Supabase bucket '{bucket}'")

upload_file_to_supabase(mcda_path, f"{PROJECT_ID}/mcda_overlay.png")
upload_file_to_supabase(pareto_path, f"{PROJECT_ID}/pareto_fronts.png")

print("✅ All plots saved and uploaded to Supabase in", EXPORT_DIR)

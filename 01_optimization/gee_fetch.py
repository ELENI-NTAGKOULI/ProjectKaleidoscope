# gee_fetch.py
import ee
import os
import requests


def authenticate_gee():
    try:
        ee.Initialize()
        print("✅ GEE already authenticated")
    except Exception:
        print("🔐 Authenticating Google Earth Engine...")
        ee.Authenticate()
        ee.Initialize()
        print("✅ GEE authenticated")


def create_study_region(center_lon, center_lat, buffer_km=10):
    point = ee.Geometry.Point([center_lon, center_lat])
    region = (point
              .transform('EPSG:32630', 1)
              .buffer(buffer_km * 1000)
              .bounds()
              .transform('EPSG:4326', 1))
    return region


def download_gee_data(region, output_folder='gee_data'):
    os.makedirs(output_folder, exist_ok=True)
    print("📡 Downloading GEE layers to:", output_folder)
    proj30 = ee.Projection('EPSG:32630').atScale(30)
    layers = {}

    study_area = ee.Image.constant(1).clip(region).rename('study_area')
    layers['study_area'] = study_area.reproject(crs=proj30, scale=30)

    # Add all GEE layers below (floodRisk, slope, soil, landcoverSuitability, urbanProximity)
    # For brevity, demo includes only one
    flood = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v1").select('depth').max().clip(region)
    stats = flood.reduceRegion(ee.Reducer.max(), region, 30, 1e13)
    region_max = ee.Number(stats.get('depth')).max(1)
    flood_norm = flood.divide(region_max).rename('floodRisk')
    layers['floodRisk'] = flood_norm.reproject(crs=proj30, scale=30)

    region_geojson = region.getInfo()
    downloaded = {}

    for name, img in layers.items():
        print(f"   Downloading {name}...")
        url = img.getDownloadURL({
            'region': region_geojson,
            'scale': 30,
            'crs': 'EPSG:32630',
            'format': 'GEO_TIFF'
        })
        resp = requests.get(url)
        if resp.status_code == 200:
            path = os.path.join(output_folder, f"{name}.tif")
            with open(path, 'wb') as f:
                f.write(resp.content)
            downloaded[name] = path
            print(f"   ✅ {name} saved to {path}")
        else:
            print(f"   ❌ Failed {name} ({resp.status_code})")

    return downloaded, region_geojson


def setup_data_automatically(center_lon, center_lat, buffer_km=10, output_folder='gee_data'):
    authenticate_gee()
    region = create_study_region(center_lon, center_lat, buffer_km)
    files, region_geojson = download_gee_data(region, output_folder)
    return files, region_geojson

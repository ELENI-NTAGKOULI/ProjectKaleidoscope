# gee_fetch.py
import ee
import os
import json
import requests

def authenticate_gee():
    try:
        service_account = 'gee-runner@gee-runner.iam.gserviceaccount.com'
        
        # Load service account JSON from environment variable
        credentials_json = os.environ.get('GCP_SERVICE_ACCOUNT')
        if not credentials_json:
            raise Exception("Missing GCP_SERVICE_ACCOUNT environment variable")

        credentials_dict = json.loads(credentials_json)
        credentials = ee.ServiceAccountCredentials(service_account, None, credentials_dict)

        ee.Initialize(credentials)
        print("✅ GEE authenticated using service account")

    except Exception as e:
        print("❌ Failed to authenticate GEE:", e)
        raise

def create_study_region(center_lon, center_lat, buffer_km=10):
    point = ee.Geometry.Point([center_lon, center_lat])
    utm_proj = ee.Projection('EPSG:32630')
    region = (
        point
        .transform(utm_proj, 1)
        .buffer(buffer_km * 1000)
        .bounds()
        .transform('EPSG:4326', 1)
    )
    return region

def download_gee_data(region, output_folder='gee_data'):
    os.makedirs(output_folder, exist_ok=True)
    print("📡 Downloading GEE layers to:", output_folder)
    layers = {}

    # Projection string to use ONLY for getDownloadURL (not for .reproject)
    crs_str = 'EPSG:32630'

    # Study area mask
    study_area = ee.Image.constant(1).clip(region).rename('study_area')
    layers['study_area'] = study_area

    # Urban proximity
    urban_mask = ee.Image("DLR/WSF/WSF2015/v1").select('WSF').clip(region).gt(0).rename('urban')
    wsf = ee.Image("DLR/WSF/WSF2015/v1").select('WSF').gt(0).selfMask()
    dist = wsf.fastDistanceTransform(256, 'pixels', 'squared_euclidean') \
              .sqrt().multiply(30).clip(region)
    norm_dist = dist.min(2500).divide(2500)
    urban_proximity = norm_dist.multiply(-1).add(1).unmask(0).rename('urbanProximity')
    urban_proximity = urban_proximity.where(urban_mask.eq(1), 0)
    layers['urbanProximity'] = urban_proximity

    # Slope (inverted flat=1, steep=0)
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30").filterBounds(region).mosaic().select('DEM').clip(region)
    slope = ee.Terrain.slope(dem).unitScale(0, 60)
    slope_inv = ee.Image(1).subtract(slope).unmask(1).rename('slope')
    layers['slope'] = slope_inv

    # Soil
    def remap_soil(img):
        return img.remap(
            [1,2,3,4,5,6,7,8,9,10,11,12],
            [0.3,0.2,0.2,0.7,0.6,0.6,1.0,0.9,0.8,0.6,0.4,0.1],
            0
        )
    soil0 = remap_soil(ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02").select('b0').clip(region))
    soil30 = remap_soil(ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02").select('b30').clip(region))
    soil = soil0.add(soil30).divide(2).unmask(0).rename('soil')
    layers['soil'] = soil

    # Landcover suitability
    lc = ee.Image("COPERNICUS/CORINE/V20/100m/2018").select('landcover').clip(region)
    lc_suit = lc.remap(
        [111,112,121,122,131,141,211,212,221,231,242,243,311,312,313,321,322,324,331,511,523],
        [0.0,0.1,0.0,0.0,0.2,0.4,0.7,0.6,0.5,0.8,0.6,0.8,0.0,0.0,0.0,0.8,0.6,0.5,0.1,0.0,0.0],
        0
    ).unmask(0).rename('landcoverSuitability')
    layers['landcoverSuitability'] = lc_suit

    # Flood risk (normalized)
    flood = ee.ImageCollection("JRC/CEMS_GLOFAS/FloodHazard/v1").select('depth').max().clip(region).unmask(0)
    stats = flood.reduceRegion(ee.Reducer.max(), region, 30, maxPixels=1e13)
    max_depth = ee.Number(stats.get('depth')).max(1)
    flood_norm = flood.divide(max_depth).rename('floodRisk')
    layers['floodRisk'] = flood_norm

    # Download layers
    region_geojson = region.getInfo()
    downloaded = {}

    for name, img in layers.items():
        print(f"   Downloading {name}...")
        try:
            url = img.getDownloadURL({
                'region': region_geojson,
                'scale': 30,
                'crs': crs_str,
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
        except Exception as e:
            print(f"   ❌ Error downloading {name}: {e}")

    return downloaded, region_geojson

def setup_data_automatically(center_lon, center_lat, buffer_km=10, output_folder='gee_data'):
    authenticate_gee()
    region = create_study_region(center_lon, center_lat, buffer_km)
    files, region_geojson = download_gee_data(region, output_folder)
    return files, region_geojson

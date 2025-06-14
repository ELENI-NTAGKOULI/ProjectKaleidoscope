# grid.py
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
from shapely.geometry import box

def load_and_check_rasters(file_paths):
    rasters = {}
    print("\n🗺️ Loading rasters:")
    for name, path in file_paths.items():
        try:
            src = rasterio.open(path)
            rasters[name] = src
            arr = src.read(1).astype(float)
            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan
            print(f"✓ {name}: shape={src.shape}, CRS={src.crs}, min={np.nanmin(arr):.3f}, max={np.nanmax(arr):.3f}")
        except Exception as e:
            print(f"✗ {name}: failed to load ({e})")
    return rasters

def create_patch_grid(raster, grid_size):
    left, bottom, right, top = raster.bounds
    cols = max(1, int((right - left) / grid_size))
    rows = max(1, int((top - bottom) / grid_size))

    patches = []
    for row in range(rows):
        for col in range(cols):
            patch_left = left + col * grid_size
            patch_bottom = bottom + (rows - row - 1) * grid_size
            patch_right = patch_left + grid_size
            patch_top = patch_bottom + grid_size
            poly = box(patch_left, patch_bottom, patch_right, patch_top)
            centroid = poly.centroid
            patches.append({
                'id': row * cols + col,
                'geometry': poly,
                'centroid_x': centroid.x,
                'centroid_y': centroid.y,
                'row': row,
                'col': col
            })

    gdf = gpd.GeoDataFrame(patches, geometry='geometry', crs=raster.crs)
    print(f"Created {len(gdf)} patches in grid")
    return gdf

def extract_patch_statistics(patch_grid, rasters):
    for name in rasters:
        patch_grid[name] = np.nan

    for idx, patch in patch_grid.iterrows():
        geom = [patch.geometry]
        for name, raster in rasters.items():
            try:
                out_image, _ = mask(raster, geom, crop=True)
                data = out_image[0]
                if raster.nodata is not None:
                    data = data[data != raster.nodata]
                if len(data) > 0:
                    patch_grid.at[idx, name] = data.mean()
            except Exception:
                patch_grid.at[idx, name] = np.nan

    filtered = patch_grid.dropna(subset=list(rasters.keys()))
    print(f"Extracted stats: {len(filtered)} valid patches / {len(patch_grid)} total")
    return filtered

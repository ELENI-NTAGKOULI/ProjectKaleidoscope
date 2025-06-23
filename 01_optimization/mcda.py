# mcda.py
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from rasterio.transform import array_bounds


def compute_composite(rasters, layer_names=None, weights=None):
    if layer_names is None:
        layer_names = ['slope', 'landcoverSuitability', 'soil', 'urbanProximity', 'floodRisk']
    if weights is None:
        raw_weights = np.array([1, 1, 1, 1, 2], dtype=float)  # floodRisk gets double weight
        weights = raw_weights / raw_weights.sum()

    print("\n🧮 Running MCDA with layers:", layer_names)
    print("Weights:", dict(zip(layer_names, weights)))

    normalized_layers = []
    for name in layer_names:
        src = rasters[name]
        arr = src.read(1).astype(float)
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        flat = arr.flatten()
        valid = ~np.isnan(flat)
        scaled = np.full(flat.shape, np.nan)
        if valid.any():
            scaler = MinMaxScaler()
            scaled[valid] = scaler.fit_transform(flat[valid].reshape(-1, 1)).flatten()
        norm_arr = scaled.reshape(arr.shape)
        normalized_layers.append(norm_arr)

    stack = np.stack(normalized_layers)
    composite = np.zeros_like(stack[0], dtype=float)
    for i, layer in enumerate(stack):
        composite += weights[i] * np.nan_to_num(layer, nan=0)

    if 'study_area' in rasters:
        mask_arr = rasters['study_area'].read(1)
        nodata_val = rasters['study_area'].nodata
        composite = np.where(mask_arr != nodata_val, composite, np.nan)

    composite_norm = (composite - np.nanmin(composite)) / (np.nanmax(composite) - np.nanmin(composite))
    print("✅ Composite suitability map computed")

    # Calculate extent properly
    height, width = composite_norm.shape
    transform = rasters[layer_names[0]].transform
    bounds = array_bounds(height, width, transform)
    extent = {
        "minx": float(bounds[0]),
        "miny": float(bounds[1]),
        "maxx": float(bounds[2]),
        "maxy": float(bounds[3])
    }

    return composite, composite_norm, extent
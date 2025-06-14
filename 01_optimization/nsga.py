# nsga.py
from deap import base, creator, tools
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import random
from scipy.spatial.distance import cdist
import pandas as pd

# NSGA parameters
def run_nsga_pipeline(valid_patches, pop_size=100, generations=20, num_runs=5, min_distance=1000, num_to_select=5):
    print("\n🤖 Running NSGA-II optimization")

    objective_cols = ['landcoverSuitability', 'slope', 'soil', 'floodRisk', 'urbanProximity']
    scaler = MinMaxScaler()
    valid_patches[objective_cols] = scaler.fit_transform(valid_patches[objective_cols])

    creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0, 1.0, 3.0, 1.0))
    creator.create("Individual", list, fitness=creator.FitnessMulti)
    toolbox = base.Toolbox()
    toolbox.register("indices", random.randint, 0, len(valid_patches) - 1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.indices, n=1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind, data):
        idx = ind[0]
        row = data.iloc[idx]
        return tuple(row[col] for col in objective_cols)

    toolbox.register("evaluate", evaluate, data=valid_patches)
    toolbox.register("mate", lambda ind1, ind2: (creator.Individual([ind2[0]]), creator.Individual([ind1[0]])))
    toolbox.register("mutate", lambda ind: (creator.Individual([random.randint(0, len(valid_patches) - 1)]),))
    toolbox.register("select", tools.selNSGA2)

    all_selected = []
    for run in range(num_runs):
        print(f"\n▶ Run {run+1} of {num_runs}")
        pop = toolbox.population(n=pop_size)
        for ind in pop:
            ind.fitness.values = toolbox.evaluate(ind)
        for gen in range(generations):
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))
            for i in range(1, len(offspring), 2):
                if random.random() < 0.7:
                    offspring[i - 1], offspring[i] = toolbox.mate(offspring[i - 1], offspring[i])
                    del offspring[i - 1].fitness.values, offspring[i].fitness.values
            for i in range(len(offspring)):
                if random.random() < 0.3:
                    offspring[i], = toolbox.mutate(offspring[i])
                    del offspring[i].fitness.values
            invalid = [ind for ind in offspring if not ind.fitness.valid]
            for ind in invalid:
                ind.fitness.values = toolbox.evaluate(ind)
            pop[:] = offspring

        selected = select_spatially_distributed(pop, valid_patches, min_distance, num_to_select)
        all_selected.extend(selected)

    results = summarize_results(all_selected, valid_patches)
    return results, all_selected


def select_spatially_distributed(pop, df, min_dist, n):
    seen = {}
    for ind in pop:
        seen[ind[0]] = ind
    candidates = list(seen.values())
    candidates = [c for c in candidates if c.fitness.valid]
    candidates.sort(key=lambda x: sum(x.fitness.values), reverse=True)

    selected, centroids = [], []
    for c in candidates:
        if len(selected) >= n:
            break
        idx = c[0]
        pt = np.array([[df.iloc[idx]['centroid_x'], df.iloc[idx]['centroid_y']]])
        if not centroids or cdist(pt, np.array(centroids)).min() >= min_dist:
            selected.append(c)
            centroids.append(pt[0])
    print(f"✅ Selected {len(selected)} spatial patches")
    return selected


def summarize_results(selected, df):
    records = []
    for rank, ind in enumerate(selected):
        idx = ind[0]
        row = df.iloc[idx]
        records.append({
            'rank': rank + 1,
            'patch_id': idx,
            'centroid_x': row['centroid_x'],
            'centroid_y': row['centroid_y'],
            'score': sum(ind.fitness.values),
            **{col: row[col] for col in ['slope', 'soil', 'floodRisk', 'urbanProximity', 'landcoverSuitability']}
        })
    return pd.DataFrame(records)
def create_results_dataframe(selected_patches, patch_data):
    import pandas as pd
    import geopandas as gpd

    results = []

    for i, patch in enumerate(selected_patches):
        # ✅ Robust patch index extraction
        try:
            if hasattr(patch, "fitness") and isinstance(patch[0], int):
                idx = patch[0]  # DEAP individual
            elif isinstance(patch, int):
                idx = patch
            elif isinstance(patch, pd.Series) and 'patch_id' in patch:
                idx = int(patch['patch_id'])
            else:
                raise ValueError(f"Unrecognized patch format at index {i}: {type(patch)}")
        except Exception as e:
            print(f"⚠️ Skipping patch {i}: couldn't extract index - {e}")
            continue

        try:
            patch_row = patch_data.iloc[idx]
            geom = patch_row.geometry
            minx, miny, maxx, maxy = geom.bounds

            # Convert to UTM if needed
            if patch_data.crs != 'EPSG:25831':
                patch_gdf = gpd.GeoDataFrame([patch_row], geometry='geometry', crs=patch_data.crs)
                patch_gdf = patch_gdf.to_crs('EPSG:25831')
                geom_utm = patch_gdf.geometry.iloc[0]
                minx, miny, maxx, maxy = geom_utm.bounds
                centroid = geom_utm.centroid
            else:
                centroid = geom.centroid

            results.append({
                'rank': i + 1,
                'patch_id': idx,
                'centroid_longitude': patch_row['centroid_x'],
                'centroid_latitude': patch_row['centroid_y'],
                'centroid_x_utm31n': centroid.x,
                'centroid_y_utm31n': centroid.y,
                'bbox_coordinates_utm31n': f"{minx:.2f},{miny:.2f},{maxx:.2f},{maxy:.2f}",
                'landcoverSuitability': patch_row.get('landcoverSuitability', 0),
                'slope': patch_row.get('slope', 0),
                'soil': patch_row.get('soil', 0),
                'floodRisk': patch_row.get('floodRisk', 0),
                'urbanProximity': patch_row.get('urbanProximity', 0),
                'overall_score': sum(patch.fitness.values) if hasattr(patch, 'fitness') else 0
            })
        except Exception as e:
            print(f"⚠️ Failed to process patch {idx}: {e}")
            continue

    return pd.DataFrame(results)



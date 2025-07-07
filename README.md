# BeaversTank
Welcome to beaversTank - Our playground for building cities that stay dry and happy. We’re Marcos, Lena, Yashashvi & Samarth four students from the Masters in AI for Architecture & Built Environment (IAAC, Barcelona), and we’ve teamed up to tackle floods the way real beavers do: with brains and a bit of cheeky engineering.

Inside this repo you’ll find two AI sidekicks working together. One (NSGA optimizer) sketches out smart layouts - think ponds, ridges and green sponge zones - while the other (a reinforcement-learning agent) learns when to open gates or fire up pumps as storms roll in. Grab the notebooks, run the demo, and help us keep the water where it belongs: out of the living room and in the scenery. 🦫

## 🛠️ System Architecture
1. **Data Acquisition**: Remote sensing with Google Earth Engine over 20x20 km areas.
2. **MCDA**: Multi-criteria decision-making based on land use, slope, soil, etc.
3. **Optimization**: NSGA-II for balancing hydrological, ecological, and feasibility goals.
4. **Simulation**: Agent-Based Modeling + PPO (RL) to simulate afforestation impact.

## 📊 Outputs
- Suitability maps and Pareto fronts
- Water flow simulations (pre/post intervention)
- Performance dashboards and detailed reports

## 🧪 Technologies
- `Google Earth Engine (GEE)`
- `NSGA-II`, `Reinforcement Learning (PPO)`
- `Agent-Based Modeling`
- `Geospatial libraries`: `geopandas`, `rasterio`, `shapely`, etc.

## 🔍 Purpose
To assist policymakers and researchers in the pre-disaster planning stage—turning high-dimensional data into actionable flood mitigation strategies.


## 📦 Project Structure

```bash
BeaversTank/
├── 01_optimization/            # GEE data fetch, MCDA, NSGA-II patch optimization
├── 02_simulation/              # Mesa-based flood simulation with/without NBS
├── 03_frontend/                # Interactive maps, charts, UI (Leaflet, Streamlit, etc.)
├── 04_data/                    # Input data: DEM, rivers, GEE layers, etc.
├── 05_results/                 # Output patches, plots, and exported analysis
├── 06_reports/                 # Final compiled reports
├── 07_scripts/                 # CLI tools to run pipeline or launch dashboard
├── 08_notebooks/               # Jupyter exploration & testing (if so)
├── config.yaml              # Central config for weights, parameters, paths
├── requirements.txt         # Project dependencies
├── .gitignore               # Files/folders to exclude from Git
└── README.md                # You're here :)



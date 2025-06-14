# BeaversTank
Welcome to beaversTank - Our playground for building cities that stay dry and happy. We’re Marcos, Lena, Yashashvi & Samarth four students from the Masters in AI for Architecture & Built Environment (IAAC, Barcelona), and we’ve teamed up to tackle floods the way real beavers do: with brains and a bit of cheeky engineering.

Inside this repo you’ll find two AI sidekicks working together. One (NSGA optimizer) sketches out smart layouts - think ponds, ridges and green sponge zones - while the other (a reinforcement-learning agent) learns when to open gates or fire up pumps as storms roll in. Grab the notebooks, run the demo, and help us keep the water where it belongs: out of the living room and in the scenery. 🦫

## 📦 Project Structure

```bash
BeaversTank/
├── optimization/            # GEE data fetch, MCDA, NSGA-II patch optimization
├── simulation/              # Mesa-based flood simulation with/without NBS
├── frontend/                # Interactive maps, charts, UI (Leaflet, Streamlit, etc.)
├── data/                    # Input data: DEM, rivers, GEE layers, etc.
├── results/                 # Output patches, plots, and exported analysis
├── reports/                 # 
├── scripts/                 # CLI tools to run pipeline or launch dashboard
├── notebooks/               # (Optional) Jupyter exploration & testing
├── config.yaml              # Central config for weights, parameters, paths
├── requirements.txt         # Project dependencies
├── .gitignore               # Files/folders to exclude from Git
└── README.md                # You're here!
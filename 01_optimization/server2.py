import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/run-preprocessing", methods=["POST"])
def run_preprocessing():
    try:
        subprocess.run(["python", "01_optimization/main1.py"], check=True)
        return jsonify({"status": "success", "message": "Preprocessing complete"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Preprocessing failed: {e}"}), 500

@app.route("/run-optimization", methods=["POST"])
def run_optimization():
    try:
        subprocess.run(["python", "01_optimization/main2.py"], check=True)
        return jsonify({"status": "success", "message": "Optimization complete"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Optimization failed: {e}"}), 500

@app.route("/generate-plots", methods=["POST"])
def generate_plots():
    try:
        subprocess.run(["python", "03_frontend/generate_plots.py"], check=True)
        return jsonify({"status": "success", "message": "Plots generated and uploaded to Supabase"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Plot generation failed: {e}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

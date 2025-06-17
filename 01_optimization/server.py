import os
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/trigger", methods=["POST"])
def trigger_pipeline():
    try:
        # Τρέξε το optimization script
        subprocess.run(["python", "01_optimization/main.py"], check=True)
        return jsonify({"status": "success", "message": "Optimization started"}), 200
    except subprocess.CalledProcessError:
        return jsonify({"status": "error", "message": "Execution failed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

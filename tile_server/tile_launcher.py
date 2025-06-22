import subprocess
import time
import requests
import os


def start_tile_server():
    process = subprocess.Popen(
        [
            "gunicorn",
            "app:app",
            "-k", "uvicorn.workers.UvicornWorker",  # 👈 Χρήση ASGI worker για FastAPI
            "--bind", "0.0.0.0:8000"
        ],
        cwd="tile_server"  # 👈 Εκτέλεση μέσα στον φάκελο tile_server
    )
    print("🟢 Tile server started on port 8000")
    return process

def wait_for_tile_server(timeout=80):
    for _ in range(timeout):
        try:
            r = requests.get("http://localhost:8000/health")
            if r.status_code == 200:
                print("✅ Tile server is ready")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("❌ Tile server did not start in time")
    return False

def stop_tile_server(process):
    print("🛑 Stopping tile server...")
    process.terminate()
    process.wait()

if __name__ == "__main__":
    p = start_tile_server()
    try:
        if wait_for_tile_server():
            project_id = os.environ.get("PROJECT_ID")
            if not project_id:
                raise ValueError("PROJECT_ID not set")
            print(f"📡 Triggering tiling for project {project_id}")
            response = requests.post("http://localhost:8000/run-tiling", json={"project_id": project_id})
            print("🔁 Response:", response.status_code, response.text)
            time.sleep(2)
    finally:
        stop_tile_server(p)

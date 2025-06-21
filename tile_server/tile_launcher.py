import subprocess
import time
import requests

def start_tile_server():
    # Εκκίνηση tile server ως subprocess
    process = subprocess.Popen(
        ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"],
        cwd="tile_server"
    )
    print("Tile server started on port 8000")
    return process

def wait_for_tile_server(timeout=15):
    # Περιμένει να ξεκινήσει σωστά ο server
    for _ in range(timeout):
        try:
            r = requests.get("http://localhost:8000/health")
            if r.status_code == 200:
                print("Tile server is ready")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Tile server did not start in time")
    return False

def stop_tile_server(process):
    print("Stopping tile server...")
    process.terminate()
    process.wait()

if __name__ == "__main__":
    p = start_tile_server()
    try:
        if wait_for_tile_server():
            print("You can now fetch tiles.")
            time.sleep(20)  # ή οποιαδήποτε λογική για να περιμένει το tiling
    finally:
        stop_tile_server(p)

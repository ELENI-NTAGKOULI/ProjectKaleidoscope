# tile_server/app.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/health")
def health():
    return JSONResponse(content={"status": "ok"})


# Παράδειγμα endpoint για tiles (τροποποίησε ανάλογα με τα δικά σου δεδομένα)
@app.get("/tiles/{z}/{x}/{y}.png")
def get_tile(z: int, x: int, y: int):
    # Προσάρμοσε με την πραγματική σου tile-serving λογική
    return JSONResponse(content={"tile": f"{z}/{x}/{y}"})

FROM python:3.12-slim

# Εγκαθιστούμε τις system βιβλιοθήκες που χρειάζονται τα rasterio/gdal
RUN apt-get update && apt-get install -y \
    libexpat1 gdal-bin libgl1-mesa-glx pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Φτιάχνουμε venv και εγκαθιστούμε Python dependencies
WORKDIR /app
COPY . .
RUN python -m venv /opt/venv \
 && . /opt/venv/bin/activate \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

# Εξάγουμε το port (για Railway)
ENV PORT=8080
EXPOSE $PORT

# Εκτελούμε τον Gunicorn από το tile_server φάκελο
CMD ["/opt/venv/bin/gunicorn", "app:app", "--chdir", "tile_server", "--bind", "0.0.0.0:8080"]

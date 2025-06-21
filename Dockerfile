FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libexpat1 gdal-bin libgl1-mesa-glx pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8080

CMD ["python", "01_optimization/server2.py"]

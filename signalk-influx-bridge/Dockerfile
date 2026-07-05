FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY signalk_influx_bridge ./signalk_influx_bridge

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "signalk_influx_bridge.bridge"]

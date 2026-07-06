FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY signalk_polar_performance ./signalk_polar_performance

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "signalk_polar_performance.performance"]

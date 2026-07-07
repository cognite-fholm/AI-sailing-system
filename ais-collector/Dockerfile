FROM python:3.12-slim-bookworm

WORKDIR /app
COPY ais-collector/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ais-collector/ais_collector/ ais_collector/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "ais_collector.collector"]

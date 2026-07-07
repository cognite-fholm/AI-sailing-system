FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY race-live-sync/requirements.txt ./race-live-sync-requirements.txt
COPY live-results/requirements.txt ./live-results-requirements.txt
COPY fleet-performance-tracker/requirements.txt ./fpt-requirements.txt
RUN pip install --no-cache-dir \
    -r race-live-sync-requirements.txt \
    -r live-results-requirements.txt \
    -r fpt-requirements.txt

COPY race-live-sync/race_live_sync/ race_live_sync/
COPY live-results/live_results/ live_results/
COPY fleet-performance-tracker/fleet_performance_tracker/ fleet_performance_tracker/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "race_live_sync.sync"]

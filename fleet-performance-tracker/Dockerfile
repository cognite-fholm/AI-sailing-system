FROM python:3.12-slim-bookworm

WORKDIR /app

COPY fleet-performance-tracker/requirements.txt ./fpt-requirements.txt
COPY live-results/requirements.txt ./live-results-requirements.txt
RUN pip install --no-cache-dir -r fpt-requirements.txt -r live-results-requirements.txt

COPY fleet-performance-tracker/fleet_performance_tracker/ fleet_performance_tracker/
COPY live-results/live_results/ live_results/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "fleet_performance_tracker.sync"]

FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY race_lifecycle/ race_lifecycle/
COPY scripts/sync_active_context.py scripts/sync_active_context.py

ENV PYTHONUNBUFFERED=1
ENV RACE_LIFECYCLE_STATE=/var/run/ai-sailing/race-lifecycle.json
CMD ["python", "-m", "race_lifecycle.sync"]

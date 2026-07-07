FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY race_live_sync/ race_live_sync/

ENV PYTHONUNBUFFERED=1
# GITHUB_TOKEN injected at runtime — never at build time
CMD ["python", "-m", "race_live_sync.sync"]

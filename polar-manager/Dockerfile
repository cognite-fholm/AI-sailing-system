FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY polar_manager ./polar_manager

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "polar_manager.api"]

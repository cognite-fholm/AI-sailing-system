FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY course_sk_sync ./course_sk_sync

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "course_sk_sync.sync"]

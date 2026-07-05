FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY race_import ./race_import

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "race_import.api"]

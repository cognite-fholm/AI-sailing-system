FROM python:3.12-slim-bookworm

WORKDIR /app
COPY grib-model-scorer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY grib-model-scorer/grib_model_scorer/ grib_model_scorer/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "grib_model_scorer.scorer"]

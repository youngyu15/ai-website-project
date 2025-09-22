FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and mount model at /models via a volume or bind
COPY app ./app

EXPOSE 8001
ENV MODEL_PATH=/models/catdog_savedmodel
ENV IMG_SIZE=128
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--no-server-header"]

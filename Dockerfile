FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/memory_db && chmod -R 777 /app/memory_db

EXPOSE 10000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]

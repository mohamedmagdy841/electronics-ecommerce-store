FROM python:3.12.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN mkdir -p db /app/mediafiles

RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    libjpeg-dev \
    zlib1g-dev \

    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

LABEL org.opencontainers.image.source="https://github.com/mohamedmagdy841/electronics-ecommerce-store"
LABEL org.opencontainers.image.description="Electronics e-commerce Django backend"

ENTRYPOINT ["/app/entrypoint.sh"]

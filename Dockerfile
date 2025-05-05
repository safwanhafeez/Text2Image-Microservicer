FROM python:3.9-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p images include

COPY . .

EXPOSE 50051
EXPOSE 8501

CMD ["bash", "start.sh"]
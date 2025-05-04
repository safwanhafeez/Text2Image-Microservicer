FROM python:3.9-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support (adjust version as needed)
RUN pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create an image directory if it doesn't exist
RUN mkdir -p images

# Default command - will be overridden in docker-compose
CMD ["python", "app.py"]
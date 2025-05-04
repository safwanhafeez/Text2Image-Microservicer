#!/bin/bash

# Copy modified files to replace originals
echo "Copying modified files..."
cp -f modified_app.py app.py
cp -f modified_grpc_server.py include/grpc_server.py

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose could not be found. Please install Docker Compose first."
    exit 1
fi

# Check if NVIDIA Container Toolkit is installed
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: NVIDIA utilities not found. GPU acceleration may not work."
    echo "Consider installing the NVIDIA Container Toolkit for GPU support."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Services started!"
echo "Access the Streamlit application at http://localhost:8501"
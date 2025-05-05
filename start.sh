#!/bin/bash

# Start gRPC server in the background
python include/grpc_server.py &
GRPC_PID=$!

# Wait for gRPC server to start (check if port 50051 is open)
echo "Waiting for gRPC server to start..."
while ! nc -z localhost 50051; do
  sleep 0.5
done

echo "gRPC server is up. Starting Streamlit app..."
streamlit run app.py

# Optionally wait on the gRPC server process if needed
wait $GRPC_PID

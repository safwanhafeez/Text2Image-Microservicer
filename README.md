# Text to Image Generator

A Streamlit application with gRPC backend that generates images from text prompts using Stable Diffusion.

## Features

- Text to Image generation
- Image to Image transformation
- Freehand drawing with transformation
- Multiple style options

## Project Structure

```
.
├── app.py                # Streamlit frontend
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Multi-container orchestration
├── images/               # Generated images storage
├── include/              # Backend code and protobuf definitions
│   ├── grpc_server.py    # gRPC server implementation
│   ├── text2image_pb2.py # Generated protobuf code
│   └── text2image.proto  # Protobuf definitions
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Prerequisites

For local development:
- Python 3.9+
- PyTorch with CUDA support
- NVIDIA GPU with CUDA support

For Docker deployment:
- Docker and Docker Compose
- NVIDIA Container Toolkit (for GPU support)

## Deployment with Docker

1. Make sure you have Docker and Docker Compose installed.

2. Ensure NVIDIA Container Toolkit is installed for GPU support:
   ```bash
   # Install NVIDIA Container Toolkit
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

3. Clone this repository and navigate to the project directory.

4. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```

5. Access the Streamlit application at http://localhost:8501

## Manual Deployment

1. Clone the repository and navigate to the project directory.

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Start the gRPC server:
   ```bash
   python include/grpc_server.py
   ```

4. In a separate terminal, start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

5. Access the Streamlit application at http://localhost:8501

## Configuration

You can modify the following environment variables in the `docker-compose.yml`:

- `CUDA_VISIBLE_DEVICES`: Specify which GPU to use
- `GRPC_SERVER_ADDRESS`: Address of the gRPC server (default: grpc-server)

## Troubleshooting

### Connection Issues
If the Streamlit app can't connect to the gRPC server, check:
1. The gRPC server is running
2. Ports are not blocked by firewall
3. In Docker, the service names match what's in the docker-compose.yml

### GPU Issues
If you encounter GPU memory errors:
1. Reduce the image dimensions
2. Use a smaller model
3. Ensure your GPU has enough VRAM for Stable Diffusion (minimum 6GB)

## License

[MIT License](LICENSE)
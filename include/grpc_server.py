import grpc
from concurrent import futures
import base64
import io
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline
import datetime
import os
import sys

# Add the current directory to the path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import text2image_pb2
import text2image_pb2_grpc

# Load the Stable Diffusion pipeline
pipe = StableDiffusionPipeline.from_pretrained(
    "SG161222/Realistic_Vision_V5.1_noVAE",
    torch_dtype=torch.float32,
    use_safetensors=True,
).to("cuda")

# Define the gRPC service implementation
class Text2ImageServicer(text2image_pb2_grpc.Text2ImageServicer):
    def GenerateImage(self, request, context):
        prompt = request.prompt
        ctx = request.context
        height = request.height or 512  # default if 0
        width = request.width or 512

        full_prompt = f"{prompt}. Context: {ctx}" if ctx else prompt

        try:
            print(f"Generating image for prompt: {full_prompt}")
            image = pipe(full_prompt, height=height, width=width).images[0]

            # Resize image to requested dimensions
            image = image.resize((width, height), Image.ANTIALIAS)

            # Create images directory if it doesn't exist
            # Get the path relative to the script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(script_dir, "..", "images")
            
            # Create the directory if it doesn't exist
            os.makedirs(images_dir, exist_ok=True)
            
            # Save image locally with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(images_dir, f"generated_image_{timestamp}.png")
            image.save(filename)
            print(f"Image saved locally as: {filename}")

            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            return text2image_pb2.ImageResponse(
                image_base64=image_base64,
                status="success"
            )
        except Exception as e:
            print(f"Error during image generation: {e}")
            return text2image_pb2.ImageResponse(
                image_base64="",
                status=f"error: {str(e)}"
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    text2image_pb2_grpc.add_Text2ImageServicer_to_server(Text2ImageServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server started on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
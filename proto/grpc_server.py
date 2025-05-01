import grpc
from concurrent import futures
import base64
import io
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline
import datetime

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
        full_prompt = f"{prompt}. Context: {ctx}" if ctx else prompt

        try:
            print(f"Generating image for prompt: {full_prompt}")
            image = pipe(full_prompt).images[0]

            # Save image locally with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"images/generated_image_{timestamp}.png"
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

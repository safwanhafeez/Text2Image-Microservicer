import grpc
from concurrent import futures
import base64
import io
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
import datetime
import os
import sys
import text2image_pb2
import text2image_pb2_grpc

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set model ID
MODEL_ID = "SG161222/Realistic_Vision_V5.1_noVAE"

# Use float16 to reduce VRAM usage
TORCH_DTYPE = torch.float32

# Load the base pipeline (text-to-image) once at start
print("Loading text-to-image pipeline...")
pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=TORCH_DTYPE,
    use_safetensors=True
).to("cuda")
pipe.enable_attention_slicing()
pipe.safety_checker = None  # Optional: skip safety checker to save memory

# gRPC Service Implementation
class Text2ImageServicer(text2image_pb2_grpc.Text2ImageServicer):
    def GenerateImage(self, request, context):
        prompt = request.prompt
        ctx = request.context
        height = request.height or 512
        width = request.width or 512

        full_prompt = f"{prompt}. Context: {ctx}" if ctx else prompt

        try:
            print(f"[Text2Image] Prompt: {full_prompt}")
            image = pipe(full_prompt, height=height, width=width).images[0]

            return self._prepare_response(image, width, height)

        except Exception as e:
            print(f"Error in text-to-image: {e}")
            return text2image_pb2.ImageResponse(image_base64="", status=f"error: {str(e)}")

    def GenerateImageFromImage(self, request, context):
        try:
            # Decode input image
            init_image = Image.open(io.BytesIO(base64.b64decode(request.input_image_base64))).convert("RGB")
            init_image = init_image.resize((request.width, request.height))

            # Convert base pipeline to img2img pipeline on demand
            print("[Img2Img] Converting base pipeline to img2img...")
            torch.cuda.empty_cache()
            img2img_pipe = StableDiffusionImg2ImgPipeline(**pipe.components).to("cuda")
            img2img_pipe.to(torch_dtype=TORCH_DTYPE)
            img2img_pipe.enable_attention_slicing()
            img2img_pipe.safety_checker = None

            full_prompt = f"{request.prompt}. Context: {request.context}" if request.context else request.prompt
            strength = request.strength or 0.75  # Default strength

            print(f"[Img2Img] Prompt: {full_prompt} | Strength: {strength}")
            image = img2img_pipe(prompt=full_prompt, image=init_image, strength=strength).images[0]

            return self._prepare_response(image, request.width, request.height)

        except Exception as e:
            print(f"Error in img2img: {e}")
            return text2image_pb2.ImageResponse(image_base64="", status=f"error: {str(e)}")

    def _prepare_response(self, image, width, height):
        # Resize to ensure output matches requested size
        image = image.resize((width, height), Image.LANCZOS)

        # Save image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = os.path.join(os.path.dirname(__file__), "..", "images")
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.join(save_dir, f"generated_{timestamp}.png")
        image.save(filename)
        print(f"Image saved: {filename}")

        # Convert image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return text2image_pb2.ImageResponse(image_base64=image_base64, status="success")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    text2image_pb2_grpc.add_Text2ImageServicer_to_server(Text2ImageServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

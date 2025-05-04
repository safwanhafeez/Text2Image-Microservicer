import grpc
from concurrent import futures
import base64
import io
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, AutoencoderKL
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
TORCH_DTYPE = torch.float16

# Define negative prompt
negative_prompt = (
    "blurry, low quality, poorly drawn hands, text, watermark, distorted face, bad anatomy, low resolution"
)

print("Loading VAE...")
vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse",
    torch_dtype=TORCH_DTYPE
).to("cuda")

print("Loading text-to-image pipeline...")
pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    vae=vae,
    torch_dtype=TORCH_DTYPE,
    use_safetensors=True
).to("cuda")
pipe.enable_attention_slicing()
pipe.safety_checker = None  # Optional: skip safety checker to save memory

# gRPC Service Implementation
class Text2ImageServicer(text2image_pb2_grpc.Text2ImageServicer):
    def GenerateImage(self, request, context):
        prompt = request.prompt
        height = request.height or 512
        width = request.width or 512

        try:
            print(f"[Text2Image] Prompt: {prompt}")
            image = pipe(
                prompt, 
                height=height, 
                width=width,
                negative_prompt=negative_prompt,
                guidance_scale=7.5
            ).images[0]

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

            full_prompt = request.prompt
            strength = request.strength or 0.75  # Default strength

            print(f"[Img2Img] Prompt: {full_prompt} | Strength: {strength}")
            image = img2img_pipe(
                prompt=full_prompt, 
                image=init_image, 
                strength=strength,
                negative_prompt=negative_prompt
            ).images[0]

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
    # Listen on all interfaces (important in Docker)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    text2image_pb2_grpc.add_Text2ImageServicer_to_server(Text2ImageServicer(), server)
    server.add_insecure_port('0.0.0.0:50051')
    print("gRPC server started on 0.0.0.0:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
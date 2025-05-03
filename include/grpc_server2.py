import grpc
from concurrent import futures
import base64
import io
import torch
from PIL import Image
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
import datetime
import os
import sys
import text2image_pb2
import text2image_pb2_grpc

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set model ID and dtype
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
TORCH_DTYPE = torch.float16

# Hardcoded negative prompt
NEGATIVE_PROMPT = (
    "blurry, low quality, poorly drawn hands, text, watermark, distorted face, bad anatomy, low resolution"
)

# Load the base pipeline (text-to-image) once at start
print("Loading text-to-image pipeline...")

pipe = StableDiffusionXLPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=TORCH_DTYPE,
    variant="fp16",
    use_safetensors=True,
).to("cuda")

pipe.enable_attention_slicing()
pipe.enable_vae_slicing()
pipe.safety_checker = None

# gRPC Service Implementation
class Text2ImageServicer(text2image_pb2_grpc.Text2ImageServicer):
    def GenerateImage(self, request, context):
        prompt = request.prompt
        height = request.height or 512
        width = request.width or 512

        # Determine quality settings based on resolution
        num_inference_steps, guidance_scale = self._get_quality_settings(width, height)
        
        try:
            print(f"[Text2Image] Prompt: {prompt} | Size: {width}x{height} | Steps: {num_inference_steps}")
            image = pipe(
                prompt=prompt,
                height=height,
                width=width,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
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

            # Determine quality settings based on resolution
            num_inference_steps, guidance_scale = self._get_quality_settings(request.width, request.height)

            # Convert base pipeline to img2img pipeline on demand
            print("[Img2Img] Converting base pipeline to img2img...")
            torch.cuda.empty_cache()
            img2img_pipe = StableDiffusionXLImg2ImgPipeline(**pipe.components).to("cuda")
            img2img_pipe.to(torch_dtype=TORCH_DTYPE)
            img2img_pipe.enable_attention_slicing()
            img2img_pipe.safety_checker = None

            full_prompt = request.prompt
            strength = request.strength or 0.75  # Default strength

            print(f"[Img2Img] Prompt: {full_prompt} | Size: {request.width}x{request.height} | Steps: {num_inference_steps}")
            image = img2img_pipe(
                prompt=full_prompt,
                image=init_image,
                strength=strength,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
            ).images[0]

            return self._prepare_response(image, request.width, request.height)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in img2img: {e}")
            return text2image_pb2.ImageResponse(image_base64="", status=f"error: {str(e)}")

    def _get_quality_settings(self, width, height):
        """Determine optimal quality settings based on image resolution"""
        resolution = width * height
        
        # High resolution (1024x1024 or equivalent)
        if resolution >= 1024 * 1024:
            return 30, 7.5  # More steps, higher guidance
        # Medium resolution (768x768 or equivalent)
        elif resolution >= 768 * 768:
            return 25, 7.0
        # Lower resolution images
        else:
            # For smaller images, we need to increase steps to improve quality
            return 35, 8.0  # Most steps for small images to compensate for artifacts
    
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
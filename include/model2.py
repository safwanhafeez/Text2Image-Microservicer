from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
import torch
from accelerate import cpu_offload

# Try to import bitsandbytes for 8-bit loading if available
try:
    import bitsandbytes as bnb
    use_8bit = True
    print("Using 8-bit optimization with bitsandbytes")
except ImportError:
    use_8bit = False
    print("bitsandbytes not available, using 16-bit")

# Create SDXL pipeline with maximum memory optimizations
if use_8bit:
    # Load in 8-bit precision for maximum memory savings
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        use_safetensors=True,
        variant="fp16",
        load_in_8bit=True  # Dramatic memory savings with minimal quality loss
    )
else:
    # Standard 16-bit loading
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        use_safetensors=True,
        variant="fp16"
    )

# Enable sequential CPU offloading
device = torch.device("cuda")
# Keep components on CPU until needed, significantly reducing peak VRAM
pipe.enable_model_cpu_offload()

# Most aggressive attention slicing setting
pipe.enable_attention_slicing(slice_size=1)

# Use faster scheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    algorithm_type="dpmsolver++",
    final_sigmas_type="sigma_min"
)



# Enable VAE slicing
pipe.enable_vae_slicing()
# Enable VAE tiling for extremely large images (helps with 1024x1024+)
pipe.enable_vae_tiling()

# Lower resolution for memory savings (can increase if VRAM allows)
height = 1024  # Reduced from SDXL's standard 1024
width = 1024   # Reduced from SDXL's standard 1024

from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import torch

# Create pipeline with optimizations
pipe = StableDiffusionPipeline.from_pretrained(
    "SG161222/Realistic_Vision_V5.1_noVAE",
    torch_dtype=torch.float16,
    use_safetensors=True
)

# Move to GPU with potential memory optimization
pipe = pipe.to("cuda")

# Enable memory-efficient attention
pipe.enable_attention_slicing(slice_size="auto")

# Fix scheduler configuration
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    algorithm_type="dpmsolver++",  # Explicitly set algorithm_type
    final_sigmas_type="sigma_min"  # Use sigma_min instead of zero
)

# Optional: Enable memory efficient cross-attention (xformers)
try:
    import xformers
    pipe.enable_xformers_memory_efficient_attention()
    print("xformers optimization enabled")
except (ImportError, AttributeError):
    print("xformers not available, using standard attention")

# Optional: Enable VAE slicing for large images
pipe.enable_vae_slicing()


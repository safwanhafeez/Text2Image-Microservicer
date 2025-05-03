from huggingface_hub import hf_hub_download
from diffusers import AutoencoderKL
import torch

# Download the VAE model manually
model_name = "stabilityai/sd-vae-ft-mse"

TORCH_DTYPE = torch.float16

vae = AutoencoderKL.from_pretrained(
    model_name,
    torch_dtype=TORCH_DTYPE
).to("cuda")

print("VAE model loaded successfully!")

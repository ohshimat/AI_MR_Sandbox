import os
import json
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from diffusers import StableDiffusionXLPipeline
from PIL import Image, ImageDraw, ImageFont

DATA_ROOT = Path.home() / "AI_MR_Sandbox_Data"

MODEL_DIR = (
    DATA_ROOT / "models" / "huggingface"
    / "models--stabilityai--stable-diffusion-xl-base-1.0"
    / "snapshots" / "462165984030d82259a11f4367a4eed129e94a7b"
)

LORA_FILE = (
    DATA_ROOT / "lora_outputs" / "first_test"
    / "pytorch_lora_weights_step200.safetensors"
)

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

SEED = args.seed
OUTPUT_DIR = DATA_ROOT / "outputs" / f"bear_compare_step200_seed{SEED}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS = {
    "prompt": "a photo of aimrbear01 teddy bear",
    "negative_prompt": "blurry, low quality, distorted, text, watermark",
    "width": 512,
    "height": 512,
    "num_inference_steps": 30,
    "guidance_scale": 7.0,
}

print("Loading local SDXL and LoRA...")

pipe = StableDiffusionXLPipeline.from_pretrained(
    str(MODEL_DIR),
    dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
    local_files_only=True,
)

pipe.load_lora_weights(
    str(LORA_FILE.parent),
    weight_name=LORA_FILE.name,
    adapter_name="bear",
    local_files_only=True,
)
pipe.set_adapters("bear", adapter_weights=1.0)
pipe.enable_model_cpu_offload()
pipe.vae.enable_slicing()

images = []

for name, use_lora in [("base", False), ("lora_step200", True)]:
    if use_lora:
        pipe.enable_lora()
    else:
        pipe.disable_lora()

    print(f"Generating: {name}")
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    image = pipe(**SETTINGS, generator=generator).images[0]
    image.save(OUTPUT_DIR / f"{name}_seed{SEED}.png")
    images.append(image)

comparison = Image.new("RGB", (1024, 552), "white")
draw = ImageDraw.Draw(comparison)
font = ImageFont.load_default(size=22)

for index, label in enumerate(["BASE (no LoRA)", "LoRA (200 steps)"]):
    comparison.paste(images[index], (index * 512, 40))
    draw.text((index * 512 + 12, 8), label, fill="black", font=font)

comparison.save(OUTPUT_DIR / "comparison.png")

metadata = {
    **SETTINGS,
    "seed": SEED,
    "model_dir": str(MODEL_DIR),
    "lora_file": str(LORA_FILE),
    "lora_strength": 1.0,
    "torch_version": str(torch.__version__),
}
(OUTPUT_DIR / "settings.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Done. Output folder: {OUTPUT_DIR}")

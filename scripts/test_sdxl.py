import json
import time
from pathlib import Path

import torch
from diffusers import StableDiffusionXLPipeline


MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

CACHE_DIR = Path(
    r"C:\Users\ohshimat\AI_MR_Sandbox_Data\models\huggingface"
)

OUTPUT_DIR = Path(
    r"C:\Users\ohshimat\AI_MR_Sandbox_Data\outputs"
)

PROMPT = (
    "A simple red cube placed on a white table, "
    "clean studio lighting, realistic photograph"
)

NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, text, watermark"
)

SEED = 12345
WIDTH = 768
HEIGHT = 768
STEPS = 20
GUIDANCE_SCALE = 7.0


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("SDXLを読み込んでいます。")
    print("初回はモデルをCドライブへダウンロードします。")

    pipe = StableDiffusionXLPipeline.from_pretrained(
        MODEL_ID,
        cache_dir=str(CACHE_DIR),
        dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )

    # 8GB VRAM向けの省メモリ設定
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()

    generator = torch.Generator(
        device="cpu"
    ).manual_seed(SEED)

    started_at = time.perf_counter()

    result = pipe(
        prompt=PROMPT,
        negative_prompt=NEGATIVE_PROMPT,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=STEPS,
        guidance_scale=GUIDANCE_SCALE,
        generator=generator,
        num_images_per_prompt=1,
    )

    elapsed_seconds = time.perf_counter() - started_at

    image_path = OUTPUT_DIR / "sdxl_test_seed_12345.png"
    metadata_path = OUTPUT_DIR / "sdxl_test_seed_12345.json"

    result.images[0].save(image_path)

    metadata = {
        "model_id": MODEL_ID,
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "seed": SEED,
        "width": WIDTH,
        "height": HEIGHT,
        "steps": STEPS,
        "guidance_scale": GUIDANCE_SCALE,
        "torch_version": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "image_path": str(image_path),
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"生成完了: {image_path}")
    print(f"実験条件: {metadata_path}")
    print(f"生成時間: {elapsed_seconds:.1f}秒")


if __name__ == "__main__":
    main()
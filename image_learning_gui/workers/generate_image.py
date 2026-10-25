from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one local SDXL + LoRA image.")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--lora", required=True, action="append")
    parser.add_argument("--strength", required=True, type=float, action="append")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--steps", required=True, type=int)
    parser.add_argument("--guidance", required=True, type=float)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--result-json", required=True)
    return parser.parse_args()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        temporary.replace(path)
    except PermissionError:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.unlink(missing_ok=True)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir).resolve()
    lora_paths = [Path(value).resolve() for value in args.lora]
    output_dir = Path(args.output_dir).resolve()
    result_json = Path(args.result_json).resolve()

    if not (model_dir / "model_index.json").is_file():
        raise FileNotFoundError(f"SDXL model_index.jsonがありません: {model_dir}")
    if len(lora_paths) != len(args.strength):
        raise ValueError("LoRAファイルと係数の数が一致しません。")
    if len(set(lora_paths)) != len(lora_paths):
        raise ValueError("同じLoRAを複数回指定することはできません。")
    for index, (lora_path, strength) in enumerate(
        zip(lora_paths, args.strength), start=1
    ):
        if not lora_path.is_file() or lora_path.suffix.lower() != ".safetensors":
            raise FileNotFoundError(f"LoRA {index}が見つかりません: {lora_path}")
        if not 0.0 <= strength <= 2.0:
            raise ValueError(f"LoRA {index}の係数は0.0～2.0で指定してください。")
    if not args.prompt.strip():
        raise ValueError("プロンプトが空です。")

    output_dir.mkdir(parents=True, exist_ok=True)
    print("SDXL Baseをローカルから読み込んでいます。", flush=True)

    import torch
    from diffusers import StableDiffusionXLPipeline

    pipe = StableDiffusionXLPipeline.from_pretrained(
        str(model_dir),
        variant="fp16",
        dtype=torch.float16,
        use_safetensors=True,
        local_files_only=True,
    )
    adapter_names: list[str] = []
    for index, lora_path in enumerate(lora_paths, start=1):
        adapter_name = f"research_lora_{index}"
        adapter_names.append(adapter_name)
        print(
            f"LoRA {index}/{len(lora_paths)}を読み込んでいます: "
            f"{lora_path.name} (係数 {args.strength[index - 1]})",
            flush=True,
        )
        pipe.load_lora_weights(
            str(lora_path.parent),
            weight_name=lora_path.name,
            adapter_name=adapter_name,
        )
    pipe.set_adapters(adapter_names, adapter_weights=args.strength)
    pipe.vae.enable_slicing()
    pipe.enable_model_cpu_offload()

    generator = torch.Generator(device="cuda").manual_seed(args.seed)
    print("画像を生成しています。", flush=True)
    image = pipe(
        prompt=args.prompt.strip(),
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=generator,
    ).images[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_stem = lora_paths[0].stem[:48]
    if len(lora_paths) > 1:
        safe_stem += f"_plus{len(lora_paths) - 1}"
    image_path = output_dir / f"{safe_stem}_seed{args.seed}_{timestamp}.png"
    image.save(image_path)

    record = {
        "operation": "generation",
        "status": "success",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_model": str(model_dir),
        "base_model_index_sha256": sha256_file(model_dir / "model_index.json"),
        # The singular fields are kept for compatibility with earlier records.
        "lora": str(lora_paths[0]),
        "lora_sha256": sha256_file(lora_paths[0]),
        "lora_strength": args.strength[0],
        "loras": [
            {
                "path": str(lora_path),
                "sha256": sha256_file(lora_path),
                "strength": strength,
                "adapter_name": adapter_name,
            }
            for lora_path, strength, adapter_name in zip(
                lora_paths, args.strength, adapter_names
            )
        ],
        "prompt": args.prompt.strip(),
        "negative_prompt": args.negative_prompt,
        "seed": args.seed,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "guidance_scale": args.guidance,
        "image": str(image_path),
        "image_sha256": sha256_file(image_path),
        "software_versions": {
            "torch": package_version("torch"),
            "diffusers": package_version("diffusers"),
            "transformers": package_version("transformers"),
            "peft": package_version("peft"),
        },
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    sidecar = image_path.with_suffix(".json")
    write_json_atomic(sidecar, record)
    record["sidecar_json"] = str(sidecar)
    write_json_atomic(result_json, record)

    print(f"画像生成が完了しました: {image_path}", flush=True)
    print(f"RESULT_JSON={result_json}", flush=True)

    del pipe
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()

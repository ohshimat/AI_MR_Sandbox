from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .environment import resolve_model_dir
from .process_manager import JobSnapshot, ProcessManager
from .records import timestamp_id


@dataclass(frozen=True)
class LoraAdapter:
    path: str
    strength: float


@dataclass(frozen=True)
class GenerationRequest:
    loras: tuple[LoraAdapter, ...]
    prompt: str
    seed: int
    width: int
    height: int
    output_dir: str


def validate_generation_request(request: GenerationRequest) -> None:
    if not request.loras:
        raise ValueError("生成用LoRAを1つ以上選択してください。")
    resolved_paths: set[Path] = set()
    for index, adapter in enumerate(request.loras, start=1):
        lora = Path(adapter.path).expanduser().resolve()
        if not lora.is_file():
            raise ValueError(f"生成用LoRA {index}が見つかりません: {lora}")
        if lora.suffix.lower() != ".safetensors":
            raise ValueError(
                f"生成用LoRA {index}は.safetensorsファイルを選択してください。"
            )
        if lora in resolved_paths:
            raise ValueError("同じLoRAを複数の枠に指定することはできません。")
        resolved_paths.add(lora)
        if not 0.0 <= float(adapter.strength) <= 2.0:
            raise ValueError(f"LoRA {index}の係数は0.0～2.0で指定してください。")
    if not request.prompt.strip():
        raise ValueError("画像生成プロンプトを入力してください。")
    try:
        int(request.seed)
    except (TypeError, ValueError) as error:
        raise ValueError("seedは整数で指定してください。") from error
    for label, value in (("横幅", request.width), ("縦幅", request.height)):
        try:
            dimension = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label}は整数で指定してください。") from error
        if not 256 <= dimension <= 2048:
            raise ValueError(f"{label}は256～2048で指定してください。")
        if dimension % 8 != 0:
            raise ValueError(f"{label}は8の倍数で指定してください。")
    output = Path(request.output_dir).expanduser()
    if output.exists() and not output.is_dir():
        raise ValueError(f"画像生成先がフォルダではありません: {output}")


class GenerationService:
    def __init__(self, config: dict[str, Any], jobs: ProcessManager) -> None:
        self.config = config
        self.jobs = jobs
        self.last_result_json: Path | None = None

    def start(self, request: GenerationRequest) -> JobSnapshot:
        validate_generation_request(request)
        model_dir = resolve_model_dir(self.config["paths"]["model_snapshot_root"])
        if model_dir is None:
            raise ValueError("SDXL Baseのローカルsnapshotが見つかりません。")
        output = Path(request.output_dir).expanduser()
        output.mkdir(parents=True, exist_ok=True)
        job_id = timestamp_id("generation")
        result_json = output / f"{job_id}_result.json"
        log_path = output / f"{job_id}.log"
        self.last_result_json = result_json

        fixed = self.config["generation"]
        command = [
            self.config["paths"]["python_executable"],
            self.config["paths"]["generation_worker"],
            f"--model-dir={model_dir}",
        ]
        for adapter in request.loras:
            command.extend(
                [
                    f"--lora={Path(adapter.path).expanduser().resolve()}",
                    f"--strength={float(adapter.strength)}",
                ]
            )
        command.extend(
            [
                f"--prompt={request.prompt.strip()}",
                f"--negative-prompt={fixed['negative_prompt']}",
                f"--seed={int(request.seed)}",
                f"--width={int(request.width)}",
                f"--height={int(request.height)}",
                f"--steps={int(fixed['steps'])}",
                f"--guidance={float(fixed['guidance_scale'])}",
                f"--output-dir={output.resolve()}",
                f"--result-json={result_json.resolve()}",
            ]
        )
        child_environment = os.environ.copy()
        child_environment["HF_HUB_OFFLINE"] = "1"
        child_environment["TRANSFORMERS_OFFLINE"] = "1"
        child_environment.pop("PYTORCH_CUDA_ALLOC_CONF", None)
        child_environment.pop("PYTHONPATH", None)
        return self.jobs.start(
            job_id=job_id,
            operation="画像生成",
            command=command,
            cwd=Path(self.config["paths"]["generation_worker"]).parent,
            environment=child_environment,
            log_path=log_path,
        )

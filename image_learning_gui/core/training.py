from __future__ import annotations

import os
import re
import shutil
import json
from math import ceil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dataset import DatasetReport, inspect_dataset
from .captions import list_caption_entries
from .environment import inspect_environment, resolve_model_dir
from .process_manager import JobSnapshot, ProcessManager
from .records import iso_now, sha256_file, timestamp_id, write_json_atomic


CHECKPOINT_PATTERN = re.compile(r"^checkpoint-(\d+)$")
TRIGGER_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]*\d+[a-zA-Z0-9_-]*\b")
CAPTION_MODE_FIXED = "固定プロンプト"
CAPTION_MODE_PER_IMAGE = "画像別キャプション（未入力は共通）"


@dataclass(frozen=True)
class TrainingRequest:
    image_dir: str
    mode: str
    output_dir: str
    target_steps: int
    instance_prompt: str
    caption_mode: str = CAPTION_MODE_FIXED
    resume_checkpoint: str = ""


def list_checkpoints(directory: str | Path) -> tuple[tuple[Path, int], ...]:
    root = Path(directory).expanduser()
    if not root.is_dir():
        return ()
    matches: list[tuple[Path, int]] = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        match = CHECKPOINT_PATTERN.fullmatch(path.name)
        if match:
            matches.append((path.resolve(), int(match.group(1))))
    return tuple(sorted(matches, key=lambda item: item[1]))


def latest_checkpoint(directory: str | Path) -> tuple[Path | None, int]:
    checkpoints = list_checkpoints(directory)
    if not checkpoints:
        return None, 0
    return checkpoints[-1]


def infer_trigger(prompt: str) -> str:
    match = TRIGGER_PATTERN.search(prompt)
    return match.group(0) if match else "research"


def named_lora_path(output_dir: str | Path, prompt: str, steps: int) -> Path:
    return Path(output_dir) / f"{infer_trigger(prompt)}_sdxl_lora_step{steps}.safetensors"


def calculate_training_steps(
    image_count: int,
    repetitions_per_image: int,
    train_batch_size: int = 1,
    gradient_accumulation_steps: int = 1,
    num_processes: int = 1,
) -> int:
    """Convert per-image repetitions into optimizer steps."""

    values = {
        "学習画像数": image_count,
        "1画像あたりの学習回数": repetitions_per_image,
        "batch size": train_batch_size,
        "gradient accumulation": gradient_accumulation_steps,
        "processes": num_processes,
    }
    for label, value in values.items():
        if int(value) < 1:
            raise ValueError(f"{label}は1以上で指定してください。")
    images_per_step = (
        int(train_batch_size)
        * int(gradient_accumulation_steps)
        * int(num_processes)
    )
    return ceil(int(image_count) * int(repetitions_per_image) / images_per_step)


def calculate_resume_target_steps(
    additional_steps: int, resume_checkpoint: str
) -> int:
    """Convert a selected checkpoint plus additional work into max_train_steps."""

    if int(additional_steps) < 1:
        raise ValueError("追加ステップは1以上で指定してください。")
    match = CHECKPOINT_PATTERN.fullmatch(str(resume_checkpoint).strip())
    if match is None:
        raise ValueError("継続元checkpointを選択してください。")
    return int(match.group(1)) + int(additional_steps)


def stage_training_dataset(
    report: DatasetReport,
    staging_root: str | Path,
    job_id: str,
    caption_mode: str = CAPTION_MODE_FIXED,
    instance_prompt: str = "",
) -> Path:
    """Stage validated images and optional ImageFolder caption metadata."""

    source_root = Path(report.directory).resolve()
    destination = Path(staging_root).expanduser().resolve() / "training_images" / job_id
    if caption_mode not in {CAPTION_MODE_FIXED, CAPTION_MODE_PER_IMAGE}:
        raise ValueError(f"未対応の学習プロンプト方式です: {caption_mode}")
    if destination.exists():
        raise ValueError(f"学習用一時フォルダが既に存在します: {destination}")
    destination.mkdir(parents=True)
    try:
        for record in report.records:
            if record.valid:
                shutil.copy2(source_root / record.relative_path, destination / record.relative_path)
        if caption_mode == CAPTION_MODE_PER_IMAGE:
            entries = list_caption_entries(source_root)
            common_prompt = instance_prompt.strip()
            if any(not entry.has_caption for entry in entries) and not common_prompt:
                raise ValueError(
                    "個別キャプションのない画像に適用する共通プロンプトが必要です。"
                )
            metadata = destination / "metadata.jsonl"
            lines = [
                json.dumps(
                    {
                        "file_name": entry.image_path.name,
                        "prompt": entry.caption if entry.has_caption else common_prompt,
                    },
                    ensure_ascii=False,
                )
                for entry in entries
            ]
            metadata.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def stage_training_images(
    report: DatasetReport, staging_root: str | Path, job_id: str
) -> Path:
    """Backward-compatible fixed-prompt staging helper."""

    return stage_training_dataset(
        report, staging_root, job_id, caption_mode=CAPTION_MODE_FIXED
    )


def validate_training_request(
    request: TrainingRequest, config: dict[str, Any]
) -> tuple[DatasetReport, Path, int]:
    report = inspect_dataset(
        request.image_dir,
        minimum_size=int(config["training"]["resolution"]),
        include_hashes=True,
    )
    if not report.can_train:
        raise ValueError("破損画像があるため学習を開始できません。")
    if not request.instance_prompt.strip():
        raise ValueError("共通／識別用の学習プロンプトを入力してください。")
    if request.caption_mode not in {CAPTION_MODE_FIXED, CAPTION_MODE_PER_IMAGE}:
        raise ValueError(f"未対応の学習プロンプト方式です: {request.caption_mode}")
    if int(request.target_steps) < 1:
        raise ValueError("目標ステップは1以上で指定してください。")

    output = Path(request.output_dir).expanduser()
    checkpoint_step = 0
    if request.mode == "新規学習":
        if output.exists() and any(output.iterdir()):
            raise ValueError(
                "新規学習の出力フォルダが空ではありません。新しいフォルダを指定してください。"
            )
        checkpoint_step = 0
    elif request.mode == "checkpointから継続":
        checkpoints = list_checkpoints(output)
        if not checkpoints:
            raise ValueError("継続学習に必要なcheckpoint-Nが見つかりません。")
        selected_name = request.resume_checkpoint.strip()
        if not selected_name:
            raise ValueError(
                "継続元checkpointを選択してください。先にcheckpointを確認してください。"
            )
        if CHECKPOINT_PATTERN.fullmatch(selected_name) is None:
            raise ValueError(f"継続元checkpointの名前が不正です: {selected_name}")
        selected = next(
            ((path, step) for path, step in checkpoints if path.name == selected_name),
            None,
        )
        if selected is None:
            raise ValueError(f"選択したcheckpointが見つかりません: {selected_name}")
        _, checkpoint_step = selected
        newest_step = checkpoints[-1][1]
        if checkpoint_step != newest_step:
            raise ValueError(
                f"{selected_name}より新しいcheckpoint-{newest_step}が同じフォルダにあります。"
                "後続checkpointの上書きを避けるため、最新checkpointを選択してください。"
            )
        if int(request.target_steps) <= checkpoint_step:
            raise ValueError(
                f"目標ステップは最新checkpoint（{checkpoint_step}）より大きくしてください。"
            )
    else:
        raise ValueError(f"未対応の学習モードです: {request.mode}")

    destination = named_lora_path(output, request.instance_prompt, int(request.target_steps))
    if destination.exists():
        raise ValueError(f"保存予定のLoRAが既に存在します: {destination}")
    return report, output, checkpoint_step


def build_training_command(
    request: TrainingRequest,
    config: dict[str, Any],
    model_dir: str | Path,
    instance_data_dir: str | Path | None = None,
) -> list[str]:
    paths = config["paths"]
    fixed = config["training"]
    arguments = [
        paths["accelerate_executable"],
        "launch",
        paths["training_script"],
        f"--pretrained_model_name_or_path={model_dir}",
        f"--variant={fixed['variant']}",
        f"--instance_prompt={request.instance_prompt.strip()}",
        f"--output_dir={Path(request.output_dir).expanduser().resolve()}",
        f"--resolution={fixed['resolution']}",
        "--center_crop",
        f"--train_batch_size={fixed['train_batch_size']}",
        f"--gradient_accumulation_steps={fixed['gradient_accumulation_steps']}",
        "--gradient_checkpointing",
        f"--learning_rate={fixed['learning_rate']}",
        f"--lr_scheduler={fixed['lr_scheduler']}",
        f"--lr_warmup_steps={fixed['lr_warmup_steps']}",
        f"--max_train_steps={int(request.target_steps)}",
        f"--checkpointing_steps={fixed['checkpointing_steps']}",
        f"--checkpoints_total_limit={fixed['checkpoints_total_limit']}",
        f"--mixed_precision={fixed['mixed_precision']}",
        f"--rank={fixed['rank']}",
        f"--dataloader_num_workers={fixed['dataloader_num_workers']}",
        f"--report_to={fixed['report_to']}",
        f"--seed={fixed['seed']}",
    ]
    staged_data = Path(instance_data_dir or request.image_dir).expanduser().resolve()
    if request.caption_mode == CAPTION_MODE_PER_IMAGE:
        datasets_cache = Path(
            paths.get("datasets_cache", staged_data.parent / "datasets_cache")
        ).expanduser().resolve()
        arguments[5:5] = [
            f"--dataset_name={staged_data}",
            "--caption_column=prompt",
            f"--cache_dir={datasets_cache}",
        ]
    else:
        arguments.insert(5, f"--instance_data_dir={staged_data}")
    if request.mode == "checkpointから継続":
        arguments.append(
            f"--resume_from_checkpoint={request.resume_checkpoint.strip()}"
        )
    return arguments


class TrainingService:
    def __init__(self, config: dict[str, Any], jobs: ProcessManager) -> None:
        self.config = config
        self.jobs = jobs
        self._manifest_path: Path | None = None
        self._manifest: dict[str, Any] | None = None
        self._request: TrainingRequest | None = None
        self._staging_dir: Path | None = None

    def start(self, request: TrainingRequest) -> JobSnapshot:
        report, output, checkpoint_step = validate_training_request(request, self.config)
        environment_report = inspect_environment(self.config)
        if not environment_report.ready:
            raise ValueError("実行環境が準備できていません。環境・履歴タブを確認してください。")
        if (
            environment_report.nvidia_used_mib is not None
            and environment_report.nvidia_used_mib > 1024
        ):
            raise ValueError(
                f"学習前のVRAM使用量が{environment_report.nvidia_used_mib} MiBです。"
                "GPUを使用する他のアプリを終了してください。"
            )

        model_dir = resolve_model_dir(self.config["paths"]["model_snapshot_root"])
        if model_dir is None:
            raise ValueError("SDXL Baseのローカルsnapshotが見つかりません。")

        output.mkdir(parents=True, exist_ok=True)
        job_id = timestamp_id("train")
        if (
            request.caption_mode == CAPTION_MODE_PER_IMAGE
            and environment_report.packages.get("datasets") in {None, "未導入", "取得不可"}
        ):
            raise ValueError(
                "画像別キャプション学習に必要なdatasetsパッケージが未導入です。"
                "install_training_dependencies.cmdを実行してください。"
            )

        staging_dir = stage_training_dataset(
            report,
            self.config["paths"]["records_root"],
            job_id,
            caption_mode=request.caption_mode,
            instance_prompt=request.instance_prompt,
        )
        log_path = output / f"{job_id}.log"
        manifest_path = output / f"{job_id}_manifest.json"
        model_index = model_dir / "model_index.json"
        self._request = request
        self._staging_dir = staging_dir
        self._manifest_path = manifest_path
        caption_records = []
        caption_metadata_path = None
        caption_metadata_sha256 = None
        if request.caption_mode == CAPTION_MODE_PER_IMAGE:
            caption_metadata_path = (staging_dir / "metadata.jsonl").resolve()
            caption_metadata_sha256 = sha256_file(caption_metadata_path)
            caption_records = [
                {
                    "image": entry.image_path.name,
                    "caption_file": (
                        entry.caption_path.name if entry.has_caption else None
                    ),
                    "caption": (
                        entry.caption
                        if entry.has_caption
                        else request.instance_prompt.strip()
                    ),
                    "caption_source": (
                        "individual" if entry.has_caption else "common_prompt"
                    ),
                    "caption_sha256": (
                        sha256_file(entry.caption_path) if entry.has_caption else None
                    ),
                }
                for entry in list_caption_entries(report.directory)
            ]
        self._manifest = {
            "experiment_id": job_id,
            "operation": "training",
            "status": "running",
            "base_model": str(model_dir),
            "base_model_index_sha256": sha256_file(model_index),
            "training_image_dir": report.directory,
            "staged_image_dir": str(staging_dir),
            "image_count": report.valid,
            "training_images": report.to_dict()["records"],
            "instance_prompt": request.instance_prompt.strip(),
            "caption_mode": request.caption_mode,
            "caption_count": (
                sum(
                    entry.has_caption
                    for entry in list_caption_entries(report.directory)
                )
                if request.caption_mode == CAPTION_MODE_PER_IMAGE
                else 0
            ),
            "common_prompt_fallback_count": (
                sum(
                    not entry.has_caption
                    for entry in list_caption_entries(report.directory)
                )
                if request.caption_mode == CAPTION_MODE_PER_IMAGE
                else 0
            ),
            "caption_metadata": (
                str(caption_metadata_path) if caption_metadata_path else None
            ),
            "caption_metadata_sha256": caption_metadata_sha256,
            "training_captions": caption_records,
            "mode": request.mode,
            "resume_checkpoint": (
                request.resume_checkpoint.strip() if checkpoint_step else None
            ),
            "target_steps": int(request.target_steps),
            "additional_steps": int(request.target_steps) - checkpoint_step,
            "fixed_parameters": self.config["training"],
            "output_lora": None,
            "output_lora_sha256": None,
            "started_at": iso_now(),
            "finished_at": None,
            "software_versions": environment_report.packages,
            "gpu": {
                "name": environment_report.gpu_name,
                "memory_total_mib": environment_report.nvidia_total_mib,
            },
            "log_path": str(log_path),
        }
        write_json_atomic(manifest_path, self._manifest)

        child_environment = os.environ.copy()
        child_environment["HF_HUB_OFFLINE"] = "1"
        child_environment["HF_DATASETS_OFFLINE"] = "1"
        child_environment["TRANSFORMERS_OFFLINE"] = "1"
        child_environment.pop("PYTORCH_CUDA_ALLOC_CONF", None)
        training_packages = self.config["paths"].get("training_packages")
        if training_packages:
            child_environment["PYTHONPATH"] = str(
                Path(training_packages).expanduser().resolve()
            )
        else:
            child_environment.pop("PYTHONPATH", None)
        datasets_cache = self.config["paths"].get("datasets_cache")
        if datasets_cache:
            datasets_cache_path = Path(datasets_cache).expanduser().resolve()
            datasets_cache_path.mkdir(parents=True, exist_ok=True)
            child_environment["HF_DATASETS_CACHE"] = str(datasets_cache_path)

        command = build_training_command(
            request, self.config, model_dir, instance_data_dir=staging_dir
        )
        try:
            return self.jobs.start(
                job_id=job_id,
                operation="LoRA学習",
                command=command,
                cwd=Path(self.config["paths"]["training_script"]).parent,
                environment=child_environment,
                log_path=log_path,
                on_complete=self._finalize,
            )
        except Exception:
            shutil.rmtree(staging_dir, ignore_errors=True)
            self._staging_dir = None
            raise

    def _finalize(self, snapshot: JobSnapshot) -> None:
        if self._manifest is None or self._manifest_path is None or self._request is None:
            return
        manifest = dict(self._manifest)
        manifest["finished_at"] = snapshot.finished_at or iso_now()
        manifest["return_code"] = snapshot.return_code
        manifest["status"] = snapshot.state

        current = Path(self._request.output_dir) / "pytorch_lora_weights.safetensors"
        if snapshot.state == "succeeded" and current.is_file():
            destination = named_lora_path(
                self._request.output_dir,
                self._request.instance_prompt,
                int(self._request.target_steps),
            )
            if destination.exists():
                manifest["status"] = "failed"
                manifest["finalization_error"] = (
                    f"保存先が既に存在するため上書きしませんでした: {destination}"
                )
            else:
                shutil.copy2(current, destination)
                manifest["output_lora"] = str(destination.resolve())
                manifest["output_lora_sha256"] = sha256_file(destination)
        elif snapshot.state == "succeeded":
            manifest["status"] = "failed"
            manifest["finalization_error"] = (
                "学習プロセスは終了コード0でしたが、LoRAファイルが見つかりません。"
            )
        if self._staging_dir is not None:
            try:
                shutil.rmtree(self._staging_dir)
                manifest["staged_image_cleanup"] = "success"
            except OSError as error:
                manifest["staged_image_cleanup"] = f"failed: {error}"
            self._staging_dir = None
        write_json_atomic(self._manifest_path, manifest)
        self._manifest = manifest

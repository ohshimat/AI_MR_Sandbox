from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PACKAGES = (
    "torch",
    "diffusers",
    "transformers",
    "peft",
    "accelerate",
    "huggingface-hub",
    "datasets",
)


@dataclass(frozen=True)
class EnvironmentReport:
    python_executable: str
    python_version: str
    packages: dict[str, str]
    cuda_available: bool
    cuda_runtime: str | None
    gpu_name: str | None
    torch_vram_allocated_mib: float | None
    nvidia_used_mib: int | None
    nvidia_total_mib: int | None
    model_dir: str | None
    path_status: dict[str, bool]
    disk_free_gib: dict[str, float | None]
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.cuda_available
            and self.model_dir is not None
            and all(self.path_status.values())
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        symbol = "✅" if self.ready else "⚠️"
        lines = [
            f"### {symbol} 実行環境",
            "",
            f"- Python：`{self.python_executable}`",
            f"- Python版：{self.python_version}",
            f"- CUDA利用可能：{self.cuda_available}",
            f"- CUDA Runtime：{self.cuda_runtime or '取得不可'}",
            f"- GPU：{self.gpu_name or '取得不可'}",
            f"- NVIDIA VRAM：{self.nvidia_used_mib if self.nvidia_used_mib is not None else '?'} / {self.nvidia_total_mib if self.nvidia_total_mib is not None else '?'} MiB",
            f"- SDXL Base：`{self.model_dir or '見つかりません'}`",
            "",
            "#### パッケージ",
        ]
        lines.extend(f"- {name}：{version}" for name, version in self.packages.items())
        lines.extend(["", "#### 必須パス"])
        lines.extend(
            f"- {'✅' if exists else '❌'} `{name}`"
            for name, exists in self.path_status.items()
        )
        lines.extend(["", "#### ディスク空き容量"])
        lines.extend(
            f"- {drive}：{free:.1f} GiB" if free is not None else f"- {drive}：取得不可"
            for drive, free in self.disk_free_gib.items()
        )
        if self.errors:
            lines.extend(["", "#### 確認事項"])
            lines.extend(f"- {error}" for error in self.errors)
        return "\n".join(lines)


def resolve_model_dir(snapshot_root: str | Path) -> Path | None:
    root = Path(snapshot_root).expanduser()
    try:
        if not root.is_dir():
            return None
        candidates = sorted(
            root.glob("*/model_index.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None
    return candidates[0].parent.resolve() if candidates else None


def _python_environment(
    python_executable: str, extra_pythonpath: str | Path | None = None
) -> dict[str, Any]:
    script = """
import importlib.metadata
import json
import sys

packages = {}
for name in %r:
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = "未導入"

result = {
    "python_executable": sys.executable,
    "python_version": sys.version.split()[0],
    "packages": packages,
    "cuda_available": False,
    "cuda_runtime": None,
    "gpu_name": None,
    "torch_vram_allocated_mib": None,
}
try:
    import torch
    result["cuda_available"] = torch.cuda.is_available()
    result["cuda_runtime"] = torch.version.cuda
    if result["cuda_available"]:
        result["gpu_name"] = torch.cuda.get_device_name(0)
        result["torch_vram_allocated_mib"] = round(
            torch.cuda.memory_allocated(0) / (1024 ** 2), 1
        )
except Exception as error:
    result["torch_error"] = str(error)
print(json.dumps(result, ensure_ascii=False))
""" % (PACKAGES,)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    if extra_pythonpath:
        environment["PYTHONPATH"] = str(Path(extra_pythonpath).resolve())
    completed = subprocess.run(
        [python_executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=environment,
    )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _nvidia_memory() -> tuple[int | None, int | None, str | None]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,name",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        first_line = completed.stdout.strip().splitlines()[0]
        used, total, name = (part.strip() for part in first_line.split(",", 2))
        return int(used), int(total), name
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, None, None


def _disk_free(path: str) -> float | None:
    try:
        return round(shutil.disk_usage(path).free / (1024**3), 2)
    except OSError:
        return None


def _is_file(path: str | Path) -> bool:
    try:
        return Path(path).is_file()
    except OSError:
        return False


def _is_dir(path: str | Path) -> bool:
    try:
        return Path(path).is_dir()
    except OSError:
        return False


def inspect_environment(config: dict[str, Any]) -> EnvironmentReport:
    errors: list[str] = []
    paths = config["paths"]
    model_dir = resolve_model_dir(paths["model_snapshot_root"])

    required = {
        "Python": _is_file(paths["python_executable"]),
        "Accelerate": _is_file(paths["accelerate_executable"]),
        "DreamBooth学習スクリプト": _is_file(paths["training_script"]),
        "SDXL snapshotルート": _is_dir(paths["model_snapshot_root"]),
    }

    python_details: dict[str, Any] = {
        "python_executable": paths["python_executable"],
        "python_version": "取得不可",
        "packages": {name: "取得不可" for name in PACKAGES},
        "cuda_available": False,
        "cuda_runtime": None,
        "gpu_name": None,
        "torch_vram_allocated_mib": None,
    }
    try:
        python_details = _python_environment(
            paths["python_executable"], paths.get("training_packages")
        )
    except Exception as error:
        errors.append(f"PyTorch/CUDA情報を取得できません: {error}")

    nvidia_used, nvidia_total, nvidia_name = _nvidia_memory()
    cuda_available = bool(python_details.get("cuda_available"))
    gpu_name = python_details.get("gpu_name") or nvidia_name
    if not cuda_available:
        errors.append("CUDA GPUを利用できません。")
    if model_dir is None:
        errors.append("SDXL Baseのmodel_index.jsonが見つかりません。")
    for name, exists in required.items():
        if not exists:
            errors.append(f"必須パスが見つかりません: {name}")

    return EnvironmentReport(
        python_executable=str(python_details.get("python_executable")),
        python_version=str(python_details.get("python_version")),
        packages=dict(python_details.get("packages", {})),
        cuda_available=cuda_available,
        cuda_runtime=python_details.get("cuda_runtime"),
        gpu_name=gpu_name,
        torch_vram_allocated_mib=python_details.get("torch_vram_allocated_mib"),
        nvidia_used_mib=nvidia_used,
        nvidia_total_mib=nvidia_total,
        model_dir=str(model_dir) if model_dir else None,
        path_status=required,
        disk_free_gib={"C:": _disk_free("C:\\"), "E:": _disk_free("E:\\")},
        errors=tuple(errors),
    )


def environment_json(config: dict[str, Any]) -> str:
    return json.dumps(
        inspect_environment(config).to_dict(), ensure_ascii=False, indent=2
    )

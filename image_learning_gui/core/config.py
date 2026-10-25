from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "defaults.yaml"


def _portable_environment_defaults() -> dict[str, str]:
    """Return PC-local resource defaults without fixing the portable drive."""

    common_root = Path(os.environ.get("AI_MR_COMMON_ROOT", r"C:\AI_MR_Sandbox"))
    legacy_gui_root = common_root / "image_learning_gui"
    runtime_root = common_root / "runtime"
    preferred_training_packages = runtime_root / "image_training_packages"
    legacy_training_packages = legacy_gui_root / ".training_packages"
    training_packages = (
        preferred_training_packages
        if preferred_training_packages.is_dir()
        or not legacy_training_packages.is_dir()
        else legacy_training_packages
    )

    return {
        "AI_MR_COMMON_ROOT": str(common_root),
        "AI_MR_WORKSPACE": os.environ.get(
            "AI_MR_WORKSPACE", str(Path.home() / "AI_MR_Workspace")
        ),
        "AI_MR_IMAGE_PYTHON": os.environ.get(
            "AI_MR_IMAGE_PYTHON",
            r"C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe",
        ),
        "AI_MR_IMAGE_ACCELERATE": os.environ.get(
            "AI_MR_IMAGE_ACCELERATE",
            r"C:\AI_venvs\AI_MR_Sandbox\Scripts\accelerate.exe",
        ),
        "AI_MR_TRAINING_PACKAGES": os.environ.get(
            "AI_MR_TRAINING_PACKAGES", str(training_packages)
        ),
    }


def _expand_portable_value(value: str) -> str:
    expanded = value
    for name, default in _portable_environment_defaults().items():
        expanded = expanded.replace(f"%{name}%", default)
    return os.path.expandvars(expanded)


class ConfigurationError(ValueError):
    """Raised when a required GUI configuration value is missing."""


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise ConfigurationError(f"設定ファイルが見つかりません: {config_path}")

    with config_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}

    required_sections = {"app", "paths", "training", "generation"}
    missing = sorted(required_sections - set(data))
    if missing:
        raise ConfigurationError(
            "設定ファイルに必須セクションがありません: " + ", ".join(missing)
        )

    # Expand environment variables first so user paths remain portable between
    # Windows accounts. Project-local paths still move together with the GUI.
    project_local_keys = {
        "training_script",
        "generation_worker",
    }
    for key, value in data.get("paths", {}).items():
        if value:
            candidate = Path(_expand_portable_value(str(value))).expanduser()
            if key in project_local_keys and not candidate.is_absolute():
                data["paths"][key] = str((PROJECT_ROOT / candidate).resolve())
            else:
                data["paths"][key] = str(candidate)

    ui_path_keys = {
        "training_image_dir",
        "training_output_dir",
        "generation_lora",
        "generation_lora_2",
        "generation_lora_3",
        "generation_output_dir",
        "external_storage_root",
        "archive_path",
        "restore_pc_root",
    }
    for key in ui_path_keys:
        value = data.get("ui_defaults", {}).get(key)
        if value:
            data["ui_defaults"][key] = str(
                Path(_expand_portable_value(str(value))).expanduser()
            )

    return data


def user_settings_path(config: dict[str, Any]) -> Path:
    return Path(config["paths"]["user_settings_file"]).expanduser()


def load_user_settings(config: dict[str, Any]) -> dict[str, Any]:
    path = user_settings_path(config)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_user_settings(config: dict[str, Any], settings: dict[str, Any]) -> Path:
    path = user_settings_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        temporary.replace(path)
    except PermissionError:
        path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.unlink(missing_ok=True)
    return path


def merged_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Return mutable UI defaults without changing the fixed configuration."""

    merged = deepcopy(config)
    saved = load_user_settings(config)
    for key, value in saved.items():
        if key in merged.get("ui_defaults", {}):
            merged["ui_defaults"][key] = value
    return merged

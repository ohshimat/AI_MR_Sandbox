from __future__ import annotations

import shutil
from pathlib import Path

from .records import sha256_file


PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def cache_preview_image(source: str | Path, cache_dir: str | Path) -> Path:
    """Copy a generated image to the only directory Gradio may serve."""

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"生成画像が見つかりません: {source_path}")
    if source_path.suffix.lower() not in PREVIEW_EXTENSIONS:
        raise ValueError(f"プレビュー未対応の画像形式です: {source_path.suffix}")

    preview_root = Path(cache_dir).expanduser().resolve()
    preview_root.mkdir(parents=True, exist_ok=True)
    fingerprint = sha256_file(source_path)[:16]
    destination = preview_root / (
        f"{source_path.stem}_{fingerprint}{source_path.suffix.lower()}"
    )
    if not destination.exists():
        shutil.copy2(source_path, destination)
    return destination

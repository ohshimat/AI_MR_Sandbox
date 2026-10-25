from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .dataset import IMAGE_EXTENSIONS
from .records import sha256_file


@dataclass(frozen=True)
class CaptionEntry:
    image_path: Path
    caption_path: Path
    caption: str

    @property
    def has_caption(self) -> bool:
        return bool(self.caption.strip())


def list_caption_entries(directory: str | Path) -> tuple[CaptionEntry, ...]:
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"学習画像フォルダが見つかりません: {root}")

    images = sorted(
        (
            path.resolve()
            for path in root.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda path: path.name.casefold(),
    )
    if not images:
        raise ValueError(f"対応する学習画像がありません: {root}")

    stems: dict[str, Path] = {}
    for image in images:
        key = image.stem.casefold()
        if key in stems:
            raise ValueError(
                "同じ基本ファイル名の画像が複数あります。キャプション名が衝突します: "
                f"{stems[key].name}, {image.name}"
            )
        stems[key] = image

    entries: list[CaptionEntry] = []
    for image in images:
        caption_path = image.with_suffix(".txt")
        caption = ""
        if caption_path.is_file():
            caption = caption_path.read_text(encoding="utf-8-sig").strip()
        entries.append(
            CaptionEntry(
                image_path=image,
                caption_path=caption_path,
                caption=caption,
            )
        )
    return tuple(entries)


def save_image_caption(
    directory: str | Path, image_path: str | Path, caption: str
) -> Path:
    root = Path(directory).expanduser().resolve()
    selected = Path(image_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"学習画像フォルダが見つかりません: {root}")
    if selected.parent != root:
        raise ValueError("選択画像が学習画像フォルダの直下にありません。")
    if not selected.is_file() or selected.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"選択画像が見つかりません: {selected}")

    normalized = caption.strip()
    if not normalized:
        raise ValueError("キャプションを入力してください。")

    caption_path = selected.with_suffix(".txt")
    temporary = caption_path.with_suffix(caption_path.suffix + ".tmp")
    temporary.write_text(normalized + "\n", encoding="utf-8")
    try:
        temporary.replace(caption_path)
    except PermissionError:
        caption_path.write_text(normalized + "\n", encoding="utf-8")
        temporary.unlink(missing_ok=True)
    return caption_path


def cache_caption_thumbnail(
    image_path: str | Path,
    cache_dir: str | Path,
    maximum_size: tuple[int, int] = (384, 384),
) -> Path:
    source = Path(image_path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"プレビューできない画像です: {source}")

    root = Path(cache_dir).expanduser().resolve() / "caption_thumbnails"
    root.mkdir(parents=True, exist_ok=True)
    fingerprint = sha256_file(source)[:16]
    destination = root / f"{source.stem}_{fingerprint}.jpg"
    if destination.is_file():
        return destination

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.thumbnail(maximum_size)
        image.save(destination, format="JPEG", quality=88, optimize=True)
    return destination


def caption_progress_markdown(
    entries: tuple[CaptionEntry, ...], selected: CaptionEntry | None = None
) -> str:
    completed = sum(entry.has_caption for entry in entries)
    lines = [
        "### 個別キャプション",
        "",
        f"- 学習画像：{len(entries)}枚",
        f"- 入力済み：{completed}件",
        f"- 未入力：{len(entries) - completed}件",
        "- 適用規則：入力済みは個別キャプション、未入力は共通プロンプト",
    ]
    if selected is not None:
        lines.extend(
            [
                "",
                f"- 選択画像：`{selected.image_path.name}`",
                f"- 保存先：`{selected.caption_path}`",
                f"- 状態：{'保存済み' if selected.has_caption else '未入力'}",
            ]
        )
    return "\n".join(lines)

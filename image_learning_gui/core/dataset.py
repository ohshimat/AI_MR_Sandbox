from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from .records import sha256_file


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class ImageRecord:
    relative_path: str
    width: int | None
    height: int | None
    size_bytes: int
    sha256: str | None
    valid: bool
    below_minimum: bool
    error: str | None = None


@dataclass(frozen=True)
class DatasetReport:
    directory: str
    total: int
    valid: int
    broken: int
    below_minimum: int
    minimum_size: int
    records: tuple[ImageRecord, ...]
    include_subfolders: bool = False

    @property
    def can_train(self) -> bool:
        return self.valid > 0 and self.broken == 0

    def to_dict(self) -> dict:
        return {
            "directory": self.directory,
            "total": self.total,
            "valid": self.valid,
            "broken": self.broken,
            "below_minimum": self.below_minimum,
            "minimum_size": self.minimum_size,
            "include_subfolders": self.include_subfolders,
            "can_train": self.can_train,
            "records": [asdict(record) for record in self.records],
        }

    def to_markdown(self) -> str:
        status = "学習可能" if self.can_train else "要確認"
        lines = [
            f"### 画像検査：{status}",
            "",
            f"- フォルダ：`{self.directory}`",
            f"- サブフォルダ：{'含む' if self.include_subfolders else '含まない'}",
            f"- 対象画像：{self.total}枚",
            f"- Valid：{self.valid}",
            f"- Broken：{self.broken}",
            f"- {self.minimum_size}px未満：{self.below_minimum}",
        ]
        problems = [record for record in self.records if not record.valid]
        if problems:
            lines.extend(["", "#### 読み込めない画像"])
            lines.extend(
                f"- `{record.relative_path}`：{record.error}" for record in problems
            )
        small = [record for record in self.records if record.below_minimum]
        if small:
            lines.extend(["", "#### 解像度警告"])
            lines.extend(
                f"- `{record.relative_path}`：{record.width}×{record.height}"
                for record in small
            )
        return "\n".join(lines)


def list_training_images(directory: str | Path, include_subfolders: bool = False) -> tuple[Path, ...]:
    """List supported image files within the dataset, without following symlink escapes."""
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"学習画像フォルダが見つかりません: {root}")
    iterator = root.rglob("*") if include_subfolders else root.iterdir()
    paths = []
    for path in iterator:
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            continue
        paths.append(path)
    return tuple(sorted(paths, key=lambda p: p.relative_to(root).as_posix().casefold()))


def inspect_dataset(
    directory: str | Path, minimum_size: int = 512, include_hashes: bool = True,
    include_subfolders: bool = False,
) -> DatasetReport:
    root = Path(directory).expanduser()
    if not root.is_dir():
        raise ValueError(f"学習画像フォルダが見つかりません: {root}")

    files = list_training_images(root, include_subfolders)
    if not files:
        raise ValueError(f"対応する学習画像がありません: {root}")

    records: list[ImageRecord] = []
    for path in files:
        width: int | None = None
        height: int | None = None
        try:
            with Image.open(path) as image:
                width, height = image.size
                image.verify()
            below = min(width, height) < minimum_size
            records.append(
                ImageRecord(
                    relative_path=path.relative_to(root).as_posix(),
                    width=width,
                    height=height,
                    size_bytes=path.stat().st_size,
                    sha256=sha256_file(path) if include_hashes else None,
                    valid=True,
                    below_minimum=below,
                )
            )
        except Exception as error:  # Pillow raises several format-specific errors.
            records.append(
                ImageRecord(
                    relative_path=path.relative_to(root).as_posix(),
                    width=width,
                    height=height,
                    size_bytes=path.stat().st_size,
                    sha256=None,
                    valid=False,
                    below_minimum=False,
                    error=str(error),
                )
            )

    valid = sum(record.valid for record in records)
    broken = len(records) - valid
    below_minimum = sum(record.below_minimum for record in records)
    return DatasetReport(
        directory=str(root.resolve()),
        total=len(records),
        valid=valid,
        broken=broken,
        below_minimum=below_minimum,
        minimum_size=minimum_size,
        records=tuple(records),
        include_subfolders=include_subfolders,
    )

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    target = Path(path)
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: str | Path, data: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        temporary.replace(target)
    except PermissionError:
        # Some Windows sandboxed temp locations reject os.replace even though
        # normal writes are allowed. Preserve usability with a direct-write
        # fallback; production experiment folders normally use the atomic path.
        target.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.unlink(missing_ok=True)
    return target


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def list_record_files(root: str | Path, limit: int = 30) -> list[Path]:
    directory = Path(root)
    if not directory.is_dir():
        return []
    files = list(directory.glob("**/*manifest*.json"))
    files.extend(directory.glob("**/*generation*.json"))
    unique = {path.resolve(): path for path in files}
    return sorted(
        unique.values(), key=lambda path: path.stat().st_mtime, reverse=True
    )[:limit]

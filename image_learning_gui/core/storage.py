from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .records import iso_now, sha256_file, write_json_atomic


ARCHIVE_FORMAT = "ai-mr-experiment-archive-v1"
ARCHIVE_MANIFEST = "archive_manifest.json"
INVALID_NAME = re.compile(r'[<>:"/\\|?*]')


@dataclass(frozen=True)
class ArchiveReport:
    archive_dir: Path
    experiment_name: str
    file_count: int
    total_bytes: int
    valid: bool
    problems: tuple[str, ...]
    dataset_dir: Path | None = None
    training_output_dir: Path | None = None
    generated_dir: Path | None = None

    def to_markdown(self, heading: str = "保存データ検査") -> str:
        icon = "✅" if self.valid else "❌"
        lines = [
            f"### {icon} {heading}",
            "",
            f"- 実験名：`{self.experiment_name}`",
            f"- 保存場所：`{self.archive_dir}`",
            f"- ファイル数：{self.file_count}",
            f"- 合計容量：{self.total_bytes / (1024 ** 3):.2f} GiB",
            f"- 完全性：{'正常' if self.valid else '要確認'}",
        ]
        if self.problems:
            lines.extend(["", "#### 確認事項"])
            lines.extend(f"- {problem}" for problem in self.problems)
        return "\n".join(lines)


def validate_experiment_name(name: str) -> str:
    normalized = str(name).strip()
    if not normalized or normalized in {".", ".."}:
        raise ValueError("実験名を入力してください。")
    if INVALID_NAME.search(normalized) or normalized.endswith((".", " ")):
        raise ValueError("実験名にWindowsで使用できない文字が含まれています。")
    return normalized


def archive_destination(external_root: str | Path, experiment_name: str) -> Path:
    if not str(external_root or "").strip():
        raise ValueError("外部ストレージの保存先ルートを指定してください。")
    root = Path(external_root).expanduser().resolve()
    name = validate_experiment_name(experiment_name)
    return root / "AI_MR_Research" / "experiments" / name


def _ensure_source(path: str | Path, label: str, required: bool = True) -> Path | None:
    text = str(path or "").strip()
    if not text:
        if required:
            raise ValueError(f"{label}を指定してください。")
        return None
    candidate = Path(text).expanduser().resolve()
    if not candidate.is_dir():
        raise ValueError(f"{label}が見つかりません: {candidate}")
    return candidate


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _iter_files(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        linked_directories = [
            current_path / name
            for name in directories
            if (current_path / name).is_symlink()
        ]
        if linked_directories:
            raise ValueError(
                f"シンボリックリンクは保存できません: {linked_directories[0]}"
            )
        for name in files:
            path = current_path / name
            if path.is_symlink():
                raise ValueError(f"シンボリックリンクは保存できません: {path}")
            yield path


def _copy_tree(
    source: Path,
    destination: Path,
    *,
    exclude_checkpoints: bool = False,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for file_path in _iter_files(source):
        relative = file_path.relative_to(source)
        if exclude_checkpoints and any(
            part.lower().startswith("checkpoint-") for part in relative.parts
        ):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)


def _inventory(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(_iter_files(root), key=lambda item: item.as_posix().casefold()):
        if path.name == ARCHIVE_MANIFEST:
            continue
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def _commit_directory(temporary: Path, destination: Path) -> None:
    """Finalize a prepared directory, with a Windows sandbox fallback."""

    try:
        temporary.rename(destination)
        return
    except PermissionError:
        # Some Windows protected folders reject a directory rename even when
        # normal directory creation and copying are permitted.
        destination.mkdir(parents=False)
        marker = destination / ".copy_incomplete"
        marker.write_text("copy in progress\n", encoding="utf-8")
        _copy_tree(temporary, destination)
        marker.unlink()
        shutil.rmtree(temporary, ignore_errors=True)


def export_experiment(
    dataset_dir: str | Path,
    training_output_dir: str | Path,
    generated_dir: str | Path | None,
    external_root: str | Path,
    experiment_name: str,
    include_checkpoints: bool = False,
) -> ArchiveReport:
    dataset = _ensure_source(dataset_dir, "学習画像フォルダ")
    training_output = _ensure_source(training_output_dir, "学習結果フォルダ")
    generated = _ensure_source(generated_dir or "", "画像生成フォルダ", required=False)
    assert dataset is not None and training_output is not None

    destination = archive_destination(external_root, experiment_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError(f"同名の保存データが既にあります: {destination}")
    for source in (dataset, training_output, generated):
        if source and (_is_within(destination, source) or _is_within(source, destination)):
            raise ValueError("保存元と保存先を親子関係にしないでください。")

    temporary = destination.parent / f".{destination.name}.partial-{uuid.uuid4().hex}"
    temporary.mkdir(parents=False)
    try:
        _copy_tree(dataset, temporary / "dataset")
        _copy_tree(
            training_output,
            temporary / "training_output",
            exclude_checkpoints=not include_checkpoints,
        )
        if generated:
            _copy_tree(generated, temporary / "generated")

        readme = (
            "AI-MR experiment archive\n"
            f"Experiment: {destination.name}\n"
            f"Exported: {iso_now()}\n"
            f"Checkpoints included: {bool(include_checkpoints)}\n"
            "Use the AI image learning GUI to validate and restore this archive.\n"
        )
        (temporary / "README.txt").write_text(readme, encoding="utf-8")
        files = _inventory(temporary)
        manifest = {
            "format": ARCHIVE_FORMAT,
            "experiment_name": destination.name,
            "exported_at": iso_now(),
            "checkpoints_included": bool(include_checkpoints),
            "source_paths": {
                "dataset": str(dataset),
                "training_output": str(training_output),
                "generated": str(generated) if generated else None,
            },
            "file_count": len(files),
            "total_bytes": sum(int(item["size_bytes"]) for item in files),
            "files": files,
        }
        write_json_atomic(temporary / ARCHIVE_MANIFEST, manifest)
        _commit_directory(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return inspect_archive(destination)


def inspect_archive(archive_dir: str | Path) -> ArchiveReport:
    root = Path(archive_dir).expanduser().resolve()
    manifest_path = root / ARCHIVE_MANIFEST
    if not root.is_dir() or not manifest_path.is_file():
        raise ValueError(f"保存データのmanifestが見つかりません: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ValueError(f"保存データのmanifestを読めません: {error}") from error
    if manifest.get("format") != ARCHIVE_FORMAT:
        raise ValueError("対応していない保存データ形式です。")

    problems: list[str] = []
    records = manifest.get("files")
    if not isinstance(records, list):
        raise ValueError("保存データのファイル一覧が不正です。")
    expected_paths: set[str] = set()
    total_bytes = 0
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            problems.append("不正なファイル記録があります。")
            continue
        relative_text = record["path"]
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            problems.append(f"不正な相対パス: {relative_text}")
            continue
        expected_paths.add(relative.as_posix())
        candidate = (root / relative).resolve()
        if not _is_within(candidate, root) or not candidate.is_file():
            problems.append(f"不足ファイル: {relative_text}")
            continue
        actual_size = candidate.stat().st_size
        total_bytes += actual_size
        if actual_size != int(record.get("size_bytes", -1)):
            problems.append(f"容量不一致: {relative_text}")
            continue
        if sha256_file(candidate) != record.get("sha256"):
            problems.append(f"SHA-256不一致: {relative_text}")

    actual_paths = {
        path.relative_to(root).as_posix()
        for path in _iter_files(root)
        if path.name != ARCHIVE_MANIFEST
    }
    for unexpected in sorted(actual_paths - expected_paths):
        problems.append(f"manifestにないファイル: {unexpected}")

    return ArchiveReport(
        archive_dir=root,
        experiment_name=str(manifest.get("experiment_name") or root.name),
        file_count=len(records),
        total_bytes=total_bytes,
        valid=not problems,
        problems=tuple(problems),
        dataset_dir=(root / "dataset") if (root / "dataset").is_dir() else None,
        training_output_dir=(
            (root / "training_output")
            if (root / "training_output").is_dir()
            else None
        ),
        generated_dir=(root / "generated") if (root / "generated").is_dir() else None,
    )


def restore_experiment(archive_dir: str | Path, pc_root: str | Path) -> ArchiveReport:
    report = inspect_archive(archive_dir)
    if not report.valid:
        raise ValueError("保存データの完全性検査に失敗したため復元できません。")
    if not str(pc_root or "").strip():
        raise ValueError("PC側の復元先ルートを指定してください。")
    root = Path(pc_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / validate_experiment_name(report.experiment_name)
    if destination.exists():
        raise ValueError(f"同名の復元先が既にあります: {destination}")
    if _is_within(destination, report.archive_dir) or _is_within(
        report.archive_dir, destination
    ):
        raise ValueError("保存元と復元先を親子関係にしないでください。")

    temporary = root / f".{destination.name}.partial-{uuid.uuid4().hex}"
    try:
        _copy_tree(report.archive_dir, temporary)
        _commit_directory(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return inspect_archive(destination)

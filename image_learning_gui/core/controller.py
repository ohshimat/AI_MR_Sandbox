from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .captions import (
    cache_caption_thumbnail,
    caption_progress_markdown,
    list_caption_entries,
    save_image_caption,
)
from .config import save_user_settings
from .dataset import inspect_dataset
from .environment import inspect_environment
from .generation import GenerationRequest, GenerationService, LoraAdapter
from .process_manager import JobBusyError, ProcessManager
from .preview import cache_preview_image
from .records import list_record_files, read_json
from .storage import (
    export_experiment as export_experiment_archive,
    inspect_archive,
    restore_experiment as restore_experiment_archive,
)
from .training import (
    CAPTION_MODE_FIXED,
    TrainingRequest,
    TrainingService,
    calculate_resume_target_steps,
    calculate_training_steps,
    latest_checkpoint,
    list_checkpoints,
)


class AppController:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.jobs = ProcessManager()
        self.training = TrainingService(config, self.jobs)
        self.generation = GenerationService(config, self.jobs)
        self._preview_result_json: Path | None = None
        self._last_preview_path: str | None = None
        self._last_result_markdown = ""

    def environment_markdown(self) -> str:
        version = self.config.get("app", {}).get("version", "不明")
        gui_root = Path(__file__).resolve().parents[1]
        workspace_root = self.config.get("paths", {}).get(
            "workspace_root", "未設定"
        )
        settings_file = self.config.get("paths", {}).get(
            "user_settings_file", "未設定"
        )
        offline = bool(self.config.get("app", {}).get("offline", False))
        analytics = bool(
            self.config.get("app", {}).get("analytics_enabled", False)
        )
        gui_information = "\n".join(
            (
                "### GUI情報",
                "",
                f"- GUIバージョン：**v{version}**",
                f"- GUI本体：`{gui_root}`",
                f"- ユーザー作業領域：`{workspace_root}`",
                f"- ユーザー設定：`{settings_file}`",
                f"- オフライン実験モード：**{'有効' if offline else '無効'}**",
                f"- Gradio分析送信：**{'有効' if analytics else '無効'}**",
            )
        )
        return gui_information + "\n\n" + inspect_environment(self.config).to_markdown()

    def inspect_images(self, directory: str) -> str:
        try:
            report = inspect_dataset(
                directory,
                minimum_size=int(self.config["training"]["resolution"]),
                include_hashes=False,
            )
            self._save_settings(training_image_dir=directory)
            return report.to_markdown()
        except Exception as error:
            return self._error_markdown("学習画像を検査できません。", error)

    def inspect_training_plan(
        self,
        directory: str,
        repetitions: int | float,
        mode: str = "新規学習",
        resume_checkpoint: str = "",
    ) -> tuple[str, int, int, str]:
        try:
            report = inspect_dataset(
                directory,
                minimum_size=int(self.config["training"]["resolution"]),
                include_hashes=False,
            )
            count = report.valid
            additional_steps = self._calculate_steps(count, repetitions)
            target_steps = self._effective_target_steps(
                additional_steps, mode, resume_checkpoint
            )
            self._save_settings(
                training_image_dir=directory,
                training_repetitions=int(repetitions),
                additional_steps=additional_steps,
                target_steps=target_steps,
            )
            return (
                report.to_markdown(),
                count,
                target_steps,
                self._training_plan_markdown(
                    count,
                    int(repetitions),
                    additional_steps,
                    target_steps,
                    mode,
                    resume_checkpoint,
                ),
            )
        except (OSError, TypeError, ValueError) as error:
            return (
                self._error_markdown("学習画像を検査できません。", error),
                0,
                0,
                self._error_markdown("ステップ数を計算できません。", error),
            )

    def recalculate_training_plan(
        self,
        image_count: int | float,
        repetitions: int | float,
        mode: str = "新規学習",
        resume_checkpoint: str = "",
    ) -> tuple[int, str]:
        try:
            count = int(image_count)
            repeats = int(repetitions)
            additional_steps = self._calculate_steps(count, repeats)
            target_steps = self._effective_target_steps(
                additional_steps, mode, resume_checkpoint
            )
            self._save_settings(
                training_repetitions=repeats,
                additional_steps=additional_steps,
                target_steps=target_steps,
            )
            return target_steps, self._training_plan_markdown(
                count,
                repeats,
                additional_steps,
                target_steps,
                mode,
                resume_checkpoint,
            )
        except (TypeError, ValueError) as error:
            return 0, self._error_markdown("ステップ数を計算できません。", error)

    def checkpoint_markdown(self, output_dir: str) -> str:
        checkpoint, step = latest_checkpoint(output_dir)
        if checkpoint is None:
            return "### ⚠️ checkpoint\n\n`checkpoint-N`が見つかりません。"
        return (
            "### ✅ checkpoint\n\n"
            f"- 最新：`{checkpoint.name}`\n"
            f"- 現在ステップ：{step}\n"
            f"- フォルダ：`{Path(output_dir).expanduser()}`"
        )

    def checkpoint_choices(
        self, output_dir: str
    ) -> tuple[str, list[str], str | None]:
        checkpoints = list_checkpoints(output_dir)
        if not checkpoints:
            return (
                "### ⚠️ checkpoint\n\n`checkpoint-N`が見つかりません。",
                [],
                None,
            )
        choices = [path.name for path, _ in reversed(checkpoints)]
        latest_path, latest_step = checkpoints[-1]
        report = (
            "### ✅ checkpoint\n\n"
            f"- 検出数：{len(checkpoints)}件\n"
            f"- 最新：`{latest_path.name}`\n"
            f"- 現在ステップ：{latest_step}\n"
            f"- フォルダ：`{Path(output_dir).expanduser()}`"
        )
        return report, choices, latest_path.name

    def load_caption_browser(
        self, directory: str
    ) -> tuple[list[tuple[str, str]], str, str | None, str, str]:
        try:
            entries = list_caption_entries(directory)
            gallery = self._caption_gallery(entries)
            selected = entries[0]
            preview = cache_caption_thumbnail(
                selected.image_path, self.config["paths"]["preview_cache"]
            )
            return (
                gallery,
                str(selected.image_path),
                str(preview),
                selected.caption,
                caption_progress_markdown(entries, selected),
            )
        except (OSError, ValueError) as error:
            return [], "", None, "", self._error_markdown(
                "個別キャプション画像を読み込めません。", error
            )

    def select_caption_image(
        self, directory: str, index: int | tuple[int, ...]
    ) -> tuple[str, str | None, str, str]:
        try:
            entries = list_caption_entries(directory)
            selected_index = index[0] if isinstance(index, tuple) else index
            selected = entries[int(selected_index)]
            preview = cache_caption_thumbnail(
                selected.image_path, self.config["paths"]["preview_cache"]
            )
            return (
                str(selected.image_path),
                str(preview),
                selected.caption,
                caption_progress_markdown(entries, selected),
            )
        except (IndexError, OSError, TypeError, ValueError) as error:
            return "", None, "", self._error_markdown(
                "選択画像のキャプションを読み込めません。", error
            )

    def save_caption(
        self, directory: str, image_path: str, caption: str
    ) -> tuple[list[tuple[str, str]], str, str]:
        try:
            caption_path = save_image_caption(directory, image_path, caption)
            entries = list_caption_entries(directory)
            selected = next(
                entry for entry in entries if entry.image_path == Path(image_path).resolve()
            )
            report = caption_progress_markdown(entries, selected)
            report += f"\n\n✅ 保存しました：`{caption_path}`"
            return self._caption_gallery(entries), selected.caption, report
        except (OSError, StopIteration, ValueError) as error:
            try:
                gallery = self._caption_gallery(list_caption_entries(directory))
            except (OSError, ValueError):
                gallery = []
            return gallery, caption, self._error_markdown(
                "キャプションを保存できません。", error
            )

    def start_training(
        self,
        image_dir: str,
        mode: str,
        output_dir: str,
        resume_checkpoint: str,
        repetitions: int | float,
        prompt: str,
        caption_mode: str = CAPTION_MODE_FIXED,
    ) -> tuple[str, str]:
        try:
            report = inspect_dataset(
                image_dir,
                minimum_size=int(self.config["training"]["resolution"]),
                include_hashes=False,
            )
            additional_steps = self._calculate_steps(report.valid, repetitions)
            target_steps = self._effective_target_steps(
                additional_steps, mode, resume_checkpoint
            )
            request = TrainingRequest(
                image_dir=image_dir,
                mode=mode,
                output_dir=output_dir,
                target_steps=int(target_steps),
                instance_prompt=prompt,
                caption_mode=caption_mode,
                resume_checkpoint=resume_checkpoint or "",
            )
            snapshot = self.training.start(request)
            self._save_settings(
                training_image_dir=image_dir,
                training_output_dir=output_dir,
                training_prompt=prompt,
                training_caption_mode=caption_mode,
                training_resume_checkpoint=resume_checkpoint or "",
                training_repetitions=int(repetitions),
                additional_steps=int(additional_steps),
                target_steps=int(target_steps),
            )
            return self._status_markdown(snapshot), snapshot.log_tail
        except (TypeError, ValueError, OSError, JobBusyError) as error:
            return self._error_markdown("学習を開始できません。", error), self.jobs.snapshot().log_tail

    def start_generation(
        self,
        lora_path_1: str,
        strength_1: float,
        lora_path_2: str,
        strength_2: float,
        lora_path_3: str,
        strength_3: float,
        prompt: str,
        seed: int | float,
        width: int | float,
        height: int | float,
        output_dir: str,
    ) -> tuple[str, str]:
        try:
            adapter_inputs = (
                (lora_path_1, strength_1),
                (lora_path_2, strength_2),
                (lora_path_3, strength_3),
            )
            adapters = tuple(
                LoraAdapter(path=str(path).strip(), strength=float(strength))
                for path, strength in adapter_inputs
                if path is not None and str(path).strip()
            )
            request = GenerationRequest(
                loras=adapters,
                prompt=prompt,
                seed=int(seed),
                width=int(width),
                height=int(height),
                output_dir=output_dir,
            )
            snapshot = self.generation.start(request)
            self._save_settings(
                generation_lora=lora_path_1,
                lora_strength=float(strength_1),
                generation_lora_2=lora_path_2,
                lora_strength_2=float(strength_2),
                generation_lora_3=lora_path_3,
                lora_strength_3=float(strength_3),
                generation_prompt=prompt,
                generation_seed=int(seed),
                generation_width=int(width),
                generation_height=int(height),
                generation_output_dir=output_dir,
            )
            return self._status_markdown(snapshot), snapshot.log_tail
        except (TypeError, ValueError, OSError, JobBusyError) as error:
            return self._error_markdown("画像生成を開始できません。", error), self.jobs.snapshot().log_tail

    def stop(self) -> tuple[str, str]:
        snapshot = self.jobs.stop()
        return self._status_markdown(snapshot), snapshot.log_tail

    def export_experiment(
        self,
        image_dir: str,
        training_output_dir: str,
        generated_dir: str,
        external_root: str,
        experiment_name: str,
        include_checkpoints: bool,
    ) -> str:
        try:
            self._require_idle_for_storage()
            report = export_experiment_archive(
                dataset_dir=image_dir,
                training_output_dir=training_output_dir,
                generated_dir=generated_dir,
                external_root=external_root,
                experiment_name=experiment_name,
                include_checkpoints=bool(include_checkpoints),
            )
            self._save_settings(
                external_storage_root=external_root,
                archive_experiment_name=experiment_name,
            )
            return report.to_markdown("外部ストレージへの保存完了")
        except (OSError, TypeError, ValueError) as error:
            return self._error_markdown("実験を保存できません。", error)

    def inspect_experiment_archive(self, archive_dir: str) -> str:
        try:
            report = inspect_archive(archive_dir)
            self._save_settings(archive_path=archive_dir)
            return report.to_markdown()
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            return self._error_markdown("保存データを検査できません。", error)

    def restore_experiment(
        self,
        archive_dir: str,
        pc_root: str,
        current_dataset: str,
        current_training_output: str,
        current_generated: str,
    ) -> tuple[str, str, str, str]:
        try:
            self._require_idle_for_storage()
            report = restore_experiment_archive(archive_dir, pc_root)
            dataset = str(report.dataset_dir or "")
            training_output = str(report.training_output_dir or "")
            generated = str(report.generated_dir or "")
            self._save_settings(
                archive_path=archive_dir,
                restore_pc_root=pc_root,
                training_image_dir=dataset,
                training_output_dir=training_output,
                generation_output_dir=generated,
            )
            markdown = report.to_markdown("PCストレージへの復元完了")
            markdown += "\n\n学習・画像生成タブのフォルダ設定も更新しました。"
            return markdown, dataset, training_output, generated
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            return (
                self._error_markdown("実験を復元できません。", error),
                current_dataset,
                current_training_output,
                current_generated,
            )

    def poll(self) -> tuple[str, str, str | None, str, str]:
        snapshot = self.jobs.snapshot()
        result_json = self.generation.last_result_json
        if (
            snapshot.operation == "画像生成"
            and snapshot.state == "succeeded"
            and result_json is not None
            and result_json.is_file()
            and result_json != self._preview_result_json
        ):
            try:
                result = read_json(result_json)
                candidate = Path(result["image"])
                if candidate.is_file():
                    preview = cache_preview_image(
                        candidate, self.config["paths"]["preview_cache"]
                    )
                    self._last_preview_path = str(preview)
                    self._preview_result_json = result_json
                loras = result.get("loras") or [
                    {
                        "path": result.get("lora"),
                        "strength": result.get("lora_strength"),
                    }
                ]
                lora_lines = "\n".join(
                    f"- LoRA {index}：`{item.get('path')}`（係数 {item.get('strength')}）"
                    for index, item in enumerate(loras, start=1)
                )
                self._last_result_markdown = (
                    "### 生成結果\n\n"
                    f"- 画像：`{result.get('image')}`\n"
                    f"{lora_lines}\n"
                    f"- seed：{result.get('seed')}\n"
                    f"- 解像度：{result.get('width')} × {result.get('height')}\n"
                    f"- 記録：`{result.get('sidecar_json')}`"
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                self._last_result_markdown = self._error_markdown(
                    "生成結果を読めません。", error
                )
        return (
            self._status_markdown(snapshot),
            snapshot.log_tail,
            self._last_preview_path,
            self._last_result_markdown,
            self.history_markdown(),
        )

    def lora_choices(self) -> list[str]:
        root = Path(self.config["paths"]["lora_root"])
        if not root.is_dir():
            return []
        return [str(path.resolve()) for path in sorted(root.glob("**/*.safetensors"))]

    def history_markdown(self) -> str:
        roots = [
            self.config["paths"]["records_root"],
            self.config["paths"]["lora_root"],
            self.config["paths"]["generated_root"],
        ]
        files: list[Path] = []
        for root in roots:
            files.extend(list_record_files(root, limit=20))
        unique = sorted(
            {path.resolve(): path for path in files}.values(),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )[:30]
        if not unique:
            return "### 実行履歴\n\nまだGUIの実行記録はありません。"
        lines = ["### 実行履歴", ""]
        for path in unique:
            try:
                data = read_json(path)
                status = data.get("status", "unknown")
                operation = data.get("operation", "record")
                when = data.get("finished_at") or data.get("generated_at") or ""
                lines.append(f"- **{operation} / {status}** {when}  ")
                lines.append(f"  `{path}`")
            except (OSError, json.JSONDecodeError):
                continue
        return "\n".join(lines)

    def _save_settings(self, **changes: Any) -> None:
        allowed = set(self.config.get("ui_defaults", {}))
        current_path = Path(self.config["paths"]["user_settings_file"])
        current: dict[str, Any] = {}
        if current_path.is_file():
            try:
                current = json.loads(current_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                current = {}
        current.update({key: value for key, value in changes.items() if key in allowed})
        save_user_settings(self.config, current)

    def _require_idle_for_storage(self) -> None:
        snapshot = self.jobs.snapshot()
        if snapshot.state in {"starting", "running", "stopping"}:
            raise ValueError(
                "学習または画像生成の実行中は保存・復元できません。完了後に実行してください。"
            )

    def _caption_gallery(self, entries) -> list[tuple[str, str]]:
        gallery: list[tuple[str, str]] = []
        for entry in entries:
            thumbnail = cache_caption_thumbnail(
                entry.image_path, self.config["paths"]["preview_cache"]
            )
            status = "✓ 保存済み" if entry.has_caption else "○ 未入力"
            gallery.append((str(thumbnail), f"{entry.image_path.name}｜{status}"))
        return gallery

    def _calculate_steps(self, image_count: int, repetitions: int | float) -> int:
        fixed = self.config["training"]
        return calculate_training_steps(
            image_count=int(image_count),
            repetitions_per_image=int(repetitions),
            train_batch_size=int(fixed["train_batch_size"]),
            gradient_accumulation_steps=int(fixed["gradient_accumulation_steps"]),
            num_processes=1,
        )

    def _effective_target_steps(
        self, additional_steps: int, mode: str, resume_checkpoint: str
    ) -> int:
        if mode == "checkpointから継続":
            if not str(resume_checkpoint or "").strip():
                return int(additional_steps)
            return calculate_resume_target_steps(additional_steps, resume_checkpoint)
        return int(additional_steps)

    def _training_plan_markdown(
        self,
        image_count: int,
        repetitions: int,
        additional_steps: int,
        target_steps: int,
        mode: str,
        resume_checkpoint: str,
    ) -> str:
        fixed = self.config["training"]
        batch = int(fixed["train_batch_size"])
        accumulation = int(fixed["gradient_accumulation_steps"])
        lines = [
            "### 学習量の計算\n\n"
            f"- 学習画像数：{image_count}枚\n"
            f"- 1画像あたりの総学習回数：{repetitions}回\n"
            f"- batch size：{batch}\n"
            f"- gradient accumulation：{accumulation}\n"
            f"- 計算された追加ステップ：{additional_steps}\n"
        ]
        if mode == "checkpointから継続" and str(resume_checkpoint or "").strip():
            checkpoint_step = target_steps - additional_steps
            lines.append(
                f"- 継続計算：{checkpoint_step}＋{additional_steps}＝{target_steps}\n"
            )
        elif mode == "checkpointから継続":
            lines.append("- 継続元checkpointを選択すると最終目標を計算します。\n")
        lines.extend(
            [
            f"- **適用する最終目標ステップ：{target_steps}**\n\n",
            "計算式：`ceil(画像数 × 学習回数 ÷ "
            "(batch size × gradient accumulation))`",
            ]
        )
        return "".join(lines)

    @staticmethod
    def _status_markdown(snapshot) -> str:
        icons = {
            "idle": "✅",
            "starting": "⏳",
            "running": "🟡",
            "stopping": "🟠",
            "succeeded": "✅",
            "stopped": "⚠️",
            "failed": "❌",
        }
        icon = icons.get(snapshot.state, "ℹ️")
        return (
            f"## {icon} {snapshot.message}\n\n"
            f"状態：`{snapshot.state}`  \n"
            f"処理：`{snapshot.operation or 'なし'}`  \n"
            f"Job ID：`{snapshot.job_id or 'なし'}`"
        )

    @staticmethod
    def _error_markdown(summary: str, error: Exception) -> str:
        return (
            f"## ❌ {summary}\n\n"
            f"確認：入力したパスと値を見直してください。  \n"
            f"詳細：`{type(error).__name__}: {error}`"
        )

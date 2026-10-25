from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.dataset import inspect_dataset
from core.training import (
    CAPTION_MODE_PER_IMAGE,
    TrainingRequest,
    build_training_command,
    calculate_resume_target_steps,
    calculate_training_steps,
    infer_trigger,
    latest_checkpoint,
    list_checkpoints,
    named_lora_path,
    stage_training_images,
    stage_training_dataset,
    validate_training_request,
)


def make_test_config() -> dict:
    return {
        "paths": {
            "accelerate_executable": r"C:\venv\accelerate.exe",
            "training_script": r"E:\vendor\train.py",
        },
        "training": {
            "resolution": 512,
            "train_batch_size": 1,
            "gradient_accumulation_steps": 1,
            "learning_rate": 1e-4,
            "lr_scheduler": "constant",
            "lr_warmup_steps": 0,
            "checkpointing_steps": 100,
            "checkpoints_total_limit": 7,
            "mixed_precision": "fp16",
            "rank": 8,
            "dataloader_num_workers": 0,
            "report_to": "tensorboard",
            "seed": 42,
            "variant": "fp16",
        },
    }


class TrainingTests(unittest.TestCase):
    def test_calculates_steps_from_images_and_repetitions(self) -> None:
        self.assertEqual(calculate_training_steps(20, 30), 600)
        self.assertEqual(calculate_training_steps(15, 30), 450)

    def test_calculation_accounts_for_batch_and_accumulation(self) -> None:
        self.assertEqual(
            calculate_training_steps(
                20,
                30,
                train_batch_size=2,
                gradient_accumulation_steps=2,
            ),
            150,
        )

    def test_calculation_rejects_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "1以上"):
            calculate_training_steps(0, 30)

    def test_resume_target_adds_checkpoint_and_additional_steps(self) -> None:
        self.assertEqual(
            calculate_resume_target_steps(390, "checkpoint-600"),
            990,
        )

    def test_resume_target_requires_checkpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            calculate_resume_target_steps(390, "")

    def test_latest_checkpoint_uses_highest_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("checkpoint-100", "checkpoint-old", "checkpoint-600", "checkpoint-400"):
                (root / name).mkdir()
            path, step = latest_checkpoint(root)
            self.assertEqual(step, 600)
            self.assertEqual(path.name, "checkpoint-600")

    def test_trigger_and_named_lora(self) -> None:
        prompt = "a photo of aimrps01 person wearing a powered suit"
        self.assertEqual(infer_trigger(prompt), "aimrps01")
        self.assertEqual(
            named_lora_path("C:/out", prompt, 600).name,
            "aimrps01_sdxl_lora_step600.safetensors",
        )

    def test_resume_command_contains_fixed_arguments(self) -> None:
        request = TrainingRequest(
            image_dir=r"C:\data with spaces\images",
            mode="checkpointから継続",
            output_dir=r"C:\output with spaces",
            target_steps=600,
            instance_prompt="a photo of aimrps01 person",
            resume_checkpoint="checkpoint-400",
        )
        command = build_training_command(request, make_test_config(), r"C:\model")
        self.assertEqual(command[0], r"C:\venv\accelerate.exe")
        self.assertIn("--variant=fp16", command)
        self.assertIn("--resolution=512", command)
        self.assertIn("--rank=8", command)
        self.assertIn("--report_to=tensorboard", command)
        self.assertIn("--resume_from_checkpoint=checkpoint-400", command)
        self.assertTrue(any("data with spaces" in argument for argument in command))

    def test_new_training_rejects_nonempty_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            output = root / "output"
            images.mkdir()
            output.mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            (output / "existing.txt").write_text("keep", encoding="utf-8")
            request = TrainingRequest(
                image_dir=str(images),
                mode="新規学習",
                output_dir=str(output),
                target_steps=1,
                instance_prompt="a photo of aimrps01 person",
            )
            with self.assertRaisesRegex(ValueError, "空ではありません"):
                validate_training_request(request, make_test_config())

    def test_resume_requires_higher_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            output = root / "output"
            images.mkdir()
            output.mkdir()
            (output / "checkpoint-600").mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            request = TrainingRequest(
                image_dir=str(images),
                mode="checkpointから継続",
                output_dir=str(output),
                target_steps=600,
                instance_prompt="a photo of aimrps01 person",
                resume_checkpoint="checkpoint-600",
            )
            with self.assertRaisesRegex(ValueError, "より大きく"):
                validate_training_request(request, make_test_config())

    def test_resume_requires_explicit_checkpoint_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            output = root / "output"
            images.mkdir()
            output.mkdir()
            (output / "checkpoint-400").mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            request = TrainingRequest(
                image_dir=str(images),
                mode="checkpointから継続",
                output_dir=str(output),
                target_steps=600,
                instance_prompt="a photo of aimrps01 person",
            )
            with self.assertRaisesRegex(ValueError, "選択してください"):
                validate_training_request(request, make_test_config())

    def test_resume_rejects_older_checkpoint_when_newer_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            output = root / "output"
            images.mkdir()
            output.mkdir()
            (output / "checkpoint-400").mkdir()
            (output / "checkpoint-600").mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            request = TrainingRequest(
                image_dir=str(images),
                mode="checkpointから継続",
                output_dir=str(output),
                target_steps=800,
                instance_prompt="a photo of aimrps01 person",
                resume_checkpoint="checkpoint-400",
            )
            with self.assertRaisesRegex(ValueError, "最新checkpoint"):
                validate_training_request(request, make_test_config())

    def test_staging_directory_contains_only_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            (images / "one.txt").write_text("caption", encoding="utf-8")

            report = inspect_dataset(images)
            staged = stage_training_images(report, root / "records", "train-test")

            self.assertEqual([path.name for path in staged.iterdir()], ["one.png"])

    def test_command_can_use_image_only_staging_directory(self) -> None:
        request = TrainingRequest(
            image_dir=r"C:\source\images",
            mode="新規学習",
            output_dir=r"C:\output",
            target_steps=600,
            instance_prompt="a photo of aimrps01 person",
        )
        command = build_training_command(
            request,
            make_test_config(),
            r"C:\model",
            instance_data_dir=r"C:\records\training_images\train-test",
        )

        self.assertIn(
            r"--instance_data_dir=C:\records\training_images\train-test", command
        )
        self.assertFalse(any(r"C:\source\images" in argument for argument in command))

    def test_caption_dataset_creates_imagefolder_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            Image.new("RGB", (512, 512), "black").save(images / "two.jpg")
            (images / "one.txt").write_text(
                "a photo of aimrperson01 person\n", encoding="utf-8"
            )
            (images / "two.txt").write_text(
                "a full-body photo of aimrperson01 person\n", encoding="utf-8"
            )

            report = inspect_dataset(images)
            staged = stage_training_dataset(
                report,
                root / "records",
                "caption-test",
                caption_mode=CAPTION_MODE_PER_IMAGE,
            )

            lines = (staged / "metadata.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn('"file_name": "one.png"', lines[0])
            self.assertIn('"prompt": "a photo of aimrperson01 person"', lines[0])
            self.assertEqual(
                sorted(path.name for path in staged.iterdir()),
                ["metadata.jsonl", "one.png", "two.jpg"],
            )

    def test_caption_dataset_uses_common_prompt_when_caption_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            report = inspect_dataset(images)
            staged = stage_training_dataset(
                report,
                root / "records",
                "caption-fallback",
                caption_mode=CAPTION_MODE_PER_IMAGE,
                instance_prompt="a photo of aimrperson01 person",
            )

            line = (staged / "metadata.jsonl").read_text(encoding="utf-8").strip()
            self.assertIn('"file_name": "one.png"', line)
            self.assertIn('"prompt": "a photo of aimrperson01 person"', line)

    def test_caption_dataset_requires_common_prompt_for_missing_caption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            Image.new("RGB", (512, 512), "white").save(images / "one.png")
            report = inspect_dataset(images)
            with self.assertRaisesRegex(ValueError, "共通プロンプト"):
                stage_training_dataset(
                    report,
                    root / "records",
                    "caption-missing-common",
                    caption_mode=CAPTION_MODE_PER_IMAGE,
                )

    def test_caption_training_command_uses_dataset_and_caption_column(self) -> None:
        request = TrainingRequest(
            image_dir=r"C:\source\images",
            mode="新規学習",
            output_dir=r"C:\output",
            target_steps=600,
            instance_prompt="a photo of aimrperson01 person",
            caption_mode=CAPTION_MODE_PER_IMAGE,
        )
        command = build_training_command(
            request,
            make_test_config(),
            r"C:\model",
            instance_data_dir=r"C:\records\training_images\train-test",
        )

        self.assertIn(
            r"--dataset_name=C:\records\training_images\train-test", command
        )
        self.assertIn("--caption_column=prompt", command)
        self.assertTrue(any(item.startswith("--cache_dir=") for item in command))
        self.assertFalse(any(item.startswith("--instance_data_dir=") for item in command))


if __name__ == "__main__":
    unittest.main()

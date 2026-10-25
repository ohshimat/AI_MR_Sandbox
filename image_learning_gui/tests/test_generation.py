from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.generation import (
    GenerationRequest,
    GenerationService,
    LoraAdapter,
    validate_generation_request,
)
from core.process_manager import JobSnapshot
from workers.generate_image import parse_args


class _CapturingJobs:
    def __init__(self) -> None:
        self.arguments = None

    def start(self, **kwargs):
        self.arguments = kwargs
        return JobSnapshot(
            job_id=kwargs["job_id"],
            operation=kwargs["operation"],
            state="running",
            started_at=None,
            finished_at=None,
            return_code=None,
            log_path=str(kwargs["log_path"]),
            message="running",
            log_tail="",
        )


class GenerationRequestTests(unittest.TestCase):
    def valid_request(self, root: Path) -> GenerationRequest:
        lora = root / "model.safetensors"
        lora.write_bytes(b"test")
        return GenerationRequest(
            loras=(LoraAdapter(path=str(lora), strength=1.0),),
            prompt="a photo of aimrps01 person",
            seed=42,
            width=512,
            height=768,
            output_dir=str(root / "output"),
        )

    def test_valid_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            validate_generation_request(self.valid_request(Path(directory)))

    def test_missing_lora(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = GenerationRequest(
                loras=(
                    LoraAdapter(
                        path=str(Path(directory) / "missing.safetensors"),
                        strength=1.0,
                    ),
                ),
                prompt="prompt",
                seed=42,
                width=512,
                height=512,
                output_dir=str(Path(directory) / "output"),
            )
            with self.assertRaisesRegex(ValueError, "見つかりません"):
                validate_generation_request(request)

    def test_strength_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = self.valid_request(Path(directory))
            invalid = GenerationRequest(
                **{
                    **request.__dict__,
                    "loras": (
                        LoraAdapter(path=request.loras[0].path, strength=2.1),
                    ),
                }
            )
            with self.assertRaisesRegex(ValueError, "0.0～2.0"):
                validate_generation_request(invalid)

    def test_multiple_loras(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "person.safetensors"
            second = root / "suit.safetensors"
            first.write_bytes(b"person")
            second.write_bytes(b"suit")
            request = GenerationRequest(
                **{
                    **self.valid_request(root).__dict__,
                    "loras": (
                        LoraAdapter(path=str(first), strength=0.8),
                        LoraAdapter(path=str(second), strength=0.6),
                    ),
                }
            )
            validate_generation_request(request)

    def test_at_least_one_lora_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = GenerationRequest(
                **{**self.valid_request(Path(directory)).__dict__, "loras": ()}
            )
            with self.assertRaisesRegex(ValueError, "1つ以上"):
                validate_generation_request(request)

    def test_duplicate_lora_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = self.valid_request(Path(directory))
            duplicate = GenerationRequest(
                **{
                    **request.__dict__,
                    "loras": (request.loras[0], request.loras[0]),
                }
            )
            with self.assertRaisesRegex(ValueError, "同じLoRA"):
                validate_generation_request(duplicate)

    def test_generation_service_passes_all_loras_and_strengths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "snapshots" / "model"
            model.mkdir(parents=True)
            (model / "model_index.json").write_text("{}", encoding="utf-8")
            first = root / "person.safetensors"
            second = root / "suit.safetensors"
            first.write_bytes(b"person")
            second.write_bytes(b"suit")
            jobs = _CapturingJobs()
            service = GenerationService(
                {
                    "paths": {
                        "model_snapshot_root": str(root / "snapshots"),
                        "python_executable": "python.exe",
                        "generation_worker": str(root / "generate_image.py"),
                    },
                    "generation": {
                        "negative_prompt": "bad",
                        "steps": 30,
                        "guidance_scale": 7.0,
                    },
                },
                jobs,
            )
            request = GenerationRequest(
                loras=(
                    LoraAdapter(str(first), 0.8),
                    LoraAdapter(str(second), 0.6),
                ),
                prompt="person wearing suit",
                seed=42,
                width=512,
                height=512,
                output_dir=str(root / "output"),
            )
            service.start(request)
            command = jobs.arguments["command"]
            self.assertEqual(2, sum(item.startswith("--lora=") for item in command))
            self.assertIn("--strength=0.8", command)
            self.assertIn("--strength=0.6", command)

    def test_worker_accepts_repeated_lora_arguments(self) -> None:
        arguments = [
            "generate_image.py",
            "--model-dir=model",
            "--lora=person.safetensors",
            "--strength=0.8",
            "--lora=suit.safetensors",
            "--strength=0.6",
            "--prompt=test",
            "--negative-prompt=bad",
            "--seed=42",
            "--width=512",
            "--height=512",
            "--steps=30",
            "--guidance=7.0",
            "--output-dir=output",
            "--result-json=result.json",
        ]
        with patch("sys.argv", arguments):
            parsed = parse_args()
        self.assertEqual(
            ["person.safetensors", "suit.safetensors"], parsed.lora
        )
        self.assertEqual([0.8, 0.6], parsed.strength)

    def test_blank_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = self.valid_request(Path(directory))
            invalid = GenerationRequest(**{**request.__dict__, "prompt": "   "})
            with self.assertRaisesRegex(ValueError, "プロンプト"):
                validate_generation_request(invalid)

    def test_resolution_must_be_multiple_of_eight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = self.valid_request(Path(directory))
            invalid = GenerationRequest(**{**request.__dict__, "width": 513})
            with self.assertRaisesRegex(ValueError, "8の倍数"):
                validate_generation_request(invalid)

    def test_resolution_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = self.valid_request(Path(directory))
            invalid = GenerationRequest(**{**request.__dict__, "height": 128})
            with self.assertRaisesRegex(ValueError, "256～2048"):
                validate_generation_request(invalid)


if __name__ == "__main__":
    unittest.main()

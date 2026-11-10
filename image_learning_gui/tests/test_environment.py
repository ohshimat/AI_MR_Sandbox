from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import load_config
from core.environment import inspect_environment, resolve_model_dir


class ModelPathTests(unittest.TestCase):
    def make_model(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        (root / "model_index.json").write_text("{}", encoding="utf-8")
        return root.resolve()

    def test_direct_model_takes_priority_over_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_model(root / "revision")
            direct = self.make_model(root)
            self.assertEqual(resolve_model_dir(root), direct)

    def test_legacy_snapshots_select_newest_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "snapshots"
            old = self.make_model(root / "old")
            new = self.make_model(root / "new")
            os.utime(old / "model_index.json", (100, 100))
            os.utime(new / "model_index.json", (200, 200))
            self.assertEqual(resolve_model_dir(root), new)

    def test_invalid_model_paths_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "file"
            file.write_text("{}", encoding="utf-8")
            (root / "model_index.json").mkdir()
            for value in ("", str(root), str(file), str(root / "missing")):
                with self.subTest(value=value):
                    self.assertIsNone(resolve_model_dir(value))

    def inspect(self, config):
        with patch("core.environment._python_environment", return_value={"cuda_available": True}), patch("core.environment._nvidia_memory", return_value=(None, None, None)), patch("core.environment._disk_free", return_value=None):
            return inspect_environment(config)

    def test_explicit_path_overrides_valid_default_and_is_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_model(root / "models" / "huggingface" / "models--stabilityai--stable-diffusion-xl-base-1.0" / "snapshots" / "revision")
            explicit = self.make_model(root / "explicit")
            with patch.dict(os.environ, {"AI_MR_COMMON_ROOT": str(root), "AI_MR_SDXL_MODEL_PATH": str(explicit)}):
                config = load_config()
            self.assertEqual(config["paths"]["model_snapshot_root"], str(explicit))
            executable = root / "executable"
            executable.touch()
            for key in ("python_executable", "accelerate_executable", "training_script"):
                config["paths"][key] = str(executable)
            report = self.inspect(config)
            self.assertEqual(report.model_dir, str(explicit))
            self.assertTrue(report.ready)
            self.assertEqual(report.errors, ())

    def test_invalid_explicit_path_never_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_model(root / "models" / "huggingface" / "models--stabilityai--stable-diffusion-xl-base-1.0" / "snapshots" / "revision")
            empty = root / "empty"
            empty.mkdir()
            for value in (str(root / "missing"), str(empty), ""):
                with self.subTest(value=value), patch.dict(os.environ, {"AI_MR_COMMON_ROOT": str(root), "AI_MR_SDXL_MODEL_PATH": value}):
                    config = load_config()
                    report = self.inspect(config)
                    self.assertEqual(config["paths"]["model_snapshot_root"], value)
                    self.assertIsNone(report.model_dir)
                    self.assertFalse(report.ready)
                    self.assertFalse(report.path_status["SDXLモデルパス"])
                    self.assertIn(repr(value), report.to_markdown())

    def test_unset_override_preserves_legacy_config(self):
        with patch.dict(os.environ):
            os.environ.pop("AI_MR_SDXL_MODEL_PATH", None)
            os.environ["AI_MR_COMMON_ROOT"] = str(Path(tempfile.gettempdir()) / "common")
            config = load_config()
            self.assertEqual(Path(config["paths"]["model_snapshot_root"]), Path(os.environ["AI_MR_COMMON_ROOT"]) / "models" / "huggingface" / "models--stabilityai--stable-diffusion-xl-base-1.0" / "snapshots")

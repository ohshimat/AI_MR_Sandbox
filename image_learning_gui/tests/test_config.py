from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import PROJECT_ROOT, load_config


class ConfigurationTests(unittest.TestCase):
    def test_training_script_is_project_relative_and_present(self) -> None:
        config = load_config()
        expected = (
            PROJECT_ROOT
            / "vendor"
            / "diffusers-0.41.0"
            / "examples"
            / "dreambooth"
            / "train_dreambooth_lora_sdxl.py"
        ).resolve()
        self.assertEqual(config["paths"]["training_script"], str(expected))
        self.assertTrue(expected.is_file())

    def test_user_workspace_paths_expand_for_the_current_account(self) -> None:
        config = load_config()
        workspace = Path.home() / "AI_MR_Workspace"
        self.assertEqual(config["paths"]["workspace_root"], str(workspace))
        self.assertEqual(
            config["paths"]["user_settings_file"],
            str(workspace / "gui_state" / "user_settings.json"),
        )
        self.assertEqual(
            config["ui_defaults"]["training_image_dir"],
            str(workspace / "training" / "instance_images"),
        )

    def test_pc_resources_can_be_overridden_without_changing_portable_source(
        self,
    ) -> None:
        overrides = {
            "AI_MR_COMMON_ROOT": r"X:\AI_MR_Common",
            "AI_MR_WORKSPACE": r"Y:\Research_Workspace",
            "AI_MR_IMAGE_PYTHON": r"X:\Python\python.exe",
            "AI_MR_IMAGE_ACCELERATE": r"X:\Python\accelerate.exe",
            "AI_MR_TRAINING_PACKAGES": r"X:\Runtime\training",
        }
        with patch.dict(os.environ, overrides, clear=False):
            config = load_config()

        self.assertEqual(
            config["paths"]["python_executable"], overrides["AI_MR_IMAGE_PYTHON"]
        )
        self.assertEqual(
            config["paths"]["model_snapshot_root"],
            r"X:\AI_MR_Common\models\huggingface\models--stabilityai--stable-diffusion-xl-base-1.0\snapshots",
        )
        self.assertEqual(
            config["paths"]["training_packages"],
            overrides["AI_MR_TRAINING_PACKAGES"],
        )
        self.assertEqual(
            config["paths"]["workspace_root"], overrides["AI_MR_WORKSPACE"]
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()

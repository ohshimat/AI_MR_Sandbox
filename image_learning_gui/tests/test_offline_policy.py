from __future__ import annotations

import os
import unittest

import app
from core.config import load_config


class OfflinePolicyTests(unittest.TestCase):
    def test_offline_environment_is_enabled_by_importing_the_app(self) -> None:
        for name, expected in app.OFFLINE_ENVIRONMENT.items():
            self.assertEqual(os.environ.get(name), expected)

    def test_gradio_sharing_and_analytics_are_disabled(self) -> None:
        application = load_config()["app"]
        self.assertTrue(application["offline"])
        self.assertFalse(application["share"])
        self.assertFalse(application["analytics_enabled"])


if __name__ == "__main__":
    unittest.main()

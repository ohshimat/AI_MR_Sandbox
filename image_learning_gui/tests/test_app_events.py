from __future__ import annotations

import unittest

import gradio as gr
from gradio import utils

from app import create_caption_select_handler, generation_is_waiting


class _Controller:
    def select_caption_image(self, directory, index):
        return directory, index


class _Jobs:
    def __init__(self, operation, state):
        self._snapshot = type(
            "Snapshot", (), {"operation": operation, "state": state}
        )()

    def snapshot(self):
        return self._snapshot


class _WaitingController:
    def __init__(self, operation, state):
        self.jobs = _Jobs(operation, state)


class AppEventTests(unittest.TestCase):
    def test_caption_select_event_has_runtime_select_data_annotation(self) -> None:
        handler = create_caption_select_handler(_Controller(), gr.SelectData)
        hints = utils.get_type_hints(handler)

        self.assertIs(hints["evt"], gr.SelectData)
        self.assertEqual(handler("dataset", type("Event", (), {"index": 3})()), ("dataset", 3))

    def test_generation_wait_effect_is_visible_while_generating(self) -> None:
        self.assertTrue(generation_is_waiting(_WaitingController("画像生成", "running")))
        self.assertTrue(generation_is_waiting(_WaitingController("画像生成", "stopping")))

    def test_generation_wait_effect_is_hidden_after_completion(self) -> None:
        self.assertFalse(generation_is_waiting(_WaitingController("画像生成", "succeeded")))
        self.assertFalse(generation_is_waiting(_WaitingController("学習", "running")))


if __name__ == "__main__":
    unittest.main()

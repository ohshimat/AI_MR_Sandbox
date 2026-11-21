from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.captions import list_caption_entries, save_image_caption
from core.dataset import inspect_dataset
from core.training import CAPTION_MODE_PER_IMAGE, stage_training_dataset, stage_training_images


class RecursiveTrainingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "images"
        (self.root / "front").mkdir(parents=True)
        (self.root / "side" / "detail").mkdir(parents=True)
        for path in (self.root / "one.png", self.root / "front" / "one.png",
                     self.root / "side" / "detail" / "two.jpg"):
            Image.new("RGB", (512, 512), "white").save(path)

    def test_off_keeps_old_behavior_on_ordinary_folder(self):
        report = inspect_dataset(self.root, include_hashes=False)
        self.assertEqual(report.total, 1)
        self.assertEqual(report.records[0].relative_path, "one.png")
        self.assertFalse(report.include_subfolders)
        self.assertEqual(len(list_caption_entries(self.root)), 1)
        staged = stage_training_images(report, Path(self.directory.name) / "staging", "off")
        self.assertEqual([p.name for p in staged.iterdir()], ["one.png"])

    def test_on_recursively_stages_distinct_filenames(self):
        report = inspect_dataset(self.root, include_subfolders=True)
        self.assertEqual(report.total, 3)
        self.assertTrue(report.can_train)
        self.assertIn("side/detail/two.jpg", [r.relative_path for r in report.records])
        staged = stage_training_images(report, Path(self.directory.name) / "staging", "on")
        self.assertEqual(len(list(staged.iterdir())), 3)
        self.assertEqual(len(set(p.name.lower() for p in staged.iterdir())), 3)
        self.assertEqual(report.to_dict()["include_subfolders"], True)

    def test_recursive_captions_and_metadata(self):
        self.assertEqual(len(list_caption_entries(self.root, True)), 3)
        save_image_caption(self.root, self.root / "front" / "one.png", "front prompt", True)
        save_image_caption(self.root, self.root / "side" / "detail" / "two.jpg", "side prompt", True)
        with self.assertRaisesRegex(ValueError, "直下"):
            save_image_caption(self.root, self.root / "front" / "one.png", "blocked")
        report = inspect_dataset(self.root, include_subfolders=True)
        staged = stage_training_dataset(report, Path(self.directory.name) / "staging",
                                        "captions", CAPTION_MODE_PER_IMAGE,
                                        instance_prompt="fallback")
        rows = [json.loads(line) for line in (staged / "metadata.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["prompt"] for row in rows}, {"front prompt", "side prompt", "fallback"})
        self.assertTrue(all((staged / row["file_name"]).exists() for row in rows))

    def test_broken_nested_file_is_only_checked_when_enabled(self):
        (self.root / "front" / "bad.png").write_bytes(b"broken")
        self.assertTrue(inspect_dataset(self.root).can_train)
        report = inspect_dataset(self.root, include_subfolders=True)
        self.assertEqual(report.broken, 1)
        self.assertFalse(report.can_train)

    def test_recursive_does_not_escape_source_root(self):
        outside = Path(self.directory.name) / "outside.png"
        Image.new("RGB", (512, 512), "black").save(outside)
        link = self.root / "side" / "outside.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported")
        report = inspect_dataset(self.root, include_subfolders=True)
        self.assertEqual(report.total, 3)


if __name__ == "__main__":
    unittest.main()

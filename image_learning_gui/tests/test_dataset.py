from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.dataset import inspect_dataset


class DatasetTests(unittest.TestCase):
    def test_valid_images_and_uppercase_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("one.png", "two.JPG", "three.webp"):
                Image.new("RGB", (512, 512), "white").save(root / name)
            report = inspect_dataset(root)
            self.assertEqual(report.total, 3)
            self.assertEqual(report.valid, 3)
            self.assertEqual(report.broken, 0)
            self.assertEqual(report.below_minimum, 0)
            self.assertTrue(report.can_train)

    def test_small_image_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (511, 512), "white").save(root / "small.png")
            report = inspect_dataset(root)
            self.assertEqual(report.valid, 1)
            self.assertEqual(report.below_minimum, 1)
            self.assertTrue(report.can_train)

    def test_broken_image_prevents_training(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "broken.jpg").write_bytes(b"not an image")
            report = inspect_dataset(root)
            self.assertEqual(report.broken, 1)
            self.assertFalse(report.can_train)

    def test_empty_folder_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "対応する学習画像"):
                inspect_dataset(directory)

    def test_missing_folder_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "見つかりません"):
            inspect_dataset(Path(tempfile.gettempdir()) / "missing-sdxl-gui-test")


if __name__ == "__main__":
    unittest.main()

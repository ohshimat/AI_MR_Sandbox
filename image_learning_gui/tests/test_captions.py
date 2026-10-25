from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.captions import (
    cache_caption_thumbnail,
    list_caption_entries,
    save_image_caption,
)


class CaptionTests(unittest.TestCase):
    def test_saves_utf8_caption_next_to_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sample.png"
            Image.new("RGB", (64, 64), "blue").save(image)

            saved = save_image_caption(root, image, "人物がパワードスーツを着ている")

            self.assertEqual(saved, root / "sample.txt")
            self.assertEqual(
                saved.read_text(encoding="utf-8").strip(),
                "人物がパワードスーツを着ている",
            )

    def test_reads_existing_caption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sample.jpg"
            Image.new("RGB", (64, 64), "white").save(image)
            (root / "sample.txt").write_text("existing caption\n", encoding="utf-8")

            entries = list_caption_entries(root)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].caption, "existing caption")
            self.assertTrue(entries[0].has_caption)

    def test_rejects_empty_caption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sample.webp"
            Image.new("RGB", (64, 64), "white").save(image)
            with self.assertRaisesRegex(ValueError, "入力"):
                save_image_caption(root, image, "   ")

    def test_rejects_image_outside_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset"
            dataset.mkdir()
            outside = root / "outside.png"
            Image.new("RGB", (64, 64), "white").save(outside)
            with self.assertRaisesRegex(ValueError, "直下"):
                save_image_caption(dataset, outside, "caption")

    def test_detects_duplicate_stems(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (64, 64), "white").save(root / "same.png")
            Image.new("RGB", (64, 64), "white").save(root / "same.jpg")
            with self.assertRaisesRegex(ValueError, "衝突"):
                list_caption_entries(root)

    def test_creates_small_cached_thumbnail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "large.png"
            Image.new("RGB", (1000, 500), "green").save(image)

            thumbnail = cache_caption_thumbnail(image, root / "cache")

            self.assertTrue(thumbnail.is_file())
            with Image.open(thumbnail) as opened:
                self.assertLessEqual(opened.width, 384)
                self.assertLessEqual(opened.height, 384)


if __name__ == "__main__":
    unittest.main()

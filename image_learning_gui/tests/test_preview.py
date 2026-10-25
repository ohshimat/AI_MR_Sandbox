from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.preview import cache_preview_image


class PreviewTests(unittest.TestCase):
    def test_copies_image_to_preview_cache_with_stable_unique_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "outside" / "generated.png"
            source.parent.mkdir()
            Image.new("RGB", (32, 32), "blue").save(source)
            cache = root / "preview"

            first = cache_preview_image(source, cache)
            second = cache_preview_image(source, cache)

            self.assertTrue(first.is_file())
            self.assertEqual(first, second)
            self.assertEqual(first.parent, cache.resolve())
            self.assertIn("generated_", first.name)

    def test_rejects_non_image_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "not-image.txt"
            source.write_text("test", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "未対応"):
                cache_preview_image(source, root / "preview")


if __name__ == "__main__":
    unittest.main()

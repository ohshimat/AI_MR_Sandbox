from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from core.records import read_json, sha256_file, write_json_atomic


class RecordTests(unittest.TestCase):
    def test_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file.bin"
            path.write_bytes(b"abc")
            self.assertEqual(sha256_file(path), hashlib.sha256(b"abc").hexdigest())

    def test_json_round_trip_preserves_japanese(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            data = {"prompt": "研究室に立っている人物", "seed": 42}
            write_json_atomic(path, data)
            self.assertEqual(read_json(path), data)
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()

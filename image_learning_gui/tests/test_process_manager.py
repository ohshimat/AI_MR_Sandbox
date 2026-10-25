from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from core.process_manager import ProcessManager


class ProcessManagerTests(unittest.TestCase):
    def test_runs_child_and_captures_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "job.log"
            manager = ProcessManager()
            manager.start(
                job_id="test-job",
                operation="test",
                command=[sys.executable, "-c", "print('hello from child')"],
                cwd=root,
                environment=os.environ.copy(),
                log_path=log_path,
            )
            deadline = time.monotonic() + 10
            while manager.busy and time.monotonic() < deadline:
                time.sleep(0.05)
            snapshot = manager.snapshot()
            self.assertEqual(snapshot.state, "succeeded")
            self.assertEqual(snapshot.return_code, 0)
            self.assertIn("hello from child", snapshot.log_tail)
            self.assertIn("hello from child", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

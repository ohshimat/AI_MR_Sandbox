from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.storage import (
    archive_destination,
    export_experiment,
    inspect_archive,
    restore_experiment,
    validate_experiment_name,
)


class StorageTests(unittest.TestCase):
    def make_sources(self, root: Path) -> tuple[Path, Path, Path]:
        dataset = root / "source" / "dataset"
        output = root / "source" / "training"
        generated = root / "source" / "generated"
        dataset.mkdir(parents=True)
        output.mkdir(parents=True)
        generated.mkdir(parents=True)
        (dataset / "image_001.png").write_bytes(b"image")
        (dataset / "image_001.txt").write_text("caption\n", encoding="utf-8")
        (output / "model.safetensors").write_bytes(b"lora")
        (output / "train_manifest.json").write_text("{}", encoding="utf-8")
        checkpoint = output / "checkpoint-100"
        checkpoint.mkdir()
        (checkpoint / "state.bin").write_bytes(b"state")
        (generated / "sample.png").write_bytes(b"sample")
        return dataset, output, generated

    def test_validates_experiment_name(self) -> None:
        self.assertEqual(validate_experiment_name("experiment_001"), "experiment_001")
        with self.assertRaises(ValueError):
            validate_experiment_name("bad/name")
        with self.assertRaisesRegex(ValueError, "保存先ルート"):
            archive_destination("", "experiment_001")

    def test_export_without_checkpoints_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, output, generated = self.make_sources(root)
            report = export_experiment(
                dataset, output, generated, root / "external", "experiment_001"
            )
            self.assertTrue(report.valid)
            self.assertTrue((report.archive_dir / "dataset" / "image_001.txt").is_file())
            self.assertFalse(
                (report.archive_dir / "training_output" / "checkpoint-100").exists()
            )
            self.assertTrue((report.archive_dir / "archive_manifest.json").is_file())

    def test_export_with_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, output, generated = self.make_sources(root)
            report = export_experiment(
                dataset,
                output,
                generated,
                root / "external",
                "experiment_002",
                include_checkpoints=True,
            )
            self.assertTrue(
                (report.archive_dir / "training_output" / "checkpoint-100" / "state.bin").is_file()
            )

    def test_refuses_existing_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, output, generated = self.make_sources(root)
            args = (dataset, output, generated, root / "external", "experiment_003")
            export_experiment(*args)
            with self.assertRaisesRegex(ValueError, "既にあります"):
                export_experiment(*args)

    def test_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, output, generated = self.make_sources(root)
            report = export_experiment(
                dataset, output, generated, root / "external", "experiment_004"
            )
            (report.archive_dir / "dataset" / "image_001.txt").write_text(
                "changed", encoding="utf-8"
            )
            checked = inspect_archive(report.archive_dir)
            self.assertFalse(checked.valid)
            self.assertTrue(any("不一致" in problem for problem in checked.problems))

    def test_restore_preserves_verified_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset, output, generated = self.make_sources(root)
            exported = export_experiment(
                dataset, output, generated, root / "external", "experiment_005"
            )
            restored = restore_experiment(exported.archive_dir, root / "pc")
            self.assertTrue(restored.valid)
            self.assertTrue((restored.dataset_dir / "image_001.png").is_file())
            self.assertTrue(
                (restored.training_output_dir / "model.safetensors").is_file()
            )

    def test_destination_uses_stable_research_layout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            expected = (
                Path(directory).resolve()
                / "AI_MR_Research"
                / "experiments"
                / "experiment_006"
            )
            self.assertEqual(
                archive_destination(directory, "experiment_006"), expected
            )


if __name__ == "__main__":
    unittest.main()

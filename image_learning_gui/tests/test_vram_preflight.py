from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from core.config import load_config
from core.controller import AppController
from core.environment import EnvironmentNotReadyError, EnvironmentReport
from core.process_manager import JobSnapshot, ProcessManager
from core.training import TrainingRequest, TrainingService


def environment_report(used=1120, total=20470, cuda=True):
    return EnvironmentReport(
        python_executable=sys.executable, python_version='test', packages={},
        cuda_available=cuda, cuda_runtime='test', gpu_name='test GPU',
        torch_vram_allocated_mib=0, nvidia_used_mib=used, nvidia_total_mib=total,
        model_dir='model', path_status={'Python': True, 'SDXLモデルパス': True},
        disk_free_gib={}, errors=(),
    )


class VramPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.images = self.root / 'images'
        self.images.mkdir()
        Image.new('RGB', (512, 512)).save(self.images / 'sample.png')
        self.model = self.root / 'model'
        self.model.mkdir()
        (self.model / 'model_index.json').write_text('{}')
        self.config = load_config()
        self.config['paths'].update(model_snapshot_root=str(self.model),
                                    records_root=str(self.root / 'records'),
                                    datasets_cache=str(self.root / 'datasets'))
        self.output = self.root / 'output'
        self.request = TrainingRequest(image_dir=str(self.images), mode='新規学習',
                                       output_dir=str(self.output), target_steps=1, instance_prompt='test01')
        self.jobs = Mock()
        self.snapshot = JobSnapshot(job_id='test', operation='LoRA学習', state='running',
                                    started_at=None, finished_at=None, return_code=None,
                                    log_path=None, message='started', log_tail='')
        self.jobs.start.return_value = self.snapshot
        self.service = TrainingService(self.config, self.jobs)

    def start(self, report):
        with patch('core.training.inspect_environment', return_value=report):
            return self.service.start(self.request)

    def test_1120_of_20470_mib_starts_and_records_diagnostics(self):
        self.assertEqual(self.start(environment_report()), self.snapshot)
        self.jobs.start.assert_called_once()
        manifest = json.loads(self.service._manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(manifest['gpu']['memory_used_mib'], 1120)
        self.assertEqual(manifest['gpu']['memory_total_mib'], 20470)
        self.assertEqual(manifest['gpu']['memory_free_mib'], 19350)

    def test_no_free_memory_threshold_is_used(self):
        self.start(environment_report(used=20470))
        self.jobs.start.assert_called_once()

    def test_cuda_unavailable_still_rejects(self):
        with self.assertRaises(EnvironmentNotReadyError):
            self.start(environment_report(cuda=False))
        self.jobs.start.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_unknown_memory_is_not_a_rejection(self):
        self.start(environment_report(used=None, total=None))
        self.jobs.start.assert_called_once()
        self.assertIsNone(self.service._manifest['gpu']['memory_free_mib'])

    def test_missing_required_path_still_rejects(self):
        report = replace(environment_report(), path_status={'Python': False})
        with self.assertRaises(EnvironmentNotReadyError):
            self.start(report)
        self.jobs.start.assert_not_called()

    def test_diagnostic_display_and_partial_unknown_values(self):
        report = environment_report()
        text = report.to_markdown()
        for amount in (1120, 20470, 19350):
            self.assertIn(f'{amount} MiB', text)
        self.assertIn('保証できません', text)
        for used, total in ((None, None), (1120, None), (None, 20470), (30000, 20470)):
            with self.subTest(used=used, total=total):
                report = environment_report(used, total)
                self.assertIsNone(report.nvidia_free_mib)
                self.assertIn('取得不可', report.vram_markdown())
                self.assertTrue(report.ready)

    def test_start_panel_displays_preflight_diagnostics(self):
        controller = AppController(self.config)
        controller.training = self.service
        with patch('core.training.inspect_environment', return_value=environment_report()), patch.object(controller, '_save_settings'):
            text, _ = controller.start_training(str(self.images), '新規学習', str(self.output), '', 1, 'test01')
        self.assertIn('19350 MiB', text)
        self.assertIn('保証できません', text)

    def test_failed_manifest_preserves_log_and_records_reason(self):
        self.start(environment_report())
        log = Path(self.service._manifest['log_path'])
        raw = b'original traceback\nCUDA out of memory\n'
        log.write_bytes(raw)
        failure = replace(self.snapshot, state='failed', return_code=1, message='CUDA Out of Memory')
        self.service._finalize(failure)
        manifest = json.loads(self.service._manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(manifest['status'], 'failed')
        self.assertEqual(manifest['failure_message'], failure.message)
        self.assertEqual(log.read_bytes(), raw)


class CudaOomNotificationTests(unittest.TestCase):
    def run_child(self, marker, return_code=1, operation='LoRA学習'):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        log = root / 'job.log'
        log.write_bytes(b'existing log preserved\n')
        manager = ProcessManager(max_log_lines=2)
        callback = Mock()
        code = f"print({marker!r}); [print('trailing line') for _ in range(8)]; raise SystemExit({return_code})"
        manager.start(job_id='oom-test', operation=operation,
                      command=[sys.executable, '-c', code], cwd=root,
                      environment=os.environ.copy(), log_path=log, on_complete=callback)
        manager._thread.join(timeout=10)
        self.assertFalse(manager._thread.is_alive())
        snapshot = manager.snapshot()
        callback.assert_called_once()
        self.assertEqual(callback.call_args.args[0], snapshot)
        return snapshot, log.read_text(encoding='utf-8')

    def test_cuda_oom_is_explained_even_after_it_leaves_log_tail(self):
        for marker in ('torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2 GiB',
                       'torch.cuda.OutOfMemoryError', 'RuntimeError: CUDA error: out of memory'):
            with self.subTest(marker=marker):
                snapshot, log = self.run_child(marker)
                self.assertEqual(snapshot.state, 'failed')
                self.assertIn('CUDA Out of Memory', snapshot.message)
                self.assertIn('他のアプリ', snapshot.message)
                self.assertIn('解像度やバッチサイズ', snapshot.message)
                self.assertNotIn(marker, snapshot.log_tail)
                self.assertTrue(log.startswith('existing log preserved\n'))
                self.assertIn(marker, log)
                self.assertIn(snapshot.log_path, AppController._status_markdown(snapshot))

    def test_generation_uses_same_oom_notification(self):
        snapshot, _ = self.run_child('CUDA out of memory', operation='画像生成')
        self.assertIn('画像生成がCUDA Out of Memory', snapshot.message)

    def test_unrelated_error_is_not_misclassified(self):
        snapshot, log = self.run_child('ValueError: invalid path')
        self.assertEqual(snapshot.state, 'failed')
        self.assertIn('終了コード1', snapshot.message)
        self.assertNotIn('CUDA Out of Memory', snapshot.message)
        self.assertIn('ValueError: invalid path', log)

    def test_success_is_not_changed_by_oom_text_in_output(self):
        snapshot, _ = self.run_child('CUDA out of memory was handled', return_code=0)
        self.assertEqual(snapshot.state, 'succeeded')
        self.assertNotIn('失敗', snapshot.message)

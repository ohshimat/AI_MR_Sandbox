import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app import build_app
from core.config import load_config
from core.controller import AppController
from core.model_settings import MODEL_ENVIRONMENT_VARIABLE, read_user_model_path, save_user_model_path


class ModelSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = self.root / 'モデル with spaces'
        self.model.mkdir()
        (self.model / 'model_index.json').write_text('{}')
        self.c = AppController.__new__(AppController)
        self.c.config = {'paths': {'model_snapshot_root': 'previous'}}
        self.c.jobs = Mock()
        self.c.jobs.snapshot.return_value = Mock(state='idle')

    def test_apply_updates_shared_config_after_persisting(self):
        with patch('core.controller.save_user_model_path', return_value=True) as save:
            value, message = self.c.apply_model_folder(str(self.model / '..' / self.model.name))
        save.assert_called_once_with(str(self.model.resolve()))
        self.assertEqual(value, str(self.model.resolve()))
        self.assertEqual(self.c.config['paths']['model_snapshot_root'], value)
        self.assertIn('保存・適用しました', message)

    def test_invalid_model_preserves_environment_and_config(self):
        with patch('core.controller.save_user_model_path') as save:
            _, message = self.c.apply_model_folder(str(self.root / 'missing'))
        save.assert_not_called()
        self.assertEqual(self.c.config['paths']['model_snapshot_root'], 'previous')
        self.assertIn('model_index.json', message)

    def test_busy_job_prevents_change(self):
        self.c.jobs.snapshot.return_value = Mock(state='running')
        with patch('core.controller.save_user_model_path') as save:
            self.c.apply_model_folder(str(self.model))
        save.assert_not_called()
        self.assertEqual(self.c.config['paths']['model_snapshot_root'], 'previous')

    def test_registry_failure_preserves_config(self):
        with patch('core.controller.save_user_model_path', side_effect=PermissionError('denied')):
            _, message = self.c.apply_model_folder(str(self.model))
        self.assertEqual(self.c.config['paths']['model_snapshot_root'], 'previous')
        self.assertIn('denied', message)

    def test_notification_failure_is_not_reported_as_save_failure(self):
        with patch('core.controller.save_user_model_path', return_value=False):
            value, message = self.c.apply_model_folder(str(self.model))
        self.assertEqual(value, str(self.model.resolve()))
        self.assertIn('保存は完了', message)

    def test_browse_cancel_does_not_persist(self):
        with patch('core.controller.choose_folder', return_value='previous'), patch('core.controller.save_user_model_path') as save:
            value, _ = self.c.browse_model_folder('previous')
        self.assertEqual(value, 'previous')
        save.assert_not_called()

    def test_native_registry_save_updates_process_environment(self):
        with patch.dict(os.environ), patch('winreg.CreateKeyEx') as create, patch('winreg.SetValueEx') as write, patch('core.model_settings.notify_environment_change', return_value=True):
            self.assertTrue(save_user_model_path(str(self.model)))
            self.assertEqual(os.environ[MODEL_ENVIRONMENT_VARIABLE], str(self.model))
            import winreg
            write.assert_called_once_with(create.return_value.__enter__.return_value, MODEL_ENVIRONMENT_VARIABLE, 0, winreg.REG_SZ, str(self.model))
            self.assertEqual(create.call_args.args[0], winreg.HKEY_CURRENT_USER)

    def test_failed_registry_write_does_not_change_process_environment(self):
        with patch.dict(os.environ, {MODEL_ENVIRONMENT_VARIABLE: 'previous'}), patch('winreg.CreateKeyEx'), patch('winreg.SetValueEx', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                save_user_model_path(str(self.model))
            self.assertEqual(os.environ[MODEL_ENVIRONMENT_VARIABLE], 'previous')

    def test_saved_user_value_used_on_next_load_without_process_override(self):
        with patch.dict(os.environ):
            os.environ.pop(MODEL_ENVIRONMENT_VARIABLE, None)
            with patch('core.config.read_user_model_path', return_value=str(self.model)):
                self.assertEqual(load_config()['paths']['model_snapshot_root'], str(self.model))

    def test_explicit_process_override_keeps_priority(self):
        with patch.dict(os.environ, {MODEL_ENVIRONMENT_VARIABLE: 'explicit'}), patch('core.config.read_user_model_path', return_value='saved') as read:
            self.assertEqual(load_config()['paths']['model_snapshot_root'], 'explicit')
            read.assert_not_called()

    def test_registry_read_and_unsupported_platform(self):
        import winreg
        with patch('winreg.OpenKey'), patch('winreg.QueryValueEx', return_value=(str(self.model), winreg.REG_SZ)):
            self.assertEqual(read_user_model_path(), str(self.model))
        with patch('core.model_settings.os.name', 'posix'):
            self.assertIsNone(read_user_model_path())
            with self.assertRaisesRegex(OSError, 'Windows'):
                save_user_model_path('anything')

    def test_gui_has_shared_model_setting_and_callbacks(self):
        with patch('gradio.queueing.safe_get_lock', side_effect=asyncio.Lock), patch('gradio.utils.safe_get_lock', side_effect=asyncio.Lock), patch('gradio.utils.safe_get_stop_event', side_effect=asyncio.Event), patch.object(AppController, 'environment_markdown', return_value='environment'), patch.object(AppController, 'history_records', return_value=[]), patch.object(AppController, 'lora_choices', return_value=[]):
            demo, _ = build_app()
        components = demo.config['components']
        model = next(c for c in components if c['props'].get('label') == 'SDXL Baseモデルフォルダー')
        self.assertTrue(any(c['props'].get('value') == 'モデル設定を保存・適用' for c in components))
        callbacks = [d for d in demo.config['dependencies'] if d['inputs'] == [model['id']]]
        self.assertEqual(len(callbacks), 2)
        self.assertTrue(all(d['api_visibility'] == 'private' for d in callbacks))

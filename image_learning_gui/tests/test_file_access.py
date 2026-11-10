import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.controller import AppController
from core.file_access import checked_path, choose_folder, open_local, read_content


class FileAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = self.root / 'test_manifest.json'
        self.image = self.root / 'image.png'
        self.log = self.root / 'train.log'
        self.log.write_text('学習ログ', encoding='utf-8')
        self.record.write_text(json.dumps({'operation': 'training', 'status': 'success',
                                         'finished_at': '2026-11-10', 'log_path': str(self.log)}), encoding='utf-8')
        self.c = AppController.__new__(AppController)
        self.c.config = {'paths': {key: str(self.root) for key in ('records_root', 'lora_root', 'generated_root')},
                         'ui_defaults': {}}
        self.c.config['paths']['preview_cache'] = str(self.root / 'preview')

    def test_history_structure_and_markdown(self):
        rows = self.c.history_records()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['datetime'], '2026-11-10')
        self.assertIn(str(self.record), self.c.history_markdown())
        self.assertIn('training / success', self.c.history_markdown())

    def test_empty_and_invalid_history(self):
        self.record.write_text('[]')
        self.assertEqual(self.c.history_records(), [])
        self.record.write_text('{broken')
        self.assertEqual(self.c.history_records(), [])

    def test_registered_log_read(self):
        self.assertIn(str(self.log), self.c.history_files(str(self.record)))
        text, image = self.c.history_file_action(str(self.record), str(self.log), 'view')
        self.assertEqual(text, '学習ログ')
        self.assertIsNone(image)

    def test_unregistered_record_rejected(self):
        with self.assertRaises(ValueError):
            self.c.history_files(str(self.log))

    def test_unreferenced_file_rejected(self):
        other = self.root / 'private.json'
        other.write_text('{}')
        with patch('core.controller.open_local') as opener:
            text, _ = self.c.history_file_action(str(self.record), str(other), 'open')
            self.assertIn('アクセスできません', text)
            opener.assert_not_called()

    def test_external_reference_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            file = Path(outside) / 'outside.log'
            file.write_text('secret')
            self.record.write_text(json.dumps({'log_path': str(file)}))
            self.assertNotIn(str(file), self.c.history_files(str(self.record)))
            with self.assertRaises(ValueError):
                checked_path(file, [self.root])

    def test_missing_reference_rejected(self):
        self.log.unlink()
        self.assertNotIn(str(self.log), self.c.history_files(str(self.record)))

    def test_normalized_relative_reference(self):
        self.record.write_text(json.dumps({'log_path': './train.log'}))
        self.assertIn(str(self.log.resolve()), self.c.history_files(str(self.record)))

    def test_open_file_and_folder(self):
        with patch('core.controller.open_local') as opener:
            self.c.history_file_action(str(self.record), str(self.log), 'open')
            opener.assert_called_once_with(self.log.resolve())
            self.c.history_file_action(str(self.record), str(self.log), 'folder')
            self.assertEqual(opener.call_args.kwargs, {'folder': True})

    def test_image_preview_uses_only_cache(self):
        from PIL import Image
        Image.new('RGB', (8, 8)).save(self.image)
        self.record.write_text(json.dumps({'image': str(self.image)}))
        _, preview = self.c.history_file_action(str(self.record), str(self.image), 'view')
        self.assertEqual(Path(preview).parent, self.root / 'preview')

    def test_safetensors_only_header(self):
        target = self.root / 'weights.safetensors'
        header = json.dumps({'__metadata__': {'trigger': 'test'}}).encode()
        target.write_bytes(struct.pack('<Q', len(header)) + header + b'NOT LOADED')
        self.record.write_text(json.dumps({'output_lora': str(target)}))
        with patch('core.controller.open_local') as opener:
            text, _ = self.c.history_file_action(str(self.record), str(target), 'open')
            self.assertIn('trigger', text)
            self.assertNotIn('NOT LOADED', text)
            opener.assert_not_called()

    def test_bad_safetensors_header(self):
        target = self.root / 'bad.safetensors'
        target.write_bytes(struct.pack('<Q', 9999999999))
        with self.assertRaises(ValueError):
            read_content(target)

    def test_large_log_is_bounded(self):
        self.log.write_bytes(b'a' * (1024 * 1024 + 2))
        self.assertIn('省略', read_content(self.log))

    def test_unsupported_platform(self):
        with patch('core.file_access.os.name', 'posix'):
            with self.assertRaisesRegex(OSError, 'Windows'):
                choose_folder('old')
            with self.assertRaisesRegex(OSError, 'Windows'):
                open_local(self.log)

    def test_folder_cancel_and_save(self):
        with patch('core.controller.choose_folder', return_value='old'), patch.object(self.c, '_save_settings') as save:
            self.assertEqual(self.c.browse_folder('old', 'training_output_dir')[0], 'old')
            save.assert_not_called()
        with patch('core.controller.choose_folder', return_value=str(self.root)), patch.object(self.c, '_save_settings') as save:
            self.c.browse_folder('old', 'training_output_dir')
            save.assert_called_once_with(training_output_dir=str(self.root))

    def test_folder_failure_preserves_input(self):
        with patch('core.controller.choose_folder', side_effect=OSError('Windows')):
            value, message = self.c.browse_folder('old', 'training_output_dir')
            self.assertEqual(value, 'old')
            self.assertIn('Windows', message)

    def test_native_dialog_cancel_and_cleanup(self):
        root = MagicMock()
        with patch('tkinter.Tk', return_value=root), patch('tkinter.filedialog.askdirectory', return_value='') as ask:
            self.assertEqual(choose_folder(str(self.root)), str(self.root))
            self.assertTrue(ask.call_args.kwargs['mustexist'])
            root.destroy.assert_called_once()

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'secret.log'
            target.write_text('secret')
            link = self.root / 'link.log'
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest('Windows symlink privilege unavailable')
            with self.assertRaises(ValueError):
                checked_path(link, [self.root])

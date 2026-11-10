import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from app import build_app, create_training_start_handler
from core.config import load_config
from core.controller import AppController
from core.training import validate_training_request


class TrainingFeedbackTests(unittest.TestCase):
    def test_start_rejection_is_visible_without_process_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = root / 'images'
            images.mkdir()
            Image.new('RGB', (512, 512)).save(images / 'sample.png')
            output = root / 'existing'
            output.mkdir()
            (output / 'previous.safetensors').write_bytes(b'preserve')
            controller = AppController(load_config())
            with patch.object(controller.training, 'start', side_effect=lambda request: validate_training_request(request, controller.config)):
                status, log, feedback = create_training_start_handler(controller)(
                    str(images), '新規学習', str(output), '', 10, 'test trigger', '固定プロンプト')
            self.assertEqual(feedback, status)
            self.assertIn('空ではありません', feedback)
            self.assertEqual(log, '')
            self.assertEqual(controller.jobs.snapshot().state, 'idle')
            self.assertEqual((output / 'previous.safetensors').read_bytes(), b'preserve')

    def test_success_forwards_training_inputs_and_log(self):
        controller = Mock()
        controller.start_training.return_value = ('running', 'started')
        args = ('images', '新規学習', 'new-output', '', 30, 'trigger', '固定プロンプト')
        self.assertEqual(create_training_start_handler(controller)(*args), ('running', 'started', 'running'))
        controller.start_training.assert_called_once_with(*args)

    def test_layout_and_polling_preserve_start_feedback(self):
        # Socket creation is unavailable in the test sandbox. No server is started.
        with patch('gradio.queueing.safe_get_lock', side_effect=asyncio.Lock), patch('gradio.utils.safe_get_lock', side_effect=asyncio.Lock), patch('gradio.utils.safe_get_stop_event', side_effect=asyncio.Event), patch.object(AppController, 'environment_markdown', return_value='environment'), patch.object(AppController, 'history_records', return_value=[]), patch.object(AppController, 'lora_choices', return_value=[]):
            demo, _ = build_app()
        components = demo.config['components']
        labels = {item['props'].get('label'): item['id'] for item in components if item['props'].get('label')}
        self.assertLess(labels['学習プロンプト方式'], labels['共通／識別用学習プロンプト'])
        self.assertLess(labels['共通／識別用学習プロンプト'], labels['学習モード'])
        start_event = next(event for event in demo.config['dependencies'] if event['inputs'] == [labels[name] for name in ['学習画像フォルダ', '学習モード', '学習結果フォルダ', '継続元checkpoint', '1画像あたりの総学習回数', '共通／識別用学習プロンプト', '学習プロンプト方式']])
        feedback = start_event['outputs'][2]
        self.assertEqual(len(start_event['outputs']), 3)
        for event in demo.config['dependencies']:
            if any(target[1] == 'tick' for target in event['targets']):
                self.assertNotIn(feedback, event['outputs'])

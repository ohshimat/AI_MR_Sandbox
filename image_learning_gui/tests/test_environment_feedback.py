import unittest
from unittest.mock import patch, Mock

from core.config import load_config
from core.controller import AppController
from core.environment import EnvironmentNotReadyError, inspect_environment
from core.training import TrainingRequest, TrainingService


class EnvironmentFeedbackTests(unittest.TestCase):
    def report(self, cuda=True, model=None, python_error=None):
        config = load_config()
        config['paths']['model_snapshot_root'] = 'missing-model-folder'
        details = {'python_executable': config['paths']['python_executable'], 'cuda_available': cuda,
                   'packages': {'torch': 'test'}, 'cuda_runtime': 'test'}
        if python_error:
            details['torch_error'] = python_error
        with patch('core.environment.resolve_model_dir', return_value=model), patch('core.environment._is_file', return_value=True), patch('core.environment._python_environment', return_value=details), patch('core.environment._nvidia_memory', return_value=(None, None, None)), patch('core.environment._disk_free', return_value=None):
            return config, inspect_environment(config)

    def test_missing_model_identifies_path_and_action(self):
        config, report = self.report()
        text = AppController._error_markdown('学習を開始できません。', EnvironmentNotReadyError(report, config))
        self.assertIn('SDXLモデルパスが見つかりません', text)
        self.assertIn('missing-model-folder', text)
        self.assertIn('AI_MR_SDXL_MODEL_PATH', text)
        self.assertIn('model_index.json', text)
        self.assertIn('まだ起動していません', text)
        self.assertNotIn('入力したパスと値を見直して', text)

    def test_cuda_and_torch_error_are_explained_and_escaped(self):
        config, report = self.report(cuda=False, python_error='<broken> torch DLL')
        text = EnvironmentNotReadyError(report, config).to_markdown()
        self.assertIn('CUDAを利用できません', text)
        self.assertIn(config['paths']['python_executable'], text)
        self.assertIn('&lt;broken&gt;', text)
        self.assertNotIn('<broken>', text)

    def test_missing_executable_identifies_configured_path(self):
        config, report = self.report()
        from dataclasses import replace
        report = replace(report, path_status={'Python': False, 'Accelerate': False})
        text = EnvironmentNotReadyError(report, config).to_markdown()
        self.assertIn('AI_MR_IMAGE_PYTHON', text)
        self.assertIn(config['paths']['accelerate_executable'], text)

    def test_training_stops_before_job_creation_with_original_report(self):
        config, report = self.report()
        jobs = Mock()
        service = TrainingService(config, jobs)
        with patch('core.training.validate_training_request', return_value=(None, None, 0)), patch('core.training.inspect_environment', return_value=report) as inspect:
            with self.assertRaises(EnvironmentNotReadyError) as raised:
                service.start(TrainingRequest(image_dir='images', mode='新規学習', output_dir='output', target_steps=1, instance_prompt='trigger'))
        self.assertIs(raised.exception.report, report)
        inspect.assert_called_once()
        jobs.start.assert_not_called()

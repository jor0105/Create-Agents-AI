from unittest.mock import Mock
import time

import pytest

from createagents.infra.adapters.Common.metrics_recorder import (
    MetricsRecorder,
)
from createagents.infra.config.metrics import ChatMetrics


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.mark.unit
class TestMetricsRecorder:
    def test_scenario_initialization_with_no_metrics_list(self, mock_logger):
        recorder = MetricsRecorder(logger=mock_logger)
        assert recorder._metrics == []

    def test_scenario_initialization_with_existing_metrics_list(
        self, mock_logger
    ):
        existing_metrics = [Mock(spec=ChatMetrics)]
        recorder = MetricsRecorder(
            logger=mock_logger, metrics_list=existing_metrics
        )
        assert recorder._metrics == existing_metrics

    def test_scenario_record_success_metrics_generic_provider(
        self, mock_logger
    ):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()

        recorder.record_success_metrics(
            model='test-model',
            start_time=start_time,
            response_api=Mock(),
            provider_type='generic',
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'test-model'
        assert metrics[0].success is True
        assert metrics[0].latency_ms >= 0

    def test_scenario_record_success_metrics_openai_provider(
        self, mock_logger
    ):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()

        mock_usage = Mock()
        mock_usage.total_tokens = 100
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 50

        mock_response = Mock()
        mock_response.usage = mock_usage

        recorder.record_success_metrics(
            model='gpt-4',
            start_time=start_time,
            response_api=mock_response,
            provider_type='openai',
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'gpt-4'
        assert metrics[0].tokens_used == 100
        assert metrics[0].prompt_tokens == 50
        assert metrics[0].completion_tokens == 50
        assert metrics[0].success is True

    def test_scenario_record_success_metrics_ollama_provider(
        self, mock_logger
    ):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()

        mock_response = {
            'prompt_eval_count': 30,
            'eval_count': 20,
            'load_duration': 1000000,
            'prompt_eval_duration': 2000000,
            'eval_duration': 3000000,
        }

        recorder.record_success_metrics(
            model='llama2',
            start_time=start_time,
            response_api=mock_response,
            provider_type='ollama',
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'llama2'
        assert metrics[0].tokens_used == 50
        assert metrics[0].prompt_tokens == 30
        assert metrics[0].completion_tokens == 20
        assert metrics[0].load_duration_ms == 1.0
        assert metrics[0].prompt_eval_duration_ms == 2.0
        assert metrics[0].eval_duration_ms == 3.0

    def test_scenario_record_error_metrics(self, mock_logger):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()
        error = ValueError('Test error')

        recorder.record_error_metrics(
            model='test-model', start_time=start_time, error=error
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == 'test-model'
        assert metrics[0].success is False
        assert metrics[0].error_message == 'Test error'
        assert metrics[0].latency_ms >= 0

    def test_scenario_get_metrics_returns_copy(self, mock_logger):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()

        recorder.record_error_metrics(
            model='test', start_time=start_time, error='error'
        )

        metrics1 = recorder.get_metrics()
        metrics2 = recorder.get_metrics()

        assert metrics1 == metrics2
        assert metrics1 is not metrics2

    def test_scenario_multiple_metrics_recorded(self, mock_logger):
        recorder = MetricsRecorder(logger=mock_logger)
        start_time = time.time()

        recorder.record_success_metrics(
            model='model1', start_time=start_time, response_api=Mock()
        )
        recorder.record_error_metrics(
            model='model2', start_time=start_time, error='err'
        )
        recorder.record_success_metrics(
            model='model3', start_time=start_time, response_api=Mock()
        )

        metrics = recorder.get_metrics()
        assert len(metrics) == 3
        assert metrics[0].model == 'model1'
        assert metrics[1].model == 'model2'
        assert metrics[2].model == 'model3'

    def test_scenario_extract_openai_tokens_no_usage(self):
        mock_response = Mock(spec=[])

        tokens_used, prompt_tokens, completion_tokens = (
            MetricsRecorder._extract_openai_tokens(mock_response)
        )

        assert tokens_used is None
        assert prompt_tokens is None
        assert completion_tokens is None

    def test_scenario_extract_ollama_tokens_empty_response(self):
        response = {}

        tokens_used, prompt_tokens, completion_tokens = (
            MetricsRecorder._extract_ollama_tokens(response)
        )

        assert tokens_used == 0
        assert prompt_tokens == 0
        assert completion_tokens == 0

    def test_scenario_extract_ollama_durations_none_values(self):
        response = {}

        load_ms, prompt_ms, eval_ms = (
            MetricsRecorder._extract_ollama_durations(response)
        )

        assert load_ms is None
        assert prompt_ms is None
        assert eval_ms is None

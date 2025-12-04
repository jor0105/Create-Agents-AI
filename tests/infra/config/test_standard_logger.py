"""Tests for LoggingConfig implementation.

This module tests the LoggingConfig class which implements LoggerInterface,
ensuring it correctly delegates to Python's logging module.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from createagents.domain.interfaces.logger_interface import LoggerInterface
from createagents.infra.config.logging_configurator import (
    JSONFormatter,
    LoggingConfigurator,
    SensitiveDataFormatter,
    _LoggingState,
)
from createagents.infra.config.logging_config import (
    LoggingConfig,
    configure_logging,
    create_logger,
)


@pytest.fixture(autouse=True)
def reset_logging_state():
    """Reset logging state before and after each test."""
    LoggingConfigurator.reset()
    yield
    LoggingConfigurator.reset()


@pytest.mark.unit
class TestStandardLogger:
    """Tests for LoggingConfig basic operations."""

    def test_initialization_success(self):
        """LoggingConfig initializes correctly with a Python logger."""
        python_logger = logging.getLogger('test.init')
        logger = LoggingConfig(python_logger)

        assert isinstance(logger, LoggerInterface)
        assert logger._logger == python_logger

    def test_debug_delegates_to_python_logger(self):
        """debug() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.debug('test message', 'arg1', key='value')

        python_logger.debug.assert_called_once_with(
            'test message', 'arg1', key='value'
        )

    def test_info_delegates_to_python_logger(self):
        """info() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.info('info message', 'arg1', key='value')

        python_logger.info.assert_called_once_with(
            'info message', 'arg1', key='value'
        )

    def test_warning_delegates_to_python_logger(self):
        """warning() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.warning('warning message', 'arg1', key='value')

        python_logger.warning.assert_called_once_with(
            'warning message', 'arg1', key='value'
        )

    def test_error_delegates_to_python_logger(self):
        """error() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.error('error message', 'arg1', key='value')

        python_logger.error.assert_called_once_with(
            'error message', 'arg1', key='value'
        )

    def test_critical_delegates_to_python_logger(self):
        """critical() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.critical('critical message', 'arg1', key='value')

        python_logger.critical.assert_called_once_with(
            'critical message', 'arg1', key='value'
        )

    def test_exception_delegates_to_python_logger(self):
        """exception() delegates correctly to Python logger."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        logger.exception('exception message', 'arg1', key='value')

        python_logger.exception.assert_called_once_with(
            'exception message', 'arg1', key='value'
        )

    def test_implements_logger_interface(self):
        """LoggingConfig implements all LoggerInterface methods."""
        python_logger = logging.getLogger('test.interface')
        logger = LoggingConfig(python_logger)

        # LoggingConfig should only have logging methods (ISP compliance)
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'critical')
        assert hasattr(logger, 'exception')

    def test_logger_with_exception_info(self):
        """error() correctly passes exc_info parameter."""
        python_logger = Mock(spec=logging.Logger)
        logger = LoggingConfig(python_logger)

        try:
            raise ValueError('test exception')
        except ValueError:
            logger.error('Error occurred', exc_info=True)

        python_logger.error.assert_called_once()
        call_args = python_logger.error.call_args
        assert call_args[0][0] == 'Error occurred'
        assert call_args[1]['exc_info'] is True


@pytest.mark.unit
class TestCreateLoggerFactory:
    """Tests for create_logger factory function."""

    def test_create_logger_returns_standard_logger(self):
        """create_logger returns a LoggingConfig instance."""
        logger = create_logger('test.factory')

        assert isinstance(logger, LoggingConfig)
        assert isinstance(logger, LoggerInterface)

    def test_create_logger_uses_correct_name(self):
        """create_logger creates logger with correct name."""
        logger = create_logger('my.module.name')

        assert logger._logger.name == 'my.module.name'

    def test_create_logger_multiple_calls_same_name(self):
        """create_logger returns loggers sharing underlying Python logger."""
        logger1 = create_logger('shared.name')
        logger2 = create_logger('shared.name')

        assert logger1._logger is logger2._logger


@pytest.mark.unit
class TestConfigureLogging:
    """Tests for configure_logging convenience function."""

    def test_configure_logging_returns_logger(self):
        """configure_logging returns a configured LoggingConfig."""
        logger = configure_logging(level=logging.DEBUG)

        assert isinstance(logger, LoggingConfig)
        assert LoggingConfigurator.is_configured()

    def test_configure_logging_sets_level(self):
        """configure_logging sets the specified log level."""
        configure_logging(level=logging.WARNING)

        assert _LoggingState.log_level == logging.WARNING


@pytest.mark.unit
class TestLoggingConfiguratorIntegration:
    """Tests for LoggingConfig with LoggingConfigurator."""

    def test_configure_sets_level(self):
        """LoggingConfigurator.configure() sets the logging level."""
        LoggingConfigurator.configure(level=logging.ERROR)

        assert _LoggingState.log_level == logging.ERROR
        assert _LoggingState.configured is True

    def test_configure_with_timestamp(self):
        """configure() includes timestamp by default."""
        LoggingConfigurator.configure(
            level=logging.INFO, include_timestamp=True
        )

        assert len(_LoggingState.handlers) >= 1

    def test_configure_without_timestamp(self):
        """configure() can exclude timestamp."""
        LoggingConfigurator.configure(
            level=logging.INFO, include_timestamp=False
        )

        assert len(_LoggingState.handlers) >= 1

    def test_reset_clears_configuration(self):
        """reset() clears logging configuration."""
        LoggingConfigurator.configure(level=logging.DEBUG)
        assert _LoggingState.configured is True

        LoggingConfigurator.reset()

        assert _LoggingState.configured is False
        assert len(_LoggingState.handlers) == 0

    def test_set_level_changes_level_at_runtime(self):
        """set_level() changes logging level at runtime."""
        LoggingConfigurator.configure(level=logging.INFO)

        LoggingConfigurator.set_level(logging.DEBUG)

        assert _LoggingState.log_level == logging.DEBUG

    def test_is_configured_returns_correct_state(self):
        """is_configured() returns correct configuration state."""
        assert LoggingConfigurator.is_configured() is False

        LoggingConfigurator.configure(level=logging.INFO)

        assert LoggingConfigurator.is_configured() is True

    @patch.dict('os.environ', {'LOG_LEVEL': 'WARNING'})
    def test_configure_reads_level_from_env(self):
        """configure() reads LOG_LEVEL from environment."""
        LoggingConfigurator.configure()

        assert _LoggingState.log_level == logging.WARNING

    @patch.dict('os.environ', {'LOG_JSON_FORMAT': 'true'})
    def test_configure_reads_json_format_from_env(self):
        """configure() reads LOG_JSON_FORMAT from environment."""
        LoggingConfigurator.configure()

        assert _LoggingState.configured is True


@pytest.mark.unit
class TestFormatters:
    """Tests for log formatters."""

    def test_sensitive_data_formatter_filters_api_key(self):
        """SensitiveDataFormatter filters API keys."""
        formatter = SensitiveDataFormatter('%(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='api_key=sk-1234567890abcdef',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'sk-1234567890abcdef' not in result
        assert 'REDACTED' in result

    def test_json_formatter_produces_valid_json(self):
        """JSONFormatter produces valid JSON output."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test.json',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test.json'
        assert parsed['message'] == 'Test message'
        assert parsed['line'] == 42

    def test_json_formatter_filters_sensitive_data(self):
        """JSONFormatter also filters sensitive data."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='password=secret123',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'secret123' not in result
        assert 'REDACTED' in result

"""Tests for logging configuration.

This module tests:
- SensitiveDataFormatter and JSONFormatter
- LoggingConfigurator (global configuration)
- LoggingConfig (logger instance)
"""

import json
import logging
import os
import tempfile
from pathlib import Path


from createagents.infra import (
    JSONFormatter,
    LoggingConfig,
    LoggingConfigurator,
    SensitiveDataFilter,
    SensitiveDataFormatter,
)
from createagents.infra.config import create_logger


class TestSensitiveDataFormatter:
    def setup_method(self):
        SensitiveDataFilter.clear_cache()

    def test_format_filters_sensitive_data(self):
        formatter = SensitiveDataFormatter('%(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='password=secret123',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'secret123' not in result
        assert '[PASSWORD_REDACTED]' in result

    def test_format_preserves_normal_messages(self):
        formatter = SensitiveDataFormatter('%(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Normal message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert result == 'Normal message'

    def test_format_with_timestamp(self):
        formatter = SensitiveDataFormatter('%(asctime)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert 'Test message' in result
        assert '-' in result


class TestJSONFormatter:
    def setup_method(self):
        SensitiveDataFilter.clear_cache()

    def test_format_returns_valid_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test.module',
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
        assert parsed['logger'] == 'test.module'
        assert parsed['message'] == 'Test message'
        assert parsed['module'] == 'test'
        assert parsed['line'] == 42

    def test_format_filters_sensitive_data_in_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='API_KEY=sk-123456789012',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert 'sk-123456789012' not in parsed['message']
        assert '[API_KEY_REDACTED]' in parsed['message']

    def test_format_includes_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError('Test error')
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error occurred',
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert 'exception' in parsed
        assert 'ValueError: Test error' in parsed['exception']


class TestLoggingConfigurator:
    """Tests for LoggingConfigurator (global configuration)."""

    def setup_method(self):
        LoggingConfigurator.reset()

    def teardown_method(self):
        LoggingConfigurator.reset()
        for key in [
            'LOG_LEVEL',
            'LOG_TO_FILE',
            'LOG_FILE_PATH',
            'LOG_JSON_FORMAT',
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_configure_default_settings(self):
        LoggingConfigurator.configure()

        assert LoggingConfigurator.is_configured() is True
        assert LoggingConfigurator.get_current_level() == logging.INFO
        assert len(LoggingConfigurator.get_handlers()) == 1

    def test_configure_custom_level(self):
        LoggingConfigurator.configure(level=logging.DEBUG)

        assert LoggingConfigurator.get_current_level() == logging.DEBUG
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_from_env_var(self):
        os.environ['LOG_LEVEL'] = 'WARNING'
        LoggingConfigurator.configure()

        assert LoggingConfigurator.get_current_level() == logging.WARNING

    def test_configure_invalid_env_var_uses_default(self):
        os.environ['LOG_LEVEL'] = 'INVALID'
        LoggingConfigurator.configure()

        assert LoggingConfigurator.get_current_level() == logging.INFO

    def test_configure_with_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            LoggingConfigurator.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            assert len(LoggingConfigurator.get_handlers()) == 2
            assert log_file.exists() or log_file.parent.exists()

    def test_configure_creates_log_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'nested' / 'dir' / 'test.log'

            LoggingConfigurator.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            assert log_file.parent.exists()

    def test_configure_with_json_format(self):
        LoggingConfigurator.configure(json_format=True)

        handlers = LoggingConfigurator.get_handlers()
        assert len(handlers) > 0
        assert isinstance(handlers[0].formatter, JSONFormatter)

    def test_configure_can_reconfigure(self):
        LoggingConfigurator.configure(level=logging.DEBUG)
        first_level = LoggingConfigurator.get_current_level()
        assert first_level == logging.DEBUG

        LoggingConfigurator.configure(level=logging.ERROR)
        second_level = LoggingConfigurator.get_current_level()

        assert second_level == logging.ERROR

    def test_set_level_changes_level(self):
        LoggingConfigurator.configure(level=logging.INFO)

        LoggingConfigurator.set_level(logging.ERROR)

        assert LoggingConfigurator.get_current_level() == logging.ERROR
        assert logging.getLogger().level == logging.ERROR

    def test_reset_clears_configuration(self):
        LoggingConfigurator.configure()
        assert LoggingConfigurator.is_configured() is True

        LoggingConfigurator.reset()

        assert LoggingConfigurator.is_configured() is False
        assert len(LoggingConfigurator.get_handlers()) == 0

    def test_reset_clears_sensitive_data_cache(self):
        test_text = 'password=secret123'
        SensitiveDataFilter.filter(test_text)
        SensitiveDataFilter.filter(test_text)

        cache_info_before = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_before.hits > 0 or cache_info_before.currsize > 0

        LoggingConfigurator.reset()

        cache_info_after = SensitiveDataFilter._filter_cached.cache_info()
        assert cache_info_after.currsize == 0
        assert cache_info_after.hits == 0
        assert cache_info_after.misses == 0

    def test_get_handlers_returns_copy(self):
        LoggingConfigurator.configure()
        handlers = LoggingConfigurator.get_handlers()
        original_count = len(LoggingConfigurator.get_handlers())

        handlers.clear()

        assert len(LoggingConfigurator.get_handlers()) == original_count

    def test_logging_filters_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            LoggingConfigurator.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            logger = logging.getLogger('test')
            logger.info('User password=secret123')

            for handler in LoggingConfigurator.get_handlers():
                handler.flush()

            if log_file.exists():
                content = log_file.read_text()
                assert 'secret123' not in content
                assert '[PASSWORD_REDACTED]' in content

    def test_configure_with_env_file_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.log'
            os.environ['LOG_TO_FILE'] = 'true'
            os.environ['LOG_FILE_PATH'] = str(log_file)

            LoggingConfigurator.configure()

            assert len(LoggingConfigurator.get_handlers()) == 2

    def test_configure_without_timestamp(self):
        LoggingConfigurator.configure(include_timestamp=False)

        handlers = LoggingConfigurator.get_handlers()
        formatter = handlers[0].formatter
        assert 'asctime' not in formatter._fmt

    def test_configure_custom_format_string(self):
        custom_format = '%(levelname)s - %(message)s'
        LoggingConfigurator.configure(format_string=custom_format)

        handlers = LoggingConfigurator.get_handlers()
        formatter = handlers[0].formatter
        assert formatter._fmt == custom_format

    def test_file_rotation_settings(self):
        from logging.handlers import RotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            max_bytes = 1024
            backup_count = 3

            LoggingConfigurator.configure(
                log_to_file=True,
                log_file_path=str(log_file),
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

            handlers = LoggingConfigurator.get_handlers()
            file_handler = [
                h for h in handlers if isinstance(h, RotatingFileHandler)
            ][0]

            assert file_handler.maxBytes == max_bytes
            assert file_handler.backupCount == backup_count

    def test_multiple_loggers_share_config(self):
        LoggingConfigurator.configure(level=logging.WARNING)

        logger1 = logging.getLogger('module1')
        logger2 = logging.getLogger('module2')

        assert logger1.getEffectiveLevel() == logging.WARNING
        assert logger2.getEffectiveLevel() == logging.WARNING

    def test_default_constants_defined(self):
        assert hasattr(LoggingConfigurator, 'DEFAULT_LOG_LEVEL')
        assert hasattr(LoggingConfigurator, 'DEFAULT_MAX_BYTES')
        assert hasattr(LoggingConfigurator, 'DEFAULT_BACKUP_COUNT')
        assert hasattr(LoggingConfigurator, 'DEFAULT_LOG_PATH')

    def test_default_constants_values(self):
        assert LoggingConfigurator.DEFAULT_LOG_LEVEL == logging.INFO
        assert LoggingConfigurator.DEFAULT_MAX_BYTES == 10 * 1024 * 1024
        assert LoggingConfigurator.DEFAULT_BACKUP_COUNT == 5
        assert LoggingConfigurator.DEFAULT_LOG_PATH == 'logs/app.log'


class TestLoggingConfigInstance:
    """Tests for LoggingConfig (logger instance)."""

    def setup_method(self):
        LoggingConfigurator.reset()

    def teardown_method(self):
        LoggingConfigurator.reset()

    def test_create_logger_returns_logging_config(self):
        logger = create_logger('test.module')

        assert isinstance(logger, LoggingConfig)
        assert logger._logger.name == 'test.module'

    def test_logger_debug_delegates(self):
        LoggingConfigurator.configure(level=logging.DEBUG)
        logger = create_logger('test')

        # Should not raise
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.critical('Critical message')

    def test_logger_exception_delegates(self):
        LoggingConfigurator.configure(level=logging.DEBUG)
        logger = create_logger('test')

        try:
            raise ValueError('Test error')
        except ValueError:
            logger.exception('Caught error')

    def test_multiple_loggers_independent(self):
        logger1 = create_logger('module1')
        logger2 = create_logger('module2')

        assert logger1._logger is not logger2._logger
        assert logger1._logger.name != logger2._logger.name


class TestLoggingIntegration:
    """Integration tests for the logging system."""

    def setup_method(self):
        LoggingConfigurator.reset()

    def teardown_method(self):
        LoggingConfigurator.reset()

    def test_real_world_scenario_with_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.log'
            LoggingConfigurator.configure(
                log_to_file=True, log_file_path=str(log_file)
            )

            logger = logging.getLogger('app')

            logger.info('User logged in: user@example.com')
            logger.debug('API request with key: sk-proj-123456789012')
            logger.warning(
                'Database connection: postgres://admin:pass123@db.com'
            )
            logger.error('Failed payment for card: 4532-1234-5678-9010')

            for handler in LoggingConfigurator.get_handlers():
                handler.flush()

            content = log_file.read_text()

            assert 'user@example.com' not in content
            assert 'sk-proj-123456789012' not in content
            assert 'pass123' not in content
            assert '4532-1234-5678-9010' not in content

            assert '[EMAIL_REDACTED]' in content
            assert (
                '[PASSWORD_REDACTED]' in content
                or '[CREDENTIALS_REDACTED]' in content
            )
            assert '[CREDIT_CARD_REDACTED]' in content

    def test_json_logging_production_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'app.json'
            LoggingConfigurator.configure(
                log_to_file=True, log_file_path=str(log_file), json_format=True
            )

            logger = logging.getLogger('api')
            logger.info('Request received from user@test.com')

            for handler in LoggingConfigurator.get_handlers():
                handler.flush()

            lines = log_file.read_text().strip().split('\n')
            for line in lines:
                log_entry = json.loads(line)

                assert 'timestamp' in log_entry
                assert 'level' in log_entry
                assert 'logger' in log_entry
                assert 'message' in log_entry

                assert 'user@test.com' not in log_entry['message']

    def test_configure_for_development(self):
        LoggingConfigurator.configure_for_development(level=logging.DEBUG)

        assert LoggingConfigurator.is_configured()
        assert LoggingConfigurator.get_current_level() == logging.DEBUG

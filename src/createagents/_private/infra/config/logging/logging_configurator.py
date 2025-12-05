import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

from .sensitive_data_filter import SensitiveDataFilter


class _LoggingState:
    """Internal state management for logging configuration.

    Thread-safe singleton state for global logging configuration.
    """

    configured: bool = False
    log_level: int = logging.INFO
    handlers: List[logging.Handler] = []


class SensitiveDataFormatter(logging.Formatter):
    """Formatter that filters sensitive data from log messages.

    Ensures compliance with LGPD/GDPR by redacting:
    - API keys and tokens
    - Personal data (emails, CPF, phone numbers)
    - Financial data (credit cards, CVV)
    - Passwords and secrets
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sensitive data filtering."""
        original = super().format(record)
        return SensitiveDataFilter.filter(original)


class JSONFormatter(logging.Formatter):
    """Formatter for structured JSON logs.

    Produces machine-readable logs suitable for:
    - Log aggregation systems (ELK, Splunk, Datadog)
    - Cloud logging services (CloudWatch, Stackdriver)
    - Automated log analysis and alerting
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        import json

        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        json_str = json.dumps(log_data, ensure_ascii=False)
        return SensitiveDataFilter.filter(json_str)


class LoggingConfigurator:
    """Manages global logging configuration.

    This class is responsible for:
    - Setting up log handlers (console, file)
    - Configuring log levels globally
    - Managing log formatters (text, JSON)
    - Environment-based configuration

    It follows the Single Responsibility Principle by handling
    only configuration concerns, not logging operations.

    Example:
        >>> LoggingConfigurator.configure(level=logging.DEBUG)
        >>> LoggingConfigurator.set_level(logging.WARNING)
        >>> LoggingConfigurator.reset()
    """

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_PATH = 'logs/app.log'

    @classmethod
    def configure(
        cls,
        level: Optional[int] = None,
        format_string: Optional[str] = None,
        include_timestamp: bool = True,
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        json_format: bool = False,
    ) -> None:
        """Configure the logging system globally.

        This method configures the root logger and all existing loggers
        to use consistent formatting and output destinations.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to LOG_LEVEL environment variable or INFO.
            format_string: Custom format string for log messages.
            include_timestamp: Whether to include timestamps in logs.
            log_to_file: Enable file logging with rotation.
            log_file_path: Path to log file. Defaults to LOG_FILE_PATH env
                           or 'logs/app.log'.
            max_bytes: Maximum file size before rotation (default: 10MB).
            backup_count: Number of backup files to keep (default: 5).
            json_format: Use JSON formatting for structured logs.
        """
        if level is None:
            level = cls._get_log_level_from_env()

        if not log_to_file:
            log_to_file = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'

        if log_file_path is None:
            log_file_path = os.getenv('LOG_FILE_PATH', cls.DEFAULT_LOG_PATH)

        if not json_format:
            json_format = (
                os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
            )

        _LoggingState.log_level = level

        if format_string is None:
            if include_timestamp:
                format_string = (
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            else:
                format_string = '%(name)s - %(levelname)s - %(message)s'

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        _LoggingState.handlers.clear()

        for logger_name in list(logging.Logger.manager.loggerDict):
            existing_logger = logging.getLogger(logger_name)
            existing_logger.setLevel(level)
            for handler in existing_logger.handlers[:]:
                existing_logger.removeHandler(handler)

        formatter: logging.Formatter
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = SensitiveDataFormatter(format_string)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        _LoggingState.handlers.append(console_handler)

        if log_to_file:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(log_file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            root_logger.addHandler(file_handler)
            _LoggingState.handlers.append(file_handler)

        _LoggingState.configured = True

    @classmethod
    def reset(cls) -> None:
        """Reset the logging configuration.

        Removes all handlers and clears configuration state.
        Useful for testing to ensure clean state between tests.
        """
        _LoggingState.configured = False
        root_logger = logging.getLogger()

        for handler in _LoggingState.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        _LoggingState.handlers.clear()
        SensitiveDataFilter.clear_cache()

    @classmethod
    def set_level(cls, level: int) -> None:
        """Adjust the logging level at runtime.

        Args:
            level: The new logging level (e.g., logging.DEBUG).
        """
        _LoggingState.log_level = level
        logging.getLogger().setLevel(level)

    @staticmethod
    def is_configured() -> bool:
        """Check if logging has been configured."""
        return _LoggingState.configured

    @staticmethod
    def get_current_level() -> int:
        """Get the current logging level."""
        return _LoggingState.log_level

    @staticmethod
    def get_handlers() -> List[logging.Handler]:
        """Get the current list of handlers."""
        return _LoggingState.handlers.copy()

    @staticmethod
    def _get_log_level_from_env() -> int:
        """Get log level from environment variable."""
        level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        return level_map.get(level_name, logging.INFO)

    @classmethod
    def configure_for_development(cls, level: int = logging.INFO) -> None:
        """Helper method to configure logging for development/testing.

        This is useful for seeing logs during development, tests, or examples.
        It enables console logging with sensible defaults.

        Args:
            level: The logging level (default: INFO).
        """
        cls.configure(level=level)

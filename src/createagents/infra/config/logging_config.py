import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, List, Optional

from ...domain.interfaces import LoggerInterface
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


class LoggingConfig(LoggerInterface):
    """Production-ready logger implementation using Python's logging module.

    This adapter implements LoggerInterface for dependency inversion,
    allowing the domain layer to remain infrastructure-agnostic.

    Features:
    - Full logging.Logger API (debug, info, warning, error, critical, exception)
    - Global configuration management
    - Sensitive data filtering
    - JSON and text output formats
    - File rotation support
    - Environment-based configuration

    Example:
        >>> logger = create_logger(__name__)
        >>> logger.configure(level=logging.DEBUG)
        >>> logger.info('Application started')
        >>> logger.error('Failed to connect', exc_info=True)
    """

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_PATH = 'logs/app.log'

    def __init__(self, logger: logging.Logger):
        """Initialize with a Python logger instance.

        Args:
            logger: The underlying Python logger to use.
        """
        self._logger = logger

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with exception information.

        This method should be called from an exception handler.
        It automatically captures and logs the current exception traceback.
        """
        self._logger.exception(message, *args, **kwargs)

    def configure(
        self,
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
            log_file_path: Path to log file. Defaults to LOG_FILE_PATH env or 'logs/app.log'.
            max_bytes: Maximum file size before rotation (default: 10MB).
            backup_count: Number of backup files to keep (default: 5).
            json_format: Use JSON formatting for structured logs.
        """
        # Resolve configuration from environment if not explicitly provided
        if level is None:
            level = self._get_log_level_from_env()

        if not log_to_file:
            log_to_file = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'

        if log_file_path is None:
            log_file_path = os.getenv('LOG_FILE_PATH', self.DEFAULT_LOG_PATH)

        if not json_format:
            json_format = (
                os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
            )

        _LoggingState.log_level = level

        # Build format string
        if format_string is None:
            if include_timestamp:
                format_string = (
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            else:
                format_string = '%(name)s - %(levelname)s - %(message)s'

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        _LoggingState.handlers.clear()

        # Configure all existing loggers
        for logger_name in list(logging.Logger.manager.loggerDict):
            existing_logger = logging.getLogger(logger_name)
            existing_logger.setLevel(level)
            for handler in existing_logger.handlers[:]:
                existing_logger.removeHandler(handler)

        # Create formatter
        formatter: logging.Formatter
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = SensitiveDataFormatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        _LoggingState.handlers.append(console_handler)

        # File handler (optional)
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

    def reset(self) -> None:
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

    def set_level(self, level: int) -> None:
        """Adjust the logging level at runtime.

        Args:
            level: The new logging level (e.g., logging.DEBUG).
        """
        _LoggingState.log_level = level
        logging.getLogger().setLevel(level)

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

    @staticmethod
    def is_configured() -> bool:
        """Check if logging has been configured."""
        return _LoggingState.configured


def create_logger(name: str) -> LoggingConfig:
    """Factory function to create a logger instance.

    This is the primary entry point for obtaining loggers throughout
    the application. Use this instead of logging.getLogger() directly
    to ensure consistent LoggerInterface implementation.

    Args:
        name: The name for the logger (usually __name__).

    Returns:
        A LoggingConfig instance implementing LoggerInterface.

    Example:
        >>> from createagents.infra.config import create_logger
        >>> logger = create_logger(__name__)
        >>> logger.info('Service initialized')
    """
    python_logger = logging.getLogger(name)
    return LoggingConfig(python_logger)


def configure_logging(
    level: Optional[int] = None,
    json_format: bool = False,
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
) -> LoggingConfig:
    """Configure global logging and return a root logger.

    Convenience function to configure logging in one call.
    Typically called once at application startup.

    Args:
        level: Logging level (default: from LOG_LEVEL env or INFO).
        json_format: Use JSON formatting for structured logs.
        log_to_file: Enable file logging with rotation.
        log_file_path: Path to log file.

    Returns:
        A configured LoggingConfig instance.

    Example:
        >>> from createagents.infra.config import configure_logging
        >>> logger = configure_logging(level=logging.DEBUG)
        >>> logger.info('Logging configured')
    """
    logger = create_logger('createagents')
    logger.configure(
        level=level,
        json_format=json_format,
        log_to_file=log_to_file,
        log_file_path=log_file_path,
    )
    return logger

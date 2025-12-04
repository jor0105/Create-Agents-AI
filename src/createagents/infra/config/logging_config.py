import logging
from typing import Any, Optional

from ...domain.interfaces import LoggerInterface
from .logging_configurator import LoggingConfigurator


class LoggingConfig(LoggerInterface):
    """Production-ready logger implementation using Python's logging module.

    This adapter implements LoggerInterface for dependency inversion,
    allowing the domain layer to remain infrastructure-agnostic.

    Features:
    - Full logging.Logger API (debug, info, warning, error, critical, exception)
    - Sensitive data filtering via formatters (when configured)

    Example:
        >>> logger = create_logger(__name__)
        >>> logger.info('Application started')
        >>> logger.error('Failed to connect', exc_info=True)

    Note:
        For global logging configuration, use LoggingConfigurator directly:
        >>> LoggingConfigurator.configure(level=logging.DEBUG)
    """

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
        >>> from createagents import create_logger
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
        >>> from createagents import configure_logging
        >>> logger = configure_logging(level=logging.DEBUG)
        >>> logger.info('Logging configured')
    """
    LoggingConfigurator.configure(
        level=level,
        json_format=json_format,
        log_to_file=log_to_file,
        log_file_path=log_file_path,
    )
    return create_logger('createagents')

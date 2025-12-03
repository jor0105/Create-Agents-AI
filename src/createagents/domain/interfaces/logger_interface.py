"""Logger interface for dependency inversion.

This module defines the contract for logging functionality,
allowing the domain layer to use logging without depending
on specific infrastructure implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class LoggerInterface(ABC):
    """Unified logging interface for logging operations and configuration.

    This interface defines the complete contract for logging functionality,
    following the Dependency Inversion Principle (DIP) from SOLID.

    The domain layer depends on this abstraction, while infrastructure
    provides concrete implementations (e.g., LoggingConfig).

    Features:
    - Standard logging levels (debug, info, warning, error, critical)
    - Exception logging with automatic traceback capture
    - Global configuration management
    - Runtime level adjustment
    """

    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message.

        Use for detailed diagnostic information useful during development.

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra, stack_info).
        """

    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message.

        Use for general operational information about program execution.

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra, stack_info).
        """

    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message.

        Use for potentially problematic situations that don't prevent operation.

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra, stack_info).
        """

    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message.

        Use for error conditions that prevented an operation from completing.

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra, stack_info).
        """

    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message.

        Use for severe errors that may cause program termination.

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., exc_info, extra, stack_info).
        """

    @abstractmethod
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with exception information.

        This method should be called from within an exception handler.
        It automatically captures and logs the current exception traceback.

        Equivalent to error(message, exc_info=True).

        Args:
            message: The message to log (supports % formatting).
            *args: Positional arguments for string formatting.
            **kwargs: Keyword arguments (e.g., extra, stack_info).

        Example:
            try:
                risky_operation()
            except Exception:
                logger.exception('Operation failed')
        """

    @abstractmethod
    def configure(
        self,
        level: Optional[int] = None,
        format_string: Optional[str] = None,
        include_timestamp: bool = True,
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        json_format: bool = False,
    ) -> None:
        """Configure the logging system globally.

        Args:
            level: The logging level (e.g., logging.DEBUG, logging.INFO).
            format_string: A custom format string for log messages.
            include_timestamp: Whether to include timestamps in logs.
            log_to_file: Whether to enable file logging with rotation.
            log_file_path: The path to the log file.
            max_bytes: Maximum file size before rotation (default: 10MB).
            backup_count: Number of backup files to keep (default: 5).
            json_format: Whether to use structured JSON format.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the logging configuration.

        Removes all handlers and clears the configuration state.
        Useful for testing to ensure clean state between tests.
        """

    @abstractmethod
    def set_level(self, level: int) -> None:
        """Adjust the logging level at runtime.

        Args:
            level: The new logging level (e.g., logging.DEBUG, logging.INFO).
        """

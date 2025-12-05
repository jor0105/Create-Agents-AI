from abc import ABC, abstractmethod
from typing import Any


class LoggerInterface(ABC):
    """Interface for logging operations only.

    This interface defines the contract for logging functionality,
    following both DIP (Dependency Inversion Principle) and ISP
    (Interface Segregation Principle) from SOLID.

    The domain layer depends on this abstraction, while infrastructure
    provides concrete implementations (e.g., LoggingConfig).

    Features:
    - Standard logging levels (debug, info, warning, error, critical)
    - Exception logging with automatic traceback capture

    Note:
        Configuration is handled by LoggingConfigurator class in infra layer.
        This interface focuses solely on logging operations.
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

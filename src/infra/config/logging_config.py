"""Centralized logging configuration for the application.

This module provides a configurable logger that can be used
throughout the application for tracking and debugging.

Features:
- Automatic sensitive data filtering
- Log file rotation
- Configuration via environment variables
- Optional structured (JSON) logs
- Different handlers for console and file
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

from src.infra.config.sensitive_data_filter import SensitiveDataFilter


class ErrorOnlyFilter(logging.Filter):
    """A filter that only allows ERROR and CRITICAL messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Only allow ERROR and CRITICAL level messages."""
        return record.levelno >= logging.ERROR


class SensitiveDataFormatter(logging.Formatter):
    """A formatter that applies sensitive data filtering.

    This ensures that no sensitive data is logged.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record while filtering for sensitive data."""
        original = super().format(record)
        return SensitiveDataFilter.filter(original)


class JSONFormatter(logging.Formatter):
    """A formatter for structured JSON logs.

    This is useful for integration with log analysis tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record as a structured JSON object."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        json_str = json.dumps(log_data, ensure_ascii=False)
        return SensitiveDataFilter.filter(json_str)


class LoggingConfig:
    """A centralized configuration for logging.

    This class provides configured loggers for different modules, featuring:
    - Sensitive data filtering
    - Log file rotation
    - Configuration via environment variables
    """

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_PATH = "logs/app.log"

    _configured: bool = False
    _log_level: int = DEFAULT_LOG_LEVEL
    _handlers: List[logging.Handler] = []

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
        """Configures the application's logging.

        Args:
            level: The logging level (e.g., DEBUG, INFO). If None, it is read from the LOG_LEVEL environment variable.
            format_string: A custom format string (optional).
            include_timestamp: Whether to include a timestamp in the logs.
            log_to_file: Whether to log to a file in addition to the console.
            log_file_path: The path to the log file. If None, it uses the LOG_FILE_PATH environment variable.
            max_bytes: The maximum file size before rotation (default: 10MB).
            backup_count: The number of backup files to keep (default: 5).
            json_format: Whether to use a structured JSON format.
        """
        # Remove a verificação anterior - sempre reconfigurar se chamado
        # if cls._configured:
        #     return

        level = level or cls._get_log_level_from_env()
        log_to_file = log_to_file or os.getenv("LOG_TO_FILE", "false").lower() == "true"
        log_file_path = cls._resolve_log_file_path(log_file_path)
        json_format = (
            json_format or os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
        )

        cls._log_level = level

        if format_string is None:
            if include_timestamp:
                format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            else:
                format_string = "%(name)s - %(levelname)s - %(message)s"

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove todos os handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        cls._handlers.clear()

        # Força todos os loggers existentes a respeitarem o novo nível e adiciona filtro
        for logger_name in list(logging.Logger.manager.loggerDict):
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            # Remove handlers antigos
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            # Se nível é ERROR, adiciona filtro
            if level >= logging.ERROR:
                logger.addFilter(ErrorOnlyFilter())

        if json_format:
            formatter: logging.Formatter = JSONFormatter()
        else:
            formatter = SensitiveDataFormatter(format_string)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        # Se o nível é ERROR ou CRITICAL, adiciona um filtro para bloquear INFO/WARNING
        if level >= logging.ERROR:
            console_handler.addFilter(ErrorOnlyFilter())

        root_logger.addHandler(console_handler)
        cls._handlers.append(console_handler)

        if log_to_file:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(log_file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            # Se o nível é ERROR ou CRITICAL, adiciona um filtro para bloquear INFO/WARNING
            if level >= logging.ERROR:
                file_handler.addFilter(ErrorOnlyFilter())

            root_logger.addHandler(file_handler)
            cls._handlers.append(file_handler)

        cls._configured = True

    @classmethod
    def _resolve_log_file_path(cls, log_file_path: Optional[str]) -> str:
        """Resolves and validates the log file path.

        This method centralizes the logic for path validation to improve readability.

        Args:
            log_file_path: The provided path, or None.

        Returns:
            A valid path as a string.
        """
        default_path = os.getenv("LOG_FILE_PATH", cls.DEFAULT_LOG_PATH)

        if log_file_path is None or isinstance(log_file_path, bool):
            return default_path

        try:
            return str(log_file_path)
        except Exception:
            return default_path

    @classmethod
    def _get_log_level_from_env(cls) -> int:
        """Retrieves the log level from the LOG_LEVEL environment variable.

        Returns:
            The logging level (default: INFO).
        """
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_name, logging.INFO)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Retrieves a configured logger for the specified module.

        Args:
            name: The name of the module (usually `__name__`).

        Returns:
            A configured logger.
        """
        if not cls._configured:
            cls.configure()

        logger = logging.getLogger(name)
        logger.setLevel(cls._log_level)

        # Se o nível é ERROR, adiciona filtro ao logger
        if cls._log_level >= logging.ERROR:
            logger.addFilter(ErrorOnlyFilter())

        return logger

    @classmethod
    def set_level(cls, level: int) -> None:
        """Adjusts the logging level at runtime.

        Args:
            level: The new logging level.
        """
        cls._log_level = level
        logging.getLogger().setLevel(level)

    @classmethod
    def reset(cls) -> None:
        """Resets the logging configuration, which is useful for tests.

        This method removes all handlers and marks the configuration as not set.
        """
        cls._configured = False
        root_logger = logging.getLogger()

        for handler in cls._handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        cls._handlers.clear()
        SensitiveDataFilter.clear_cache()

    @classmethod
    def get_handlers(cls) -> list:
        """Returns a list of the configured handlers.

        Returns:
            A list of active handlers.
        """
        return cls._handlers.copy()

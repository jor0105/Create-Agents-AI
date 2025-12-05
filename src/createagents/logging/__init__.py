"""
Public Logging API for CreateAgentsAI.

This module exposes all necessary types for configuring and customizing
the logging system, including formatters, filters, and configuration utilities.

Quick Start
-----------
Basic configuration:

    >>> from createagents.logging import configure_logging
    >>> import logging
    >>> configure_logging(level=logging.INFO)

Creating a custom logger:

    >>> from createagents.logging import create_logger
    >>> logger = create_logger("my_module")
    >>> logger.info("Hello from my module!")

Module Contents
---------------
Configuration:
    configure_logging: Quick function to configure logging globally.
Interfaces:
    LoggerInterface: Abstract interface for custom logger implementations.

Factory:
    create_logger: Creates a configured logger instance.
"""

from .._private.domain import LoggerInterface
from .._private.infra import (
    configure_logging,
    create_logger,
)

__all__ = [
    # Configuration
    'configure_logging',
    # Interfaces
    'LoggerInterface',
    # Factory
    'create_logger',
]

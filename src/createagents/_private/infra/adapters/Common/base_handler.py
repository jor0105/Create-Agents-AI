from abc import ABC
from typing import Any, List, Optional

from ....domain import BaseTool, ToolExecutor
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    ITraceLogger,
    LoggerInterface,
)
from ....domain.services import LoggerFactory
from ...config import SensitiveDataFilter


class BaseHandler(ABC):
    """Base handler for LLM providers with tool execution support.

    This abstract base class centralizes common logic for all handlers:
    - Tool executor factory management
    - Common dependencies injection
    - Shared initialization logic
    - Sensitive data sanitization for logging

    Subclasses should implement specific API call logic while inheriting
    the common tool execution infrastructure.
    """

    def __init__(
        self,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        trace_logger: Optional[ITraceLogger] = None,
        logger_factory: Optional[LoggerFactory] = None,
    ):
        """Initialize the base handler with common dependencies.

        Args:
            logger: Logger instance for logging operations.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
            trace_logger: Optional trace logger for persistent tracing.
            logger_factory: Optional factory function to create loggers for tools.
        """
        self._logger = logger
        self._metrics_recorder = metrics_recorder
        self._schema_builder = schema_builder
        self._trace_logger = trace_logger
        self._logger_factory = logger_factory
        self._tool_executor_factory = self._default_tool_executor_factory

    def _default_tool_executor_factory(
        self, tools: Optional[List[BaseTool]]
    ) -> ToolExecutor:
        """Default factory for creating ToolExecutor instances.

        This method provides the standard way to create a ToolExecutor
        with the tools and logger. It can be overridden via constructor
        injection for testing or custom behavior.

        Args:
            tools: Optional list of tools to provide to the executor.

        Returns:
            Configured ToolExecutor instance.
        """
        if tools is None:
            tools = []
        return ToolExecutor(tools, self._logger, self._logger_factory)

    def _create_tool_executor(
        self, tools: Optional[List[BaseTool]]
    ) -> Optional[ToolExecutor]:
        """Create a tool executor if tools are provided.

        This is the centralized method for creating tool executors,
        ensuring consistent behavior across all handlers.

        Args:
            tools: Optional list of tools. If None or empty, returns None.

        Returns:
            ToolExecutor instance if tools provided, None otherwise.
        """
        if not tools:
            return None
        return self._tool_executor_factory(tools)

    def _sanitize_for_logging(self, data: Any) -> str:
        """Sanitize sensitive data before logging.

        This method ensures that sensitive data (API keys, passwords, PII)
        is redacted before being included in log entries.

        Args:
            data: Data to sanitize (dict, str, or any serializable type).

        Returns:
            Sanitized string representation safe for logging.
        """
        import json  # pylint: disable=import-outside-toplevel

        if data is None:
            return 'None'

        try:
            if isinstance(data, dict):
                data_str = json.dumps(data, default=str, ensure_ascii=False)
            else:
                data_str = str(data)
            return SensitiveDataFilter.filter(data_str)
        except (TypeError, ValueError):
            return '[SERIALIZATION_ERROR]'


__all__ = ['BaseHandler']

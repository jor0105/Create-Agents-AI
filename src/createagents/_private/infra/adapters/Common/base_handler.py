from abc import ABC
from typing import Any, List, Optional, Tuple

from ....domain import BaseTool, ToolExecutor
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    ITraceLogger,
    LoggerInterface,
)
from ....domain.services import LoggerFactory
from ....domain.value_objects import ToolChoice, ToolChoiceMode, ToolChoiceType
from ...config import SensitiveDataFilter


class BaseHandler(ABC):
    """Base handler for LLM providers with tool execution support.

    This abstract base class centralizes common logic for all handlers:
    - Tool executor factory management
    - Common dependencies injection
    - Shared initialization logic
    - Sensitive data sanitization for logging
    - Intelligent tool filtering based on tool_choice

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

    def _filter_tools_by_choice(
        self,
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[ToolChoiceType],
    ) -> Tuple[Optional[List[BaseTool]], bool]:
        """Filter tools based on tool_choice for optimized API calls.

        This method implements intelligent tool filtering:
        - tool_choice='none': Returns empty list (no tools sent to LLM)
        - tool_choice='auto'/'required': Returns all tools
        - tool_choice=specific("X"): Returns only tool X (token optimization)

        This optimization:
        1. Reduces token usage (fewer tool descriptions in context)
        2. Simulates tool_choice behavior for providers that don't support it (e.g., Ollama)
        3. Improves accuracy by limiting model choices

        Args:
            tools: Original list of tools available.
            tool_choice: The tool_choice configuration.

        Returns:
            Tuple of (filtered_tools, is_tool_choice_none):
            - filtered_tools: The filtered list of tools to send to API
            - is_tool_choice_none: True if tool_choice is 'none'
        """
        if not tools:
            return tools, False

        # Extract tool names for validation in from_value
        available_tool_names = [t.name for t in tools]

        # Parse tool_choice to ToolChoice value object
        parsed_choice = ToolChoice.from_value(
            tool_choice, available_tool_names
        )
        if parsed_choice is None:
            return tools, False

        # Check for 'none' mode - disable all tools
        if parsed_choice.mode == ToolChoiceMode.NONE:
            self._logger.debug(
                "tool_choice='none' - tools will be disabled for this request"
            )
            return [], True

        # Check for specific function mode - filter to only that tool
        if parsed_choice.is_specific_function and parsed_choice.function_name:
            target_name = parsed_choice.function_name
            filtered = [t for t in tools if t.name == target_name]

            if not filtered:
                self._logger.warning(
                    "tool_choice specifies '%s' but tool not found in list",
                    target_name,
                )
                return tools, False

            self._logger.debug(
                "tool_choice=specific('%s') - filtering to single tool",
                target_name,
            )
            return filtered, False

        # For 'auto' or 'required', return all tools
        return tools, False


__all__ = ['BaseHandler']

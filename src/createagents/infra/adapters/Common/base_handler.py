from abc import ABC
from typing import Callable, List, Optional

from ....domain import BaseTool, ToolExecutor
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    LoggerInterface,
)


class BaseHandler(ABC):
    """Base handler for LLM providers with tool execution support.

    This abstract base class centralizes common logic for all handlers:
    - Tool executor factory management
    - Common dependencies injection
    - Shared initialization logic

    Subclasses should implement specific API call logic while inheriting
    the common tool execution infrastructure.
    """

    def __init__(
        self,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder
    ):
        """Initialize the base handler with common dependencies.

        Args:
            logger: Logger instance for logging operations.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
        """
        self._logger = logger
        self._metrics_recorder = metrics_recorder
        self._schema_builder = schema_builder
        self._tool_executor_factory = (
            self._default_tool_executor_factory
        )

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
        return ToolExecutor(tools, self._logger)

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


__all__ = ['BaseHandler']

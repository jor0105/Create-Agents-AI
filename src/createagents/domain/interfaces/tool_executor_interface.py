from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..value_objects.tool_execution_result import ToolExecutionResult


class IToolExecutor(ABC):
    """Abstract interface for tool execution.

    This interface allows handlers to execute tools without
    coupling to specific implementations.
    """

    @abstractmethod
    def get_available_tool_names(self) -> List[str]:
        """Get list of available tool names.

        Returns:
            List of tool names that can be executed.
        """
        pass

    @abstractmethod
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if the tool exists, False otherwise.
        """
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        tool_call_id: Optional[str] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute.
            tool_call_id: Optional tool call ID for injection.
            agent_state: Optional agent state for injection.
            **kwargs: Arguments to pass to the tool.

        Returns:
            A ToolExecutionResult containing the execution outcome.
        """
        pass

    @abstractmethod
    async def execute_multiple_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        parallel: bool = False,
    ) -> List[ToolExecutionResult]:
        """Execute multiple tools in sequence or parallel.

        Args:
            tool_calls: List of tool call specifications.
            parallel: If True, execute tools in parallel.

        Returns:
            List of ToolExecutionResult objects.
        """
        pass


__all__ = ['IToolExecutor']

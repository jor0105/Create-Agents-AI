from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ..value_objects import BaseTool, ToolChoiceType


class IToolSchemaBuilder(ABC):
    """Abstract interface for tool schema building.

    This interface allows domain and application layers to format tools
    without knowing the specific provider implementation.

    Implementations format tools for OpenAI Responses API format,
    with optional strict mode support for structured outputs.
    """

    @abstractmethod
    def single_format(self, tool: BaseTool) -> Dict[str, Any]:
        """Convert a single tool to provider-specific format.

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for the provider's API.
        """
        pass

    @abstractmethod
    def multiple_format(self, tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert multiple tools to provider-specific format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for the provider's API.
        """
        pass

    @abstractmethod
    def format_tool_choice(
        self,
        tool_choice: Optional[ToolChoiceType],
        tools: Optional[List[BaseTool]] = None,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Format tool_choice parameter for provider API.

        Args:
            tool_choice: The tool_choice configuration from the user.
            tools: Optional list of available tools for validation.

        Returns:
            Formatted tool_choice for provider API, or None if not specified.
        """
        pass


__all__ = ['IToolSchemaBuilder']

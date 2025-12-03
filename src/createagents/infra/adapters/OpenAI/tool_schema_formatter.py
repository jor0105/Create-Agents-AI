from typing import Any, Dict, List, Optional, Union

from ....domain import BaseTool, ToolChoice, ToolChoiceType
from ...config import LoggingConfig


class ToolSchemaFormatter:
    """Formats tool schemas for OpenAI Responses API.

    This class converts domain-level tool schemas into the specific
    format required by OpenAI's Responses API function calling.

    Responsibilities:
    - Transform generic tool schemas to OpenAI Responses API format
    - Support strict mode for structured outputs
    - Ensure compliance with OpenAI's schema requirements
    - Keep provider-specific logic out of the domain layer
    """

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def format_tool(
        tool: BaseTool,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Convert a tool to OpenAI Responses API format.

        Args:
            tool: A BaseTool instance from the domain layer.
            strict: If True, enables strict mode for structured outputs.
                   This adds 'strict: true' and 'additionalProperties: false'
                   to ensure the model follows the schema exactly.

        Returns:
            A dictionary formatted for Responses API's tools parameter.
        """
        schema = tool.get_schema()

        ToolSchemaFormatter._logger.debug(
            "Formatting tool '%s' for OpenAI Responses API (strict=%s)",
            schema['name'],
            strict,
        )

        # Build parameters with optional strict mode
        parameters = schema['parameters'].copy()
        if strict:
            parameters['additionalProperties'] = False

        result: Dict[str, Any] = {
            'type': 'function',
            'name': schema['name'],
            'description': schema['description'],
            'parameters': parameters,
        }

        if strict:
            result['strict'] = True

        return result

    @staticmethod
    def format_tools(
        tools: List[BaseTool],
        strict: bool = False,
    ) -> List[Dict[str, Any]]:
        """Convert multiple tools to OpenAI Responses API format.

        Args:
            tools: List of BaseTool instances.
            strict: If True, enables strict mode for all tools.

        Returns:
            List of dictionaries formatted for Responses API's tools parameter.
        """
        ToolSchemaFormatter._logger.info(
            'Formatting %s tool(s) for OpenAI Responses API (strict=%s)',
            len(tools),
            strict,
        )

        formatted = [
            ToolSchemaFormatter.format_tool(tool, strict=strict)
            for tool in tools
        ]

        ToolSchemaFormatter._logger.debug(
            'Formatted tools: %s', [t['name'] for t in formatted]
        )

        return formatted

    @staticmethod
    def format_tool_choice(
        tool_choice: Optional[ToolChoiceType],
        tools: Optional[List[BaseTool]] = None,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Format tool_choice parameter for OpenAI API.

        Uses the domain ToolChoice value object for validation and formatting.

        Supports three main modes:
        - "auto": Let the model decide whether to call a tool (default)
        - "none": Force the model to not call any tool
        - "required": Force the model to call at least one tool
        - {"type": "function", "function": {"name": "tool_name"}}: Force a specific tool

        Args:
            tool_choice: The tool_choice configuration from the user.
            tools: Optional list of available tools for validation.

        Returns:
            Formatted tool_choice for OpenAI API, or None if not specified.

        Example:
            ```python
            # Let model decide
            format_tool_choice("auto")  # Returns "auto"

            # Force specific tool
            format_tool_choice({"type": "function", "function": {"name": "search"}})
            ```
        """
        if tool_choice is None:
            return None

        ToolSchemaFormatter._logger.debug(
            'Formatting tool_choice: %s', tool_choice
        )

        try:
            # Get available tool names for validation
            available_tools = [tool.name for tool in tools] if tools else None

            # Use domain ToolChoice for parsing and validation
            choice = ToolChoice.from_value(tool_choice, available_tools)

            if choice is None:
                return None

            return choice.to_openai_format()

        except ValueError as e:
            ToolSchemaFormatter._logger.warning(
                "Invalid tool_choice: %s. Using 'auto'.", e
            )
            return 'auto'

from typing import Any, Dict, List, Optional, Union

from ....domain import BaseTool, ToolChoice, ToolChoiceType
from ...config import LoggingConfig


class OllamaToolSchemaFormatter:
    """Formatter for Ollama native tool calling schemas.

    Converts BaseTool instances to Ollama's function calling format.

    Ollama expects tools in this format:
    ```python
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    ```
    """

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def format_tools_for_ollama(tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert BaseTool instances to Ollama's native tool format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of tool schemas in Ollama's format.

        Example:
            Input: [WebSearchTool()]
            Output: [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web...",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                ...
            ]
        """
        if not tools:
            OllamaToolSchemaFormatter._logger.debug('No tools to format')
            return []

        formatted_tools = []
        for tool in tools:
            try:
                schema = tool.get_schema()

                # Convert to Ollama's native format
                ollama_tool = {
                    'type': 'function',
                    'function': {
                        'name': schema['name'],
                        'description': schema['description'],
                        'parameters': schema['parameters'],
                    },
                }

                formatted_tools.append(ollama_tool)
                OllamaToolSchemaFormatter._logger.debug(
                    "Formatted tool '%s' for Ollama", schema['name']
                )
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                OllamaToolSchemaFormatter._logger.error(
                    'Error formatting tool %s: %s', tool.name, e, exc_info=True
                )
                continue

        OllamaToolSchemaFormatter._logger.info(
            'Formatted %s tool(s) for Ollama native API', len(formatted_tools)
        )
        return formatted_tools

    @staticmethod
    def format_tool_choice(
        tool_choice: Optional[ToolChoiceType],
        tools: Optional[List[BaseTool]] = None,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Format tool_choice parameter for Ollama API.

        Uses the domain ToolChoice value object for validation and formatting.

        Note: Ollama's support for tool_choice may be limited compared
        to OpenAI. This method provides the same interface for consistency.

        Args:
            tool_choice: The tool_choice configuration from the user.
            tools: Optional list of available tools for validation.

        Returns:
            Formatted tool_choice, or None if not specified.
        """
        if tool_choice is None:
            return None

        OllamaToolSchemaFormatter._logger.debug(
            'Formatting tool_choice for Ollama: %s', tool_choice
        )

        try:
            # Get available tool names for validation
            available_tools = [tool.name for tool in tools] if tools else None

            # Use domain ToolChoice for parsing and validation
            choice = ToolChoice.from_value(tool_choice, available_tools)

            if choice is None:
                return None

            # Ollama uses same format as OpenAI
            return choice.to_openai_format()

        except ValueError as e:
            OllamaToolSchemaFormatter._logger.warning(
                "Invalid tool_choice: %s. Using 'auto'.", e
            )
            return 'auto'

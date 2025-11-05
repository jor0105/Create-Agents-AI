"""Tool schema formatter for OpenAI.

This module is responsible for converting generic tool schemas
(from the domain layer) into OpenAI-specific formats.

This follows the Dependency Inversion Principle: the domain defines
a generic schema, and the infrastructure adapts it to specific providers.
"""

from typing import Any, Dict, List

from src.domain import BaseTool


class ToolSchemaFormatter:
    """Formats tool schemas for OpenAI API.

    This class converts domain-level tool schemas into the specific
    format required by OpenAI's function calling API.

    Responsibilities:
    - Transform generic tool schemas to OpenAI format
    - Ensure compliance with OpenAI's schema requirements
    - Keep provider-specific logic out of the domain layer
    """

    @staticmethod
    def format_tool_for_openai(tool: BaseTool) -> Dict[str, Any]:
        """Convert a tool to OpenAI function calling format.

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for OpenAI's tools parameter.

        Example:
            ```python
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
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
            }
            ```
        """
        schema = tool.get_schema()

        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["parameters"],
            },
        }

    @staticmethod
    def format_tools_for_openai(tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert multiple tools to OpenAI format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for OpenAI's tools parameter.
        """
        return [ToolSchemaFormatter.format_tool_for_openai(tool) for tool in tools]

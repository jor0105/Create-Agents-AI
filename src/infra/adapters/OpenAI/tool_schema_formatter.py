from typing import Any, Dict, List

from src.domain import BaseTool


class ToolSchemaFormatter:
    """Formats tool schemas for OpenAI API.

    This class converts domain-level tool schemas into the specific
    format required by OpenAI's function calling API and Responses API.

    Responsibilities:
    - Transform generic tool schemas to OpenAI format
    - Ensure compliance with OpenAI's schema requirements
    - Keep provider-specific logic out of the domain layer
    """

    @staticmethod
    def format_tool_for_openai(tool: BaseTool) -> Dict[str, Any]:
        """Convert a tool to OpenAI function calling format (Completions API).

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for OpenAI's tools parameter.
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
    def format_tool_for_responses_api(tool: BaseTool) -> Dict[str, Any]:
        """Convert a tool to OpenAI Responses API format.

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for Responses API's tools parameter.
        """
        schema = tool.get_schema()

        return {
            "type": "function",
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema["parameters"],
        }

    @staticmethod
    def format_tools_for_openai(tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert multiple tools to OpenAI Completions API format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for OpenAI's tools parameter.
        """
        return [ToolSchemaFormatter.format_tool_for_openai(tool) for tool in tools]

    @staticmethod
    def format_tools_for_responses_api(tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert multiple tools to OpenAI Responses API format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for Responses API's tools parameter.
        """
        return [
            ToolSchemaFormatter.format_tool_for_responses_api(tool) for tool in tools
        ]

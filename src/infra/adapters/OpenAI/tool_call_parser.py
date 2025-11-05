"""Tool call parser for OpenAI responses.

This module provides utilities for parsing and extracting tool calls
from OpenAI API responses, following the function calling specification.
"""

import json
from typing import Any, Dict, List, Optional


class ToolCallParser:
    """Parser for OpenAI tool calls.

    This class is responsible for extracting and parsing tool call information
    from OpenAI API responses. It handles the specific format that OpenAI uses
    for function calling.

    OpenAI returns tool calls in this format:
    ```python
    response.choices[0].message.tool_calls = [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "web_search",
                "arguments": '{"query": "Python tutorials"}'
            }
        }
    ]
    ```
    """

    @staticmethod
    def has_tool_calls(response: Any) -> bool:
        """Check if the response contains tool calls.

        Args:
            response: OpenAI API response object.

        Returns:
            True if tool calls are present, False otherwise.
        """
        try:
            message = response.choices[0].message
            return hasattr(message, "tool_calls") and message.tool_calls is not None
        except (AttributeError, IndexError, TypeError):
            return False

    @staticmethod
    def extract_tool_calls(response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI response.

        Args:
            response: OpenAI API response object.

        Returns:
            List of tool call dictionaries with 'id', 'name', and 'arguments' keys.
            Returns empty list if no tool calls are present.

        Example:
            ```python
            [
                {
                    "id": "call_abc123",
                    "name": "web_search",
                    "arguments": {"query": "Python tutorials"}
                }
            ]
            ```
        """
        if not ToolCallParser.has_tool_calls(response):
            return []

        tool_calls = []
        raw_tool_calls = response.choices[0].message.tool_calls

        for tool_call in raw_tool_calls:
            try:
                # Parse arguments from JSON string
                arguments_str = tool_call.function.arguments
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                else:
                    arguments = arguments_str

                tool_calls.append(
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": arguments,
                    }
                )
            except (json.JSONDecodeError, AttributeError) as e:
                # Log error but continue processing other tool calls
                print(f"Warning: Failed to parse tool call: {e}")
                continue

        return tool_calls

    @staticmethod
    def format_tool_results_for_llm(
        tool_call_id: str, tool_name: str, result: str
    ) -> Dict[str, Any]:
        """Format tool execution result for sending back to OpenAI.

        OpenAI expects tool results in a specific format to continue the conversation.

        Args:
            tool_call_id: The ID of the tool call (from the original response).
            tool_name: Name of the tool that was executed.
            result: The result of the tool execution.

        Returns:
            A dictionary formatted for OpenAI's messages array.

        Example:
            ```python
            {
                "role": "tool",
                "tool_call_id": "call_abc123",
                "name": "web_search",
                "content": "Search results: ..."
            }
            ```
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": str(result),
        }

    @staticmethod
    def get_assistant_message_with_tool_calls(
        response: Any,
    ) -> Optional[Dict[str, Any]]:
        """Extract the assistant message that contains tool calls.

        This is needed to maintain conversation context when tools are called.

        Args:
            response: OpenAI API response object.

        Returns:
            Dictionary representing the assistant message, or None if not available.
        """
        if not ToolCallParser.has_tool_calls(response):
            return None

        try:
            message = response.choices[0].message

            # Convert tool_calls to dict format
            tool_calls_list = []
            for tc in message.tool_calls:
                tool_calls_list.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )

            return {
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls_list,
            }
        except (AttributeError, IndexError):
            return None

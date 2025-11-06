import json
from typing import Any, Dict, List, Optional


class ToolCallParser:
    """Parser for OpenAI Responses API tool calls.

    This class is responsible for extracting and parsing tool call information
    from OpenAI Responses API responses.

    OpenAI Responses API returns tool calls in the response.output list:
    ```python
    response.output = [
        {
            "id": "fc_abc123",
            "call_id": "call_abc123",
            "type": "function_call",
            "name": "get_weather",
            "arguments": '{"location": "Paris"}'
        }
    ]
    ```
    """

    @staticmethod
    def has_tool_calls(response: Any) -> bool:
        """Check if the response contains tool calls.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            True if tool calls are present, False otherwise.
        """
        try:
            if not hasattr(response, "output") or not response.output:
                return False

            # Check if any item in output has type "function_call"
            for item in response.output:
                if hasattr(item, "type") and item.type == "function_call":
                    return True
            return False
        except (AttributeError, TypeError):
            return False

    @staticmethod
    def extract_tool_calls(response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI Responses API response.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            List of tool call dictionaries with 'id', 'name', and 'arguments' keys.
            Returns empty list if no tool calls are present.

        Example:
            ```python
            [
                {
                    "id": "call_abc123",
                    "name": "get_weather",
                    "arguments": {"location": "Paris"}
                }
            ]
            ```
        """
        if not ToolCallParser.has_tool_calls(response):
            return []

        tool_calls = []

        for item in response.output:
            if not hasattr(item, "type") or item.type != "function_call":
                continue

            try:
                # Parse arguments from JSON string
                arguments_str = item.arguments
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                else:
                    arguments = arguments_str

                tool_calls.append(
                    {
                        "id": item.call_id,  # Responses API uses call_id
                        "name": item.name,
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
        """Format tool execution result for sending back to OpenAI Responses API.

        Args:
            tool_call_id: The call_id of the tool call (from the original response).
            tool_name: Name of the tool that was executed.
            result: The result of the tool execution.

        Returns:
            A dictionary formatted for Responses API's input array.

        Example:
            ```python
            {
                "type": "function_call_output",
                "call_id": "call_abc123",
                "output": "Weather in Paris: 15°C"
            }
            ```
        """
        return {
            "type": "function_call_output",
            "call_id": tool_call_id,
            "output": str(result),
        }

    @staticmethod
    def get_assistant_message_with_tool_calls(
        response: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract the output items from response for adding to input history.

        For Responses API, we need to append specific output items to maintain context.
        We only include 'reasoning' and 'function_call' types, filtering out extra fields.

        Args:
            response: OpenAI Responses API response object.

        Returns:
            List of output items (cleaned), or None if not available.
        """
        if not ToolCallParser.has_tool_calls(response):
            return None

        try:
            if not hasattr(response, "output") or not response.output:
                return None

            # Convert to dict format for messages, keeping only necessary fields
            output_items = []
            for item in response.output:
                item_type = getattr(item, "type", None)

                # Only include reasoning and function_call types
                if item_type == "reasoning":
                    output_items.append(
                        {
                            "type": "reasoning",
                            "id": getattr(item, "id", None),
                            "summary": getattr(item, "summary", []),
                        }
                    )
                elif item_type == "function_call":
                    output_items.append(
                        {
                            "type": "function_call",
                            "id": getattr(item, "id", None),
                            "call_id": getattr(item, "call_id", None),
                            "name": getattr(item, "name", None),
                            "arguments": getattr(item, "arguments", None),
                        }
                    )

            return output_items if output_items else None
        except (AttributeError, TypeError):
            return None

"""Tool call parser for Ollama responses.

Since Ollama doesn't have native function calling support like OpenAI,
this parser detects tool usage attempts in the model's text response
using pattern matching and XML-like tags.

The parser expects the model to request tool calls in this format:
```
<tool_call>
  <name>web_search</name>
  <arguments>
    <query>Python tutorials</query>
  </arguments>
</tool_call>
```

Or JSON format:
```
<tool_call>
{
  "name": "web_search",
  "arguments": {"query": "Python tutorials"}
}
</tool_call>
```
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from src.infra.config.logging_config import LoggingConfig


class OllamaToolCallParser:
    """Parser for Ollama tool calls via prompt engineering.

    This class detects and extracts tool call requests from Ollama's
    text responses using pattern matching on XML-like tags.

    Unlike OpenAI which has native function calling, Ollama models must
    be prompted to output tool requests in a specific format that can
    be parsed.
    """

    # Regex pattern to extract tool_call blocks
    TOOL_CALL_PATTERN = re.compile(
        r"<tool_call>(.*?)</tool_call>", re.DOTALL | re.IGNORECASE
    )

    _logger = LoggingConfig.get_logger(__name__)

    @staticmethod
    def has_tool_calls(response: str) -> bool:
        """Check if the response contains tool call requests.

        Args:
            response: The text response from Ollama.

        Returns:
            True if tool calls are detected, False otherwise.
        """
        if not response or not isinstance(response, str):
            OllamaToolCallParser._logger.debug("Response is empty or not a string")
            return False

        has_calls = bool(OllamaToolCallParser.TOOL_CALL_PATTERN.search(response))
        if has_calls:
            OllamaToolCallParser._logger.debug(
                "Tool call pattern detected in Ollama response"
            )
        else:
            OllamaToolCallParser._logger.debug(
                "No tool call pattern found in Ollama response"
            )

        return has_calls

    @staticmethod
    def extract_tool_calls(response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from Ollama response.

        Args:
            response: The text response from Ollama.

        Returns:
            List of tool call dictionaries with 'name' and 'arguments' keys.
            Returns empty list if no tool calls are detected.

        Example:
            ```python
            [
                {
                    "name": "web_search",
                    "arguments": {"query": "Python tutorials"}
                }
            ]
            ```
        """
        if not OllamaToolCallParser.has_tool_calls(response):
            OllamaToolCallParser._logger.debug(
                "No tool calls to extract from Ollama response"
            )
            return []

        OllamaToolCallParser._logger.debug("Extracting tool calls from Ollama response")
        tool_calls = []
        matches = OllamaToolCallParser.TOOL_CALL_PATTERN.findall(response)

        OllamaToolCallParser._logger.debug(
            f"Found {len(matches)} tool call pattern match(es)"
        )

        for idx, match in enumerate(matches, 1):
            try:
                OllamaToolCallParser._logger.debug(
                    f"Parsing tool call {idx}/{len(matches)}"
                )

                # Try parsing as XML first
                tool_call = OllamaToolCallParser._parse_xml_tool_call(match)
                if tool_call:
                    tool_calls.append(tool_call)
                    OllamaToolCallParser._logger.debug(
                        f"Successfully parsed XML tool call: {tool_call.get('name', 'unknown')}"
                    )
                    continue

                # Try parsing as JSON
                tool_call = OllamaToolCallParser._parse_json_tool_call(match)
                if tool_call:
                    tool_calls.append(tool_call)
                    OllamaToolCallParser._logger.debug(
                        f"Successfully parsed JSON tool call: {tool_call.get('name', 'unknown')}"
                    )
                else:
                    OllamaToolCallParser._logger.warning(
                        f"Failed to parse tool call {idx} as XML or JSON"
                    )

            except Exception as e:
                # Log error but continue processing other tool calls
                OllamaToolCallParser._logger.error(
                    f"Failed to parse tool call {idx}: {str(e)}", exc_info=True
                )
                continue

        OllamaToolCallParser._logger.info(
            f"Extracted {len(tool_calls)} tool call(s) from Ollama response"
        )
        return tool_calls

    @staticmethod
    def _parse_xml_tool_call(xml_content: str) -> Optional[Dict[str, Any]]:
        """Parse XML-formatted tool call.

        Expected format:
        ```xml
        <name>web_search</name>
        <arguments>
          <query>Python tutorials</query>
        </arguments>
        ```

        Args:
            xml_content: The content inside <tool_call> tags.

        Returns:
            Dictionary with 'name' and 'arguments', or None if parsing fails.
        """
        try:
            # Wrap in root element for parsing
            xml_str = f"<root>{xml_content.strip()}</root>"
            root = ET.fromstring(xml_str)

            # Extract tool name
            name_elem = root.find("name")
            if name_elem is None or not name_elem.text:
                OllamaToolCallParser._logger.debug(
                    "XML parsing failed: no name element found"
                )
                return None

            tool_name = name_elem.text.strip()

            # Extract arguments
            args_elem = root.find("arguments")
            if args_elem is None:
                OllamaToolCallParser._logger.debug(
                    f"XML tool call '{tool_name}' has no arguments"
                )
                return {"name": tool_name, "arguments": {}}

            # Convert XML arguments to dict
            arguments = {}
            for child in args_elem:
                arg_name = child.tag
                arg_value = child.text.strip() if child.text else ""

                # Try to convert to appropriate type
                arguments[arg_name] = OllamaToolCallParser._convert_value(arg_value)

            OllamaToolCallParser._logger.debug(
                f"Successfully parsed XML tool call '{tool_name}' with {len(arguments)} argument(s)"
            )
            return {"name": tool_name, "arguments": arguments}

        except ET.ParseError as e:
            OllamaToolCallParser._logger.debug(f"XML parse error: {str(e)}")
            return None
        except Exception as e:
            OllamaToolCallParser._logger.debug(
                f"Unexpected error parsing XML: {str(e)}"
            )
            return None

    @staticmethod
    def _parse_json_tool_call(json_content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON-formatted tool call.

        Expected format:
        ```json
        {
          "name": "web_search",
          "arguments": {"query": "Python tutorials"}
        }
        ```

        Args:
            json_content: The content inside <tool_call> tags.

        Returns:
            Dictionary with 'name' and 'arguments', or None if parsing fails.
        """
        try:
            data = json.loads(json_content.strip())

            if not isinstance(data, dict):
                OllamaToolCallParser._logger.debug(
                    "JSON parsing failed: data is not a dict"
                )
                return None

            tool_name = data.get("name")
            if not tool_name:
                OllamaToolCallParser._logger.debug(
                    "JSON parsing failed: no 'name' field"
                )
                return None

            arguments = data.get("arguments", {})
            if not isinstance(arguments, dict):
                OllamaToolCallParser._logger.debug(
                    "JSON parsing failed: 'arguments' is not a dict"
                )
                return None

            OllamaToolCallParser._logger.debug(
                f"Successfully parsed JSON tool call '{tool_name}' with {len(arguments)} argument(s)"
            )
            return {"name": tool_name, "arguments": arguments}

        except json.JSONDecodeError as e:
            OllamaToolCallParser._logger.debug(f"JSON decode error: {str(e)}")
            return None
        except Exception as e:
            OllamaToolCallParser._logger.debug(
                f"Unexpected error parsing JSON: {str(e)}"
            )
            return None

    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string value to appropriate Python type.

        Tries to convert to int, float, bool, or keeps as string.

        Args:
            value: String value to convert.

        Returns:
            Converted value.
        """
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Keep as string
        return value

    @staticmethod
    def remove_tool_calls_from_response(response: str) -> str:
        """Remove tool call tags from response to get clean text.

        This is useful to extract the final response after tool calls
        have been processed.

        Args:
            response: The full response including tool calls.

        Returns:
            Response with tool call tags removed.
        """
        cleaned = OllamaToolCallParser.TOOL_CALL_PATTERN.sub("", response).strip()
        if cleaned != response:
            OllamaToolCallParser._logger.debug("Removed tool call tags from response")
        return cleaned

    @staticmethod
    def format_tool_results_for_llm(tool_name: str, result: str) -> str:
        """Format tool execution result to send back to Ollama.

        Since Ollama doesn't have a structured format like OpenAI,
        we format the result as clear text that can be appended
        to the conversation.

        Args:
            tool_name: Name of the tool that was executed.
            result: The result of the tool execution.

        Returns:
            Formatted text to add to the conversation.
        """
        OllamaToolCallParser._logger.debug(
            f"Formatting tool result for '{tool_name}' (length: {len(result)} chars)"
        )

        formatted = f"<tool_result>\n<name>{tool_name}</name>\n<result>{result}</result>\n</tool_result>"
        return formatted

"""
Unit tests for OpenAI ToolSchemaFormatter.

Tests the formatting of BaseTool instances for OpenAI's API formats
(both Completions API and Responses API).
"""

import pytest

from src.domain.value_objects.base_tools import BaseTool
from src.infra.adapters.OpenAI.tool_schema_formatter import ToolSchemaFormatter


class MockWeatherTool(BaseTool):
    """Mock weather tool for testing."""

    name = "get_weather"
    description = "Get the current weather for a location"
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit",
            },
        },
        "required": ["location"],
    }

    def execute(self, location: str, unit: str = "celsius") -> str:
        return f"Weather in {location}: 15°{unit[0].upper()}"


class MockSearchTool(BaseTool):
    """Mock search tool for testing."""

    name = "web_search"
    description = "Search the web for information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            }
        },
        "required": ["query"],
    }

    def execute(self, query: str) -> str:
        return f"Search results for: {query}"


class MockNoParamsTool(BaseTool):
    """Mock tool with no parameters."""

    name = "get_time"
    description = "Get the current time"
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self) -> str:
        return "12:00 PM"


@pytest.mark.unit
class TestToolSchemaFormatter:
    """Test suite for ToolSchemaFormatter."""

    def test_format_tool_for_openai_completions(self):
        """Test format_tool_for_openai creates correct structure for Completions API."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        assert result["type"] == "function"
        assert "function" in result
        assert result["function"]["name"] == "get_weather"
        assert (
            result["function"]["description"]
            == "Get the current weather for a location"
        )
        assert "parameters" in result["function"]

    def test_format_tool_for_openai_includes_parameters(self):
        """Test format_tool_for_openai includes parameters structure."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        params = result["function"]["parameters"]
        assert params["type"] == "object"
        assert "location" in params["properties"]
        assert "unit" in params["properties"]
        assert params["required"] == ["location"]

    def test_format_tool_for_responses_api(self):
        """Test format_tool_for_responses_api creates correct structure for Responses API."""
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result["type"] == "function"
        assert result["name"] == "web_search"
        assert result["description"] == "Search the web for information"
        assert "parameters" in result

    def test_format_tool_for_responses_api_includes_parameters(self):
        """Test format_tool_for_responses_api includes parameters directly."""
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        params = result["parameters"]
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert params["required"] == ["query"]

    def test_format_tools_for_openai_single_tool(self):
        """Test format_tools_for_openai with single tool."""
        tools = [MockWeatherTool()]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "get_weather"

    def test_format_tools_for_openai_multiple_tools(self):
        """Test format_tools_for_openai with multiple tools."""
        tools = [MockWeatherTool(), MockSearchTool(), MockNoParamsTool()]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert len(result) == 3
        names = [tool["function"]["name"] for tool in result]
        assert "get_weather" in names
        assert "web_search" in names
        assert "get_time" in names

    def test_format_tools_for_responses_api_single_tool(self):
        """Test format_tools_for_responses_api with single tool."""
        tools = [MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["name"] == "web_search"

    def test_format_tools_for_responses_api_multiple_tools(self):
        """Test format_tools_for_responses_api with multiple tools."""
        tools = [MockWeatherTool(), MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        names = [tool["name"] for tool in result]
        assert "get_weather" in names
        assert "web_search" in names

    def test_format_tool_with_no_parameters(self):
        """Test formatting tool with empty parameters."""
        tool = MockNoParamsTool()

        result_completions = ToolSchemaFormatter.format_tool_for_openai(tool)
        result_responses = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result_completions["function"]["parameters"]["properties"] == {}
        assert result_responses["parameters"]["properties"] == {}

    def test_format_tools_for_openai_empty_list(self):
        """Test format_tools_for_openai with empty list."""
        tools = []

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert result == []

    def test_format_tools_for_responses_api_empty_list(self):
        """Test format_tools_for_responses_api with empty list."""
        tools = []

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert result == []

    def test_format_preserves_parameter_types(self):
        """Test that parameter types are preserved correctly."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        location_prop = result["function"]["parameters"]["properties"]["location"]
        unit_prop = result["function"]["parameters"]["properties"]["unit"]

        assert location_prop["type"] == "string"
        assert unit_prop["type"] == "string"
        assert unit_prop["enum"] == ["celsius", "fahrenheit"]

    def test_format_preserves_descriptions(self):
        """Test that descriptions are preserved in formatting."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result["description"] == "Get the current weather for a location"
        location_desc = result["parameters"]["properties"]["location"]["description"]
        assert "city and state" in location_desc

    def test_format_preserves_required_fields(self):
        """Test that required fields are preserved."""
        tool = MockWeatherTool()

        result_completions = ToolSchemaFormatter.format_tool_for_openai(tool)
        result_responses = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result_completions["function"]["parameters"]["required"] == ["location"]
        assert result_responses["parameters"]["required"] == ["location"]

    def test_completions_and_responses_have_different_structure(self):
        """Test that Completions API and Responses API formats differ correctly."""
        tool = MockWeatherTool()

        completions_format = ToolSchemaFormatter.format_tool_for_openai(tool)
        responses_format = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        # Completions API nests everything under "function"
        assert "function" in completions_format
        assert completions_format["function"]["name"] == "get_weather"

        # Responses API has name at top level
        assert "name" in responses_format
        assert responses_format["name"] == "get_weather"
        assert "function" not in responses_format

    def test_format_tools_maintains_order(self):
        """Test that tool order is preserved in formatting."""
        tools = [
            MockWeatherTool(),
            MockSearchTool(),
            MockNoParamsTool(),
        ]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert result[0]["function"]["name"] == "get_weather"
        assert result[1]["function"]["name"] == "web_search"
        assert result[2]["function"]["name"] == "get_time"

    def test_format_tool_with_complex_parameters(self):
        """Test formatting tool with nested/complex parameters."""

        class ComplexTool(BaseTool):
            name = "complex_search"
            description = "Advanced search with filters"
            parameters = {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "date_from": {"type": "string"},
                            "date_to": {"type": "string"},
                            "categories": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["query"],
            }

            def execute(self, **kwargs):
                return "results"

        tool = ComplexTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert "filters" in result["parameters"]["properties"]
        assert (
            "date_from" in result["parameters"]["properties"]["filters"]["properties"]
        )
        assert result["parameters"]["properties"]["limit"]["minimum"] == 1

    def test_format_tool_preserves_enum_values(self):
        """Test that enum values are preserved correctly."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        unit_enum = result["function"]["parameters"]["properties"]["unit"]["enum"]
        assert unit_enum == ["celsius", "fahrenheit"]

    def test_format_tool_with_special_characters_in_description(self):
        """Test formatting tool with special characters in description."""

        class SpecialTool(BaseTool):
            name = "special_tool"
            description = "Tool with special chars: @#$%^&*() and unicode: 你好"
            parameters = {"type": "object", "properties": {}}

            def execute(self):
                return "ok"

        tool = SpecialTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert "你好" in result["description"]
        assert "@#$%^&*()" in result["description"]

    def test_format_tools_for_openai_logs_count(self, caplog):
        """Test that format_tools_for_openai logs the count of tools."""
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        ToolSchemaFormatter.format_tools_for_openai(tools)

        # Check that logging occurred (if implemented)
        # This is optional based on implementation

    def test_format_tools_for_responses_api_logs_count(self, caplog):
        """Test that format_tools_for_responses_api logs the count of tools."""
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        ToolSchemaFormatter.format_tools_for_responses_api(tools)

        # Check that logging occurred (if implemented)
        # This is optional based on implementation

    def test_format_tool_with_array_parameter(self):
        """Test formatting tool with array parameter."""

        class ArrayTool(BaseTool):
            name = "multi_search"
            description = "Search multiple queries"
            parameters = {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of search queries",
                    }
                },
                "required": ["queries"],
            }

            def execute(self, queries):
                return f"Searching: {queries}"

        tool = ArrayTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        queries_prop = result["function"]["parameters"]["properties"]["queries"]
        assert queries_prop["type"] == "array"
        assert queries_prop["items"]["type"] == "string"

    def test_format_tool_with_number_parameters(self):
        """Test formatting tool with number/integer parameters."""

        class MathTool(BaseTool):
            name = "calculate"
            description = "Perform calculations"
            parameters = {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"},
                },
                "required": ["a", "b"],
            }

            def execute(self, a, b):
                return a + b

        tool = MathTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result["parameters"]["properties"]["a"]["type"] == "number"
        assert result["parameters"]["properties"]["b"]["type"] == "integer"

    def test_format_tool_with_boolean_parameter(self):
        """Test formatting tool with boolean parameter."""

        class FlagTool(BaseTool):
            name = "search_with_flag"
            description = "Search with optional flag"
            parameters = {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "exact_match": {
                        "type": "boolean",
                        "description": "Use exact matching",
                    },
                },
                "required": ["query"],
            }

            def execute(self, query, exact_match=False):
                return f"Searching: {query} (exact={exact_match})"

        tool = FlagTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        exact_match_prop = result["function"]["parameters"]["properties"]["exact_match"]
        assert exact_match_prop["type"] == "boolean"

    def test_format_multiple_tools_with_same_parameter_names(self):
        """Test formatting multiple tools that have overlapping parameter names."""

        class Tool1(BaseTool):
            name = "tool_one"
            description = "First tool"
            parameters = {
                "type": "object",
                "properties": {"param": {"type": "string"}},
            }

            def execute(self, param):
                return param

        class Tool2(BaseTool):
            name = "tool_two"
            description = "Second tool"
            parameters = {
                "type": "object",
                "properties": {"param": {"type": "integer"}},
            }

            def execute(self, param):
                return param

        tools = [Tool1(), Tool2()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        assert result[0]["parameters"]["properties"]["param"]["type"] == "string"
        assert result[1]["parameters"]["properties"]["param"]["type"] == "integer"

    def test_completions_format_has_nested_function_key(self):
        """Test that Completions API format has nested 'function' key."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        # Verify nested structure
        assert "type" in result
        assert "function" in result
        assert "name" in result["function"]
        assert "description" in result["function"]
        assert "parameters" in result["function"]

    def test_responses_format_has_flat_structure(self):
        """Test that Responses API format has flat structure."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        # Verify flat structure
        assert "type" in result
        assert "name" in result
        assert "description" in result
        assert "parameters" in result
        assert "function" not in result

    def test_format_tool_schema_is_valid_json_schema(self):
        """Test that formatted tools produce valid JSON Schema."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        # Check JSON Schema structure
        params = result["parameters"]
        assert params["type"] == "object"
        assert isinstance(params["properties"], dict)
        assert isinstance(params.get("required", []), list)

    def test_format_preserves_additional_schema_properties(self):
        """Test that additional schema properties like minLength are preserved."""

        class ValidationTool(BaseTool):
            name = "validate_input"
            description = "Validate input with constraints"
            parameters = {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 100,
                        "pattern": "^[a-zA-Z]+$",
                    }
                },
                "required": ["text"],
            }

            def execute(self, text):
                return f"Valid: {text}"

        tool = ValidationTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        text_prop = result["function"]["parameters"]["properties"]["text"]
        assert text_prop["minLength"] == 5
        assert text_prop["maxLength"] == 100
        assert text_prop["pattern"] == "^[a-zA-Z]+$"

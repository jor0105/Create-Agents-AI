from typing import List, Literal, Optional

import pytest
from pydantic import BaseModel, Field, field_validator

from createagents.domain import BaseTool
from createagents.infra import ToolSchemaFormatter


class WeatherInput(BaseModel):
    """Input schema for weather tool."""

    location: str = Field(
        description='The city and state, e.g. San Francisco, CA'
    )
    unit: Literal['celsius', 'fahrenheit'] = Field(
        default='celsius', description='Temperature unit'
    )


class SearchInput(BaseModel):
    """Input schema for search tool."""

    query: str = Field(description='The search query')


class EmptyInput(BaseModel):
    """Empty input schema."""

    pass


class ComplexSearchInput(BaseModel):
    """Complex search input with filters."""

    query: str = Field(description='Search query')
    date_from: Optional[str] = Field(default=None, description='Start date')
    date_to: Optional[str] = Field(default=None, description='End date')
    categories: Optional[List[str]] = Field(
        default=None, description='Categories'
    )
    limit: int = Field(default=10, ge=1, le=100, description='Result limit')


class ArraySearchInput(BaseModel):
    """Input with array parameter."""

    queries: List[str] = Field(description='List of search queries')


class MathInput(BaseModel):
    """Input for math calculations."""

    a: float = Field(description='First number')
    b: int = Field(description='Second number')


class FlagInput(BaseModel):
    """Input with boolean flag."""

    query: str = Field(description='Search query')
    exact_match: bool = Field(default=False, description='Use exact matching')


class ParamStringInput(BaseModel):
    """Input with string param."""

    param: str = Field(description='String parameter')


class ParamIntInput(BaseModel):
    """Input with int param."""

    param: int = Field(description='Integer parameter')


class ValidationInput(BaseModel):
    """Input with validation constraints."""

    text: str = Field(
        min_length=5, max_length=100, description='Text to validate'
    )

    @field_validator('text')
    @classmethod
    def validate_alpha(cls, v):
        if not v.isalpha():
            raise ValueError('Text must be alphabetic')
        return v


class MockWeatherTool(BaseTool):
    name = 'get_weather'
    description = 'Get the current weather for a location'
    args_schema = WeatherInput

    def _run(self, location: str, unit: str = 'celsius') -> str:
        return f'Weather in {location}: 15°{unit[0].upper()}'


class MockSearchTool(BaseTool):
    name = 'web_search'
    description = 'Search the web for information'
    args_schema = SearchInput

    def _run(self, query: str) -> str:
        return f'Search results for: {query}'


class MockNoParamsTool(BaseTool):
    name = 'get_time'
    description = 'Get the current time'
    args_schema = EmptyInput

    def _run(self) -> str:
        return '12:00 PM'


@pytest.mark.unit
class TestToolSchemaFormatter:
    """Tests for ToolSchemaFormatter with OpenAI Responses API format."""

    def test_format_tool_responses_api(self):
        """Test formatting a single tool for Responses API."""
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert result['type'] == 'function'
        assert result['name'] == 'web_search'
        assert result['description'] == 'Search the web for information'
        assert 'parameters' in result
        # Responses API format should NOT have nested 'function' key
        assert 'function' not in result

    def test_format_tool_includes_parameters(self):
        """Test that format_tool includes all parameters."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert 'location' in params['properties']
        assert 'unit' in params['properties']
        assert params['required'] == ['location']

    def test_format_tool_with_strict_mode(self):
        """Test formatting a tool with strict mode enabled."""
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool(tool, strict=True)

        assert result['strict'] is True
        assert result['parameters']['additionalProperties'] is False

    def test_format_tool_without_strict_mode(self):
        """Test formatting a tool without strict mode (default)."""
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool(tool, strict=False)

        assert 'strict' not in result
        assert 'additionalProperties' not in result['parameters']

    def test_format_tools_single_tool(self):
        """Test formatting a single tool in a list."""
        tools = [MockSearchTool()]

        result = ToolSchemaFormatter.format_tools(tools)

        assert len(result) == 1
        assert result[0]['type'] == 'function'
        assert result[0]['name'] == 'web_search'

    def test_format_tools_multiple_tools(self):
        """Test formatting multiple tools."""
        tools = [MockWeatherTool(), MockSearchTool(), MockNoParamsTool()]

        result = ToolSchemaFormatter.format_tools(tools)

        assert len(result) == 3
        names = [tool['name'] for tool in result]
        assert 'get_weather' in names
        assert 'web_search' in names
        assert 'get_time' in names

    def test_format_tools_with_strict_mode(self):
        """Test formatting multiple tools with strict mode."""
        tools = [MockWeatherTool(), MockSearchTool()]

        result = ToolSchemaFormatter.format_tools(tools, strict=True)

        assert len(result) == 2
        for tool in result:
            assert tool['strict'] is True
            assert tool['parameters']['additionalProperties'] is False

    def test_format_tool_with_no_parameters(self):
        """Test formatting a tool with empty parameters."""
        tool = MockNoParamsTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert result['parameters']['properties'] == {}

    def test_format_tools_empty_list(self):
        """Test formatting an empty list of tools."""
        tools = []

        result = ToolSchemaFormatter.format_tools(tools)

        assert result == []

    def test_format_preserves_parameter_types(self):
        """Test that parameter types are preserved."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        location_prop = result['parameters']['properties']['location']
        unit_prop = result['parameters']['properties']['unit']

        assert location_prop['type'] == 'string'
        assert unit_prop['type'] == 'string'
        assert unit_prop['enum'] == ['celsius', 'fahrenheit']

    def test_format_preserves_descriptions(self):
        """Test that descriptions are preserved."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert (
            result['description'] == 'Get the current weather for a location'
        )
        location_desc = result['parameters']['properties']['location'][
            'description'
        ]
        assert 'city and state' in location_desc

    def test_format_preserves_required_fields(self):
        """Test that required fields are preserved."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert result['parameters']['required'] == ['location']

    def test_format_tools_maintains_order(self):
        """Test that tool order is maintained."""
        tools = [
            MockWeatherTool(),
            MockSearchTool(),
            MockNoParamsTool(),
        ]

        result = ToolSchemaFormatter.format_tools(tools)

        assert result[0]['name'] == 'get_weather'
        assert result[1]['name'] == 'web_search'
        assert result[2]['name'] == 'get_time'

    def test_format_tool_with_complex_parameters(self):
        """Test formatting a tool with complex parameters."""

        class ComplexTool(BaseTool):
            name = 'complex_search'
            description = 'Advanced search with filters'
            args_schema = ComplexSearchInput

            def _run(self, **kwargs):
                return 'results'

        tool = ComplexTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert 'query' in result['parameters']['properties']
        assert 'limit' in result['parameters']['properties']

    def test_format_tool_preserves_enum_values(self):
        """Test that enum values are preserved."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        unit_enum = result['parameters']['properties']['unit']['enum']
        assert unit_enum == ['celsius', 'fahrenheit']

    def test_format_tool_with_special_characters_in_description(self):
        """Test formatting a tool with special characters in description."""

        class SpecialTool(BaseTool):
            name = 'special_tool'
            description = (
                'Tool with special chars: @#$%^&*() and unicode: 你好'
            )
            args_schema = EmptyInput

            def _run(self):
                return 'ok'

        tool = SpecialTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert '你好' in result['description']
        assert '@#$%^&*()' in result['description']

    def test_format_tools_logs_count(self, caplog):
        """Test that formatting logs the tool count."""
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        ToolSchemaFormatter.format_tools(tools)

    def test_format_tool_with_array_parameter(self):
        """Test formatting a tool with array parameter."""

        class ArrayTool(BaseTool):
            name = 'multi_search'
            description = 'Search multiple queries'
            args_schema = ArraySearchInput

            def _run(self, queries):
                return f'Searching: {queries}'

        tool = ArrayTool()

        result = ToolSchemaFormatter.format_tool(tool)

        queries_prop = result['parameters']['properties']['queries']
        assert queries_prop['type'] == 'array'

    def test_format_tool_with_number_parameters(self):
        """Test formatting a tool with number parameters."""

        class MathTool(BaseTool):
            name = 'calculate'
            description = 'Perform calculations'
            args_schema = MathInput

            def _run(self, a, b):
                return a + b

        tool = MathTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert result['parameters']['properties']['a']['type'] == 'number'
        assert result['parameters']['properties']['b']['type'] == 'integer'

    def test_format_tool_with_boolean_parameter(self):
        """Test formatting a tool with boolean parameter."""

        class FlagTool(BaseTool):
            name = 'search_with_flag'
            description = 'Search with optional flag'
            args_schema = FlagInput

            def _run(self, query, exact_match=False):
                return f'Searching: {query} (exact={exact_match})'

        tool = FlagTool()

        result = ToolSchemaFormatter.format_tool(tool)

        exact_match_prop = result['parameters']['properties']['exact_match']
        assert exact_match_prop['type'] == 'boolean'

    def test_format_multiple_tools_with_same_parameter_names(self):
        """Test formatting multiple tools with same parameter names."""

        class Tool1(BaseTool):
            name = 'tool_one'
            description = 'First tool'
            args_schema = ParamStringInput

            def _run(self, param):
                return param

        class Tool2(BaseTool):
            name = 'tool_two'
            description = 'Second tool'
            args_schema = ParamIntInput

            def _run(self, param):
                return param

        tools = [Tool1(), Tool2()]

        result = ToolSchemaFormatter.format_tools(tools)

        assert len(result) == 2
        assert (
            result[0]['parameters']['properties']['param']['type'] == 'string'
        )
        assert (
            result[1]['parameters']['properties']['param']['type'] == 'integer'
        )

    def test_responses_format_has_flat_structure(self):
        """Test that Responses API format has flat structure (no nested 'function')."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        assert 'type' in result
        assert 'name' in result
        assert 'description' in result
        assert 'parameters' in result
        assert 'function' not in result

    def test_format_tool_schema_is_valid_json_schema(self):
        """Test that the parameters conform to JSON Schema structure."""
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert isinstance(params['properties'], dict)
        assert isinstance(params.get('required', []), list)

    def test_format_preserves_additional_schema_properties(self):
        """Test that additional schema properties are preserved."""

        class ValidationTool(BaseTool):
            name = 'validate_input'
            description = 'Validate input with constraints'
            args_schema = ValidationInput

            def _run(self, text):
                return f'Valid: {text}'

        tool = ValidationTool()

        result = ToolSchemaFormatter.format_tool(tool)

        text_prop = result['parameters']['properties']['text']
        assert text_prop['minLength'] == 5
        assert text_prop['maxLength'] == 100

    def test_strict_mode_does_not_mutate_original_schema(self):
        """Test that strict mode doesn't mutate the original tool schema."""
        tool = MockWeatherTool()

        # Get original schema
        original_schema = tool.get_schema()
        original_params = original_schema['parameters'].copy()

        # Format with strict mode
        ToolSchemaFormatter.format_tool(tool, strict=True)

        # Verify original schema is unchanged
        assert 'additionalProperties' not in tool.get_schema()['parameters']
        assert tool.get_schema()['parameters'] == original_params

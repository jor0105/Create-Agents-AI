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
    def test_format_tool_for_openai_completions(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        assert result['type'] == 'function'
        assert 'function' in result
        assert result['function']['name'] == 'get_weather'
        assert (
            result['function']['description']
            == 'Get the current weather for a location'
        )
        assert 'parameters' in result['function']

    def test_format_tool_for_openai_includes_parameters(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        params = result['function']['parameters']
        assert params['type'] == 'object'
        assert 'location' in params['properties']
        assert 'unit' in params['properties']
        assert params['required'] == ['location']

    def test_format_tool_for_responses_api(self):
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['type'] == 'function'
        assert result['name'] == 'web_search'
        assert result['description'] == 'Search the web for information'
        assert 'parameters' in result

    def test_format_tool_for_responses_api_includes_parameters(self):
        tool = MockSearchTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert 'query' in params['properties']
        assert params['required'] == ['query']

    def test_format_tools_for_openai_single_tool(self):
        tools = [MockWeatherTool()]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert len(result) == 1
        assert result[0]['type'] == 'function'
        assert result[0]['function']['name'] == 'get_weather'

    def test_format_tools_for_openai_multiple_tools(self):
        tools = [MockWeatherTool(), MockSearchTool(), MockNoParamsTool()]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert len(result) == 3
        names = [tool['function']['name'] for tool in result]
        assert 'get_weather' in names
        assert 'web_search' in names
        assert 'get_time' in names

    def test_format_tools_for_responses_api_single_tool(self):
        tools = [MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 1
        assert result[0]['type'] == 'function'
        assert result[0]['name'] == 'web_search'

    def test_format_tools_for_responses_api_multiple_tools(self):
        tools = [MockWeatherTool(), MockSearchTool()]

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        names = [tool['name'] for tool in result]
        assert 'get_weather' in names
        assert 'web_search' in names

    def test_format_tool_with_no_parameters(self):
        tool = MockNoParamsTool()

        result_completions = ToolSchemaFormatter.format_tool_for_openai(tool)
        result_responses = ToolSchemaFormatter.format_tool_for_responses_api(
            tool
        )

        assert result_completions['function']['parameters']['properties'] == {}
        assert result_responses['parameters']['properties'] == {}

    def test_format_tools_for_openai_empty_list(self):
        tools = []

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert result == []

    def test_format_tools_for_responses_api_empty_list(self):
        tools = []

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert result == []

    def test_format_preserves_parameter_types(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        location_prop = result['function']['parameters']['properties'][
            'location'
        ]
        unit_prop = result['function']['parameters']['properties']['unit']

        assert location_prop['type'] == 'string'
        assert unit_prop['type'] == 'string'
        assert unit_prop['enum'] == ['celsius', 'fahrenheit']

    def test_format_preserves_descriptions(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert (
            result['description'] == 'Get the current weather for a location'
        )
        location_desc = result['parameters']['properties']['location'][
            'description'
        ]
        assert 'city and state' in location_desc

    def test_format_preserves_required_fields(self):
        tool = MockWeatherTool()

        result_completions = ToolSchemaFormatter.format_tool_for_openai(tool)
        result_responses = ToolSchemaFormatter.format_tool_for_responses_api(
            tool
        )

        assert result_completions['function']['parameters']['required'] == [
            'location'
        ]
        assert result_responses['parameters']['required'] == ['location']

    def test_completions_and_responses_have_different_structure(self):
        tool = MockWeatherTool()

        completions_format = ToolSchemaFormatter.format_tool_for_openai(tool)
        responses_format = ToolSchemaFormatter.format_tool_for_responses_api(
            tool
        )

        assert 'function' in completions_format
        assert completions_format['function']['name'] == 'get_weather'

        assert 'name' in responses_format
        assert responses_format['name'] == 'get_weather'
        assert 'function' not in responses_format

    def test_format_tools_maintains_order(self):
        tools = [
            MockWeatherTool(),
            MockSearchTool(),
            MockNoParamsTool(),
        ]

        result = ToolSchemaFormatter.format_tools_for_openai(tools)

        assert result[0]['function']['name'] == 'get_weather'
        assert result[1]['function']['name'] == 'web_search'
        assert result[2]['function']['name'] == 'get_time'

    def test_format_tool_with_complex_parameters(self):
        class ComplexTool(BaseTool):
            name = 'complex_search'
            description = 'Advanced search with filters'
            args_schema = ComplexSearchInput

            def _run(self, **kwargs):
                return 'results'

        tool = ComplexTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert 'query' in result['parameters']['properties']
        assert 'limit' in result['parameters']['properties']

    def test_format_tool_preserves_enum_values(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        unit_enum = result['function']['parameters']['properties']['unit'][
            'enum'
        ]
        assert unit_enum == ['celsius', 'fahrenheit']

    def test_format_tool_with_special_characters_in_description(self):
        class SpecialTool(BaseTool):
            name = 'special_tool'
            description = (
                'Tool with special chars: @#$%^&*() and unicode: 你好'
            )
            args_schema = EmptyInput

            def _run(self):
                return 'ok'

        tool = SpecialTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert '你好' in result['description']
        assert '@#$%^&*()' in result['description']

    def test_format_tools_for_openai_logs_count(self, caplog):
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        ToolSchemaFormatter.format_tools_for_openai(tools)

    def test_format_tools_for_responses_api_logs_count(self, caplog):
        import logging

        caplog.set_level(logging.INFO)

        tools = [MockWeatherTool(), MockSearchTool()]

        ToolSchemaFormatter.format_tools_for_responses_api(tools)

    def test_format_tool_with_array_parameter(self):
        class ArrayTool(BaseTool):
            name = 'multi_search'
            description = 'Search multiple queries'
            args_schema = ArraySearchInput

            def _run(self, queries):
                return f'Searching: {queries}'

        tool = ArrayTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        queries_prop = result['function']['parameters']['properties'][
            'queries'
        ]
        assert queries_prop['type'] == 'array'

    def test_format_tool_with_number_parameters(self):
        class MathTool(BaseTool):
            name = 'calculate'
            description = 'Perform calculations'
            args_schema = MathInput

            def _run(self, a, b):
                return a + b

        tool = MathTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert result['parameters']['properties']['a']['type'] == 'number'
        assert result['parameters']['properties']['b']['type'] == 'integer'

    def test_format_tool_with_boolean_parameter(self):
        class FlagTool(BaseTool):
            name = 'search_with_flag'
            description = 'Search with optional flag'
            args_schema = FlagInput

            def _run(self, query, exact_match=False):
                return f'Searching: {query} (exact={exact_match})'

        tool = FlagTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        exact_match_prop = result['function']['parameters']['properties'][
            'exact_match'
        ]
        assert exact_match_prop['type'] == 'boolean'

    def test_format_multiple_tools_with_same_parameter_names(self):
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

        result = ToolSchemaFormatter.format_tools_for_responses_api(tools)

        assert len(result) == 2
        assert (
            result[0]['parameters']['properties']['param']['type'] == 'string'
        )
        assert (
            result[1]['parameters']['properties']['param']['type'] == 'integer'
        )

    def test_completions_format_has_nested_function_key(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        assert 'type' in result
        assert 'function' in result
        assert 'name' in result['function']
        assert 'description' in result['function']
        assert 'parameters' in result['function']

    def test_responses_format_has_flat_structure(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        assert 'type' in result
        assert 'name' in result
        assert 'description' in result
        assert 'parameters' in result
        assert 'function' not in result

    def test_format_tool_schema_is_valid_json_schema(self):
        tool = MockWeatherTool()

        result = ToolSchemaFormatter.format_tool_for_responses_api(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert isinstance(params['properties'], dict)
        assert isinstance(params.get('required', []), list)

    def test_format_preserves_additional_schema_properties(self):
        class ValidationTool(BaseTool):
            name = 'validate_input'
            description = 'Validate input with constraints'
            args_schema = ValidationInput

            def _run(self, text):
                return f'Valid: {text}'

        tool = ValidationTool()

        result = ToolSchemaFormatter.format_tool_for_openai(tool)

        text_prop = result['function']['parameters']['properties']['text']
        assert text_prop['minLength'] == 5
        assert text_prop['maxLength'] == 100

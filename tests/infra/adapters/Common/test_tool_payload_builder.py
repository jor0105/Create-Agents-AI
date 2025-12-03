"""Tests for ToolPayloadBuilder - unified tool schema formatter.

This module tests the ToolPayloadBuilder which handles formatting
tool schemas for both OpenAI and Ollama providers.
"""

from typing import List, Literal, Optional
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from createagents.domain import BaseTool
from createagents.infra.adapters.Common import ToolPayloadBuilder


# =============================================================================
# Test Input Schemas
# =============================================================================


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


# =============================================================================
# Test Tools
# =============================================================================


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


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock()


@pytest.fixture
def openai_builder(mock_logger):
    """Create a ToolPayloadBuilder configured for OpenAI."""
    return ToolPayloadBuilder(
        logger=mock_logger,
        format_style='openai',
        strict=False,
    )


@pytest.fixture
def openai_strict_builder(mock_logger):
    """Create a ToolPayloadBuilder configured for OpenAI with strict mode."""
    return ToolPayloadBuilder(
        logger=mock_logger,
        format_style='openai',
        strict=True,
    )


@pytest.fixture
def ollama_builder(mock_logger):
    """Create a ToolPayloadBuilder configured for Ollama."""
    return ToolPayloadBuilder(
        logger=mock_logger,
        format_style='ollama',
        strict=False,
    )


# =============================================================================
# OpenAI Format Tests
# =============================================================================


@pytest.mark.unit
class TestToolPayloadBuilderOpenAI:
    """Tests for ToolPayloadBuilder with OpenAI format."""

    def test_single_format_openai(self, openai_builder):
        """Test formatting a single tool for OpenAI."""
        tool = MockSearchTool()

        result = openai_builder.single_format(tool)

        assert result['type'] == 'function'
        assert result['name'] == 'web_search'
        assert result['description'] == 'Search the web for information'
        assert 'parameters' in result
        # OpenAI format should NOT have nested 'function' key
        assert 'function' not in result

    def test_single_format_includes_parameters(self, openai_builder):
        """Test that single_format includes all parameters."""
        tool = MockWeatherTool()

        result = openai_builder.single_format(tool)

        params = result['parameters']
        assert params['type'] == 'object'
        assert 'location' in params['properties']
        assert 'unit' in params['properties']
        assert params['required'] == ['location']

    def test_single_format_with_strict_mode(self, openai_strict_builder):
        """Test formatting a tool with strict mode enabled."""
        tool = MockSearchTool()

        result = openai_strict_builder.single_format(tool)

        assert result['strict'] is True
        assert result['parameters']['additionalProperties'] is False

    def test_single_format_without_strict_mode(self, openai_builder):
        """Test formatting a tool without strict mode (default)."""
        tool = MockSearchTool()

        result = openai_builder.single_format(tool)

        assert 'strict' not in result
        assert 'additionalProperties' not in result['parameters']

    def test_multiple_format_single_tool(self, openai_builder):
        """Test formatting a single tool in a list."""
        tools = [MockSearchTool()]

        result = openai_builder.multiple_format(tools)

        assert len(result) == 1
        assert result[0]['type'] == 'function'
        assert result[0]['name'] == 'web_search'

    def test_multiple_format_multiple_tools(self, openai_builder):
        """Test formatting multiple tools."""
        tools = [MockWeatherTool(), MockSearchTool(), MockNoParamsTool()]

        result = openai_builder.multiple_format(tools)

        assert len(result) == 3
        names = [tool['name'] for tool in result]
        assert 'get_weather' in names
        assert 'web_search' in names
        assert 'get_time' in names

    def test_multiple_format_empty_list(self, openai_builder):
        """Test formatting an empty list of tools."""
        result = openai_builder.multiple_format([])

        assert result == []

    def test_format_preserves_enum_values(self, openai_builder):
        """Test that enum values are preserved."""
        tool = MockWeatherTool()

        result = openai_builder.single_format(tool)

        unit_enum = result['parameters']['properties']['unit']['enum']
        assert unit_enum == ['celsius', 'fahrenheit']

    def test_format_with_array_parameter(self, openai_builder):
        """Test formatting a tool with array parameter."""

        class ArrayTool(BaseTool):
            name = 'multi_search'
            description = 'Search multiple queries'
            args_schema = ArraySearchInput

            def _run(self, queries):
                return f'Searching: {queries}'

        tool = ArrayTool()

        result = openai_builder.single_format(tool)

        queries_prop = result['parameters']['properties']['queries']
        assert queries_prop['type'] == 'array'

    def test_format_with_number_parameters(self, openai_builder):
        """Test formatting a tool with number parameters."""

        class MathTool(BaseTool):
            name = 'calculate'
            description = 'Perform calculations'
            args_schema = MathInput

            def _run(self, a, b):
                return a + b

        tool = MathTool()

        result = openai_builder.single_format(tool)

        assert result['parameters']['properties']['a']['type'] == 'number'
        assert result['parameters']['properties']['b']['type'] == 'integer'

    def test_format_with_boolean_parameter(self, openai_builder):
        """Test formatting a tool with boolean parameter."""

        class FlagTool(BaseTool):
            name = 'search_with_flag'
            description = 'Search with optional flag'
            args_schema = FlagInput

            def _run(self, query, exact_match=False):
                return f'Searching: {query} (exact={exact_match})'

        tool = FlagTool()

        result = openai_builder.single_format(tool)

        exact_match_prop = result['parameters']['properties']['exact_match']
        assert exact_match_prop['type'] == 'boolean'


# =============================================================================
# Ollama Format Tests
# =============================================================================


@pytest.mark.unit
class TestToolPayloadBuilderOllama:
    """Tests for ToolPayloadBuilder with Ollama format."""

    def test_single_format_ollama(self, ollama_builder):
        """Test formatting a single tool for Ollama."""
        tool = MockSearchTool()

        result = ollama_builder.single_format(tool)

        # Ollama format has nested 'function' key
        assert result['type'] == 'function'
        assert 'function' in result
        assert result['function']['name'] == 'web_search'
        assert (
            result['function']['description']
            == 'Search the web for information'
        )
        assert 'parameters' in result['function']

    def test_single_format_ollama_includes_parameters(self, ollama_builder):
        """Test that Ollama format includes all parameters."""
        tool = MockWeatherTool()

        result = ollama_builder.single_format(tool)

        params = result['function']['parameters']
        assert params['type'] == 'object'
        assert 'location' in params['properties']
        assert 'unit' in params['properties']
        assert params['required'] == ['location']

    def test_multiple_format_ollama(self, ollama_builder):
        """Test formatting multiple tools for Ollama."""
        tools = [MockWeatherTool(), MockSearchTool()]

        result = ollama_builder.multiple_format(tools)

        assert len(result) == 2
        assert result[0]['function']['name'] == 'get_weather'
        assert result[1]['function']['name'] == 'web_search'

    def test_ollama_format_no_strict_mode(self, mock_logger):
        """Test that strict mode doesn't affect Ollama format."""
        builder = ToolPayloadBuilder(
            logger=mock_logger,
            format_style='ollama',
            strict=True,  # Should be ignored for Ollama
        )
        tool = MockSearchTool()

        result = builder.single_format(tool)

        # Ollama doesn't use strict mode
        assert 'strict' not in result
        assert 'additionalProperties' not in result['function']['parameters']


# =============================================================================
# Tool Choice Tests
# =============================================================================


@pytest.mark.unit
class TestToolPayloadBuilderToolChoice:
    """Tests for tool_choice formatting."""

    def test_format_tool_choice_none_value(self, openai_builder):
        """Test that None tool_choice returns None."""
        result = openai_builder.format_tool_choice(None)

        assert result is None

    def test_format_tool_choice_auto(self, openai_builder):
        """Test formatting 'auto' tool_choice."""
        result = openai_builder.format_tool_choice('auto')

        assert result == 'auto'

    def test_format_tool_choice_none_string(self, openai_builder):
        """Test formatting 'none' tool_choice."""
        result = openai_builder.format_tool_choice('none')

        assert result == 'none'

    def test_format_tool_choice_required(self, openai_builder):
        """Test formatting 'required' tool_choice."""
        result = openai_builder.format_tool_choice('required')

        assert result == 'required'

    def test_format_tool_choice_specific_tool(self, openai_builder):
        """Test formatting specific tool choice."""
        tools = [MockWeatherTool(), MockSearchTool()]

        result = openai_builder.format_tool_choice('get_weather', tools)

        assert result == {
            'type': 'function',
            'function': {'name': 'get_weather'},
        }

    def test_format_tool_choice_dict_format(self, openai_builder):
        """Test formatting dict tool_choice."""
        tool_choice = {
            'type': 'function',
            'function': {'name': 'web_search'},
        }
        tools = [MockSearchTool()]

        result = openai_builder.format_tool_choice(tool_choice, tools)

        assert result == tool_choice

    def test_format_tool_choice_invalid_returns_auto(self, openai_builder):
        """Test that invalid tool_choice falls back to 'auto'."""
        # Non-existent tool name without tools list for validation
        result = openai_builder.format_tool_choice('nonexistent_tool', [])

        assert result == 'auto'


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


@pytest.mark.unit
class TestToolPayloadBuilderEdgeCases:
    """Tests for edge cases and error handling."""

    def test_format_tool_with_empty_parameters(self, openai_builder):
        """Test formatting a tool with empty parameters."""
        tool = MockNoParamsTool()

        result = openai_builder.single_format(tool)

        assert result['parameters']['properties'] == {}

    def test_format_preserves_descriptions(self, openai_builder):
        """Test that descriptions are preserved."""
        tool = MockWeatherTool()

        result = openai_builder.single_format(tool)

        assert (
            result['description'] == 'Get the current weather for a location'
        )
        location_desc = result['parameters']['properties']['location'][
            'description'
        ]
        assert 'city and state' in location_desc

    def test_strict_mode_does_not_mutate_original_schema(
        self, openai_strict_builder
    ):
        """Test that strict mode doesn't mutate the original tool schema."""
        tool = MockWeatherTool()

        # Get original schema
        original_schema = tool.get_schema()
        original_params = original_schema['parameters'].copy()

        # Format with strict mode
        openai_strict_builder.single_format(tool)

        # Verify original schema is unchanged
        assert 'additionalProperties' not in tool.get_schema()['parameters']
        assert tool.get_schema()['parameters'] == original_params

    def test_format_multiple_tools_maintains_order(self, openai_builder):
        """Test that tool order is maintained."""
        tools = [
            MockWeatherTool(),
            MockSearchTool(),
            MockNoParamsTool(),
        ]

        result = openai_builder.multiple_format(tools)

        assert result[0]['name'] == 'get_weather'
        assert result[1]['name'] == 'web_search'
        assert result[2]['name'] == 'get_time'

    def test_format_tool_with_special_characters(self, openai_builder):
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

        result = openai_builder.single_format(tool)

        assert '你好' in result['description']
        assert '@#$%^&*()' in result['description']

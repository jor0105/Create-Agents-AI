from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict, List, Optional, Union

import pytest
from pydantic import BaseModel, Field, ValidationError

from createagents.domain.value_objects import (
    InjectedState,
    InjectedToolArg,
    InjectedToolCallId,
    StructuredTool,
    tool,
)


class MyCustomInjected(InjectedToolArg):
    pass


class SearchInput(BaseModel):
    query: str = Field(description='The search query')
    max_results: int = Field(
        default=10, description='Maximum number of results'
    )


class CalculatorInput(BaseModel):
    expression: str = Field(description='Mathematical expression to calculate')


class ComplexInput(BaseModel):
    name: str = Field(description='User name')
    tags: List[str] = Field(default_factory=list, description='Tag list')
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description='Optional metadata'
    )
    priority: Union[int, str] = Field(default=1, description='Priority')


@pytest.mark.unit
class TestToolDecoratorWithoutParentheses:
    def test_tool_decorator_basic_function(self):
        @tool
        def greet(name: str) -> str:
            return f'Hello, {name}!'

        assert isinstance(greet, StructuredTool)
        assert greet.name == 'greet'

    def test_tool_decorator_infers_name_from_function(self):
        @tool
        def my_custom_tool(x: int) -> int:
            return x * 2

        assert my_custom_tool.name == 'my_custom_tool'

    def test_tool_decorator_infers_description_from_docstring(self):
        @tool
        def describe_weather(city: str) -> str:
            return f'Sunny in {city}'

        assert describe_weather.description

    def test_tool_decorator_generates_schema_from_signature(self):
        @tool
        def calculate(a: int, b: int) -> int:
            return a + b

        schema = calculate.get_schema()

        assert schema['name'] == 'calculate'
        assert 'parameters' in schema
        assert 'properties' in schema['parameters']
        assert 'a' in schema['parameters']['properties']
        assert 'b' in schema['parameters']['properties']

    def test_tool_decorator_includes_required_fields(self):
        @tool
        def required_test(
            required_param: str, optional_param: str = 'default'
        ) -> str:
            return f'{required_param} - {optional_param}'

        schema = required_test.get_schema()
        required = schema['parameters'].get('required', [])

        assert 'required_param' in required

    def test_tool_decorator_run_executes_function(self):
        @tool
        def multiply(x: int, y: int) -> int:
            return x * y

        result = multiply.run(x=3, y=4)
        assert result == 12

    def test_tool_decorator_with_default_values(self):
        @tool
        def with_defaults(
            name: str, count: int = 5, active: bool = True
        ) -> str:
            return f'{name}: {count}, {active}'

        result = with_defaults.run(name='test')
        assert result == 'test: 5, True'

        result = with_defaults.run(name='test', count=10, active=False)
        assert result == 'test: 10, False'


@pytest.mark.unit
class TestToolDecoratorWithCustomName:
    def test_scenario_custom_name_overrides_function_name(self):
        @tool('weather_tool')
        def get_weather_info(city: str) -> str:
            return f'Weather for {city}'

        assert get_weather_info.name == 'weather_tool'

    def test_scenario_custom_name_preserves_docstring(self):
        @tool('data_search')
        def fetch_data(query: str) -> str:
            return f'Data for {query}'

        assert fetch_data.name == 'data_search'

    def test_scenario_name_parameter_works(self):
        @tool(name='explicit_name')
        def implementation(x: int) -> int:
            return x * 2

        assert implementation.name == 'explicit_name'


@pytest.mark.unit
class TestToolDecoratorWithArgsSchema:
    def test_scenario_explicit_args_schema(self):
        @tool(args_schema=SearchInput)
        def search(query: str, max_results: int = 10) -> str:
            return f'Searching for {query}'

        assert search.args_schema is SearchInput

    def test_scenario_calculator_with_schema(self):
        @tool(args_schema=CalculatorInput)
        def calculator(expression: str) -> str:
            return f'Result: {expression}'

        assert calculator.args_schema is CalculatorInput

    def test_scenario_schema_matches_function_signature(self):
        @tool(args_schema=SearchInput)
        def advanced_search(query: str, max_results: int = 10) -> str:
            return query

        schema = advanced_search.get_schema()
        assert 'query' in schema['parameters']['properties']
        assert 'max_results' in schema['parameters']['properties']


@pytest.mark.unit
class TestToolDecoratorWithComplexTypes:
    def test_scenario_complex_input_types(self):
        @tool
        def process_complex(
            name: str,
            tags: List[str],
            metadata: Optional[Dict[str, Any]] = None,
        ) -> str:
            return name

        schema = process_complex.get_schema()
        assert 'name' in schema['parameters']['properties']
        assert 'tags' in schema['parameters']['properties']
        assert 'metadata' in schema['parameters']['properties']

    def test_scenario_union_types(self):
        @tool
        def handle_union(value: Union[int, str]) -> str:
            return str(value)

        schema = handle_union.get_schema()
        assert 'value' in schema['parameters']['properties']

    def test_scenario_optional_types(self):
        @tool
        def handle_optional(value: Optional[str] = None) -> str:
            return value or 'default'

        schema = handle_optional.get_schema()
        assert 'value' in schema['parameters']['properties']


@pytest.mark.unit
class TestToolDecoratorWithInjectedArgs:
    def test_scenario_injected_args_excluded_from_schema(self):
        @tool
        def with_injection(
            query: str,
            internal_id: Annotated[str, InjectedToolArg],
        ) -> str:
            return query

        schema = with_injection.get_schema()
        props = schema['parameters']['properties']

        assert 'query' in props
        assert 'internal_id' not in props

    def test_scenario_injected_tool_call_id(self):
        @tool
        def traceable(
            data: str,
            call_id: Annotated[str, InjectedToolCallId],
        ) -> str:
            return data

        schema = traceable.get_schema()
        props = schema['parameters']['properties']

        assert 'data' in props
        assert 'call_id' not in props

    def test_scenario_injected_state(self):
        @tool
        def stateful(
            action: str,
            state: Annotated[Dict[str, Any], InjectedState],
        ) -> str:
            return action

        schema = stateful.get_schema()
        props = schema['parameters']['properties']

        assert 'action' in props
        assert 'state' not in props

    def test_scenario_multiple_injections(self):
        @tool
        def multi_inject(
            query: str,
            call_id: Annotated[str, InjectedToolCallId],
            state: Annotated[Dict[str, Any], InjectedState],
            custom: Annotated[int, MyCustomInjected],
        ) -> str:
            return query

        schema = multi_inject.get_schema()
        props = schema['parameters']['properties']

        assert 'query' in props
        assert 'call_id' not in props
        assert 'state' not in props
        assert 'custom' not in props


@pytest.mark.unit
class TestToolDecoratorTypeValidation:
    def test_scenario_validates_int_type(self):
        @tool
        def int_tool(value: int) -> int:
            return value * 2

        result = int_tool.run(value=21)
        assert result == 42

    def test_scenario_validates_string_type(self):
        @tool
        def string_tool(text: str) -> str:
            return text.upper()

        result = string_tool.run(text='hello')
        assert result == 'HELLO'

    def test_scenario_rejects_invalid_type(self):
        @tool
        def strict_tool(value: int) -> int:
            return value

        with pytest.raises((ValidationError, ValueError, TypeError)):
            strict_tool.run(value='not_an_int')


@pytest.mark.unit
class TestToolDecoratorSchemaGeneration:
    def test_scenario_required_fields_marked(self):
        @tool
        def with_required(a: str, b: str) -> str:
            return f'{a}{b}'

        schema = with_required.get_schema()
        required = schema['parameters'].get('required', [])

        assert 'a' in required
        assert 'b' in required

    def test_scenario_optional_fields_have_defaults(self):
        @tool
        def with_optional(
            required: str, optional: int = 10, flag: bool = True
        ) -> str:
            return required

        schema = with_optional.get_schema()
        required_fields = schema['parameters'].get('required', [])

        assert 'required' in required_fields
        assert (
            'optional' not in required_fields
            or 'default' in schema['parameters']['properties']['optional']
        )

    def test_scenario_all_optional_parameters(self):
        @tool
        def all_optional(x: int = 1, y: int = 2) -> int:
            return x + y

        schema = all_optional.get_schema()
        required = schema['parameters'].get('required', [])

        assert len(required) == 0


@pytest.mark.unit
class TestToolDecoratorComplexReturnTypes:
    def test_scenario_returns_list(self):
        @tool
        def list_tool(count: int) -> List[int]:
            return list(range(count))

        result = list_tool.run(count=3)
        assert result == [0, 1, 2]

    def test_scenario_returns_dict(self):
        @tool
        def dict_tool(key: str, value: str) -> Dict[str, str]:
            return {key: value}

        result = dict_tool.run(key='name', value='test')
        assert result == {'name': 'test'}

    def test_scenario_returns_none(self):
        @tool
        def none_tool(value: str) -> None:
            pass

        result = none_tool.run(value='test')
        assert result is None


@pytest.mark.unit
class TestToolDecoratorAsync:
    def test_scenario_async_tool_creation(self):
        @tool
        async def async_fetch(url: str) -> str:
            await asyncio.sleep(0.01)
            return f'Data from {url}'

        assert isinstance(async_fetch, StructuredTool)
        assert async_fetch.coroutine is not None

    def test_scenario_async_tool_execution(self):
        @tool
        async def async_process(data: str) -> str:
            await asyncio.sleep(0.01)
            return data.upper()

        async def run_test():
            result = await async_process.arun(data='hello')
            return result

        result = asyncio.run(run_test())
        assert result == 'HELLO'

    def test_scenario_async_with_complex_params(self):
        @tool
        async def async_search(query: str, limit: int = 10) -> str:
            await asyncio.sleep(0.01)
            return f'{query}: {limit}'

        async def run_test():
            result = await async_search.arun(query='test', limit=5)
            return result

        result = asyncio.run(run_test())
        assert 'test' in result
        assert '5' in result


@pytest.mark.unit
class TestToolDecoratorSchemaJsonSerializable:
    def test_scenario_schema_is_json_serializable(self):
        import json

        @tool
        def complex_tool(
            name: str, items: List[str], data: Optional[Dict[str, int]] = None
        ) -> str:
            return name

        schema = complex_tool.get_schema()
        json_str = json.dumps(schema)
        assert isinstance(json_str, str)

    def test_scenario_schema_roundtrip(self):
        import json

        @tool
        def serializable(value: str) -> str:
            return value

        schema = serializable.get_schema()
        json_str = json.dumps(schema)
        parsed = json.loads(json_str)

        assert parsed['name'] == 'serializable'
        assert 'parameters' in parsed


@pytest.mark.unit
class TestToolDecoratorEdgeCases:
    def test_scenario_empty_docstring(self):
        @tool
        def no_doc(x: int) -> int:
            return x

        assert no_doc.description is not None

    def test_scenario_multiline_description(self):
        @tool
        def multi_desc(x: int) -> int:
            return x

        assert multi_desc.description

    def test_scenario_special_characters_in_name(self):
        @tool('special_tool_123')
        def impl(x: int) -> int:
            return x

        assert impl.name == 'special_tool_123'

    def test_scenario_decorator_with_empty_parentheses(self):
        @tool()
        def with_parens(x: int) -> int:
            return x * 2

        assert isinstance(with_parens, StructuredTool)
        assert with_parens.name == 'with_parens'

    def test_scenario_decorator_without_parentheses(self):
        @tool
        def without_parens(x: int) -> int:
            return x * 2

        assert isinstance(without_parens, StructuredTool)
        assert without_parens.name == 'without_parens'


@pytest.mark.unit
class TestToolDecoratorProtocolCompliance:
    def test_scenario_implements_tool_protocol(self):
        @tool
        def protocol_tool(x: int) -> int:
            return x

        assert hasattr(protocol_tool, 'name')
        assert hasattr(protocol_tool, 'description')
        assert callable(getattr(protocol_tool, 'run', None))

    def test_scenario_has_callable_execute(self):
        @tool
        def executable(x: int) -> int:
            return x

        assert callable(getattr(executable, 'run', None))

    def test_scenario_has_schema_method(self):
        @tool
        def schema_tool(x: str) -> str:
            return x

        assert callable(schema_tool.get_schema)

        schema = schema_tool.get_schema()
        assert isinstance(schema, dict)
        assert 'name' in schema
        assert 'description' in schema
        assert 'parameters' in schema

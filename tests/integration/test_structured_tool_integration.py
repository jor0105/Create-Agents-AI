from __future__ import annotations

import asyncio
from typing import Annotated, Any, Dict, List, Optional

import pytest
from pydantic import BaseModel, Field, ValidationError

from createagents.domain.value_objects import (
    InjectedState,
    InjectedToolCallId,
    StructuredTool,
    ToolProtocol,
    tool,
)
from createagents.infra.config.available_tools import AvailableTools


class WeatherInput(BaseModel):
    city: str = Field(description='City name')
    units: str = Field(default='celsius', description='Temperature unit')


class DatabaseQueryInput(BaseModel):
    query: str = Field(description='SQL query')
    limit: int = Field(default=100, description='Result limit')
    timeout: float = Field(default=30.0, description='Timeout in seconds')


@pytest.mark.integration
class TestStructuredToolFromFunction:
    def test_creates_tool_from_sync_function(self):
        def add(a: int, b: int) -> int:
            return a + b

        tool = StructuredTool.from_function(add)

        assert isinstance(tool, StructuredTool)
        assert tool.name == 'add'
        assert tool.func is add
        assert tool.coroutine is None

    def test_creates_tool_from_async_function(self):
        async def fetch_data(url: str) -> str:
            await asyncio.sleep(0.01)
            return f'Data from {url}'

        tool = StructuredTool.from_function(coroutine=fetch_data)

        assert isinstance(tool, StructuredTool)
        assert tool.name == 'fetch_data'
        assert tool.func is None
        assert tool.coroutine is fetch_data

    def test_custom_name_overrides_function_name(self):
        def implementation(x: int) -> int:
            return x

        tool = StructuredTool.from_function(implementation, name='custom_name')

        assert tool.name == 'custom_name'

    def test_custom_description_overrides_docstring(self):
        def func(x: int) -> int:
            return x

        tool = StructuredTool.from_function(
            func, description='Descricao customizada'
        )

        assert tool.description == 'Descricao customizada'

    def test_args_schema_is_inferred(self):
        def typed_func(name: str, count: int = 10) -> str:
            return f'{name}: {count}'

        tool = StructuredTool.from_function(typed_func)

        assert tool.args_schema is not None

    def test_explicit_args_schema_is_used(self):
        def weather(city: str, units: str = 'celsius') -> str:
            return f'{city}: {units}'

        tool = StructuredTool.from_function(weather, args_schema=WeatherInput)

        assert tool.args_schema is WeatherInput

    def test_requires_func_or_coroutine(self):
        with pytest.raises(ValueError, match='Either func or coroutine'):
            StructuredTool.from_function()


@pytest.mark.integration
class TestStructuredToolExecution:
    def test_run_executes_sync_function(self):
        def multiply(x: int, y: int) -> int:
            return x * y

        tool = StructuredTool.from_function(multiply)

        result = tool.run(x=3, y=4)

        assert result == 12

    def test_run_validates_input(self):
        def strict(value: int) -> int:
            return value

        tool = StructuredTool.from_function(strict)

        assert tool.run(value=42) == 42

        with pytest.raises((ValidationError, ValueError, TypeError)):
            tool.run(value='not a number')

    def test_arun_executes_async_function(self):
        async def async_process(data: str) -> str:
            await asyncio.sleep(0.01)
            return data.upper()

        tool = StructuredTool.from_function(coroutine=async_process)

        async def run_test():
            return await tool.arun(data='hello')

        result = asyncio.run(run_test())
        assert result == 'HELLO'

    def test_arun_validates_input(self):
        async def typed_async(count: int) -> int:
            await asyncio.sleep(0.01)
            return count * 2

        tool = StructuredTool.from_function(coroutine=typed_async)

        async def run_test():
            result = await tool.arun(count=5)
            assert result == 10

            with pytest.raises((ValidationError, ValueError, TypeError)):
                await tool.arun(count='not a number')

        asyncio.run(run_test())

    def test_arun_wraps_sync_function(self):
        def sync_func(x: int) -> int:
            return x * 2

        tool = StructuredTool.from_function(sync_func)

        async def run_test():
            return await tool.arun(x=21)

        result = asyncio.run(run_test())
        assert result == 42

    def test_run_with_defaults(self):
        def with_defaults(
            required: str, optional: int = 10, flag: bool = True
        ) -> str:
            return f'{required}: {optional}, {flag}'

        tool = StructuredTool.from_function(with_defaults)

        result = tool.run(required='test')
        assert result == 'test: 10, True'

        result = tool.run(required='test', optional=20, flag=False)
        assert result == 'test: 20, False'


@pytest.mark.integration
class TestStructuredToolGetSchema:
    def test_schema_has_required_keys(self):
        def simple(x: int) -> int:
            return x

        tool = StructuredTool.from_function(simple)
        schema = tool.get_schema()

        assert 'name' in schema
        assert 'description' in schema
        assert 'parameters' in schema

    def test_schema_parameters_structure(self):
        def func(name: str, age: int) -> str:
            return name

        tool = StructuredTool.from_function(func)
        schema = tool.get_schema()

        params = schema['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'name' in params['properties']
        assert 'age' in params['properties']

    def test_schema_includes_required_fields(self):
        def mixed(required: str, optional: int = 10) -> str:
            return required

        tool = StructuredTool.from_function(mixed)
        schema = tool.get_schema()

        required = schema['parameters'].get('required', [])
        assert 'required' in required

    def test_schema_is_json_serializable(self):
        import json

        def withplex_func(
            name: str, items: List[str], data: Optional[Dict[str, int]] = None
        ) -> str:
            return name

        tool = StructuredTool.from_function(withplex_func)
        schema = tool.get_schema()

        json_str = json.dumps(schema)
        assert isinstance(json_str, str)


@pytest.mark.integration
class TestToolDecoratorCreatesStructuredTool:
    def test_decorator_creates_structured_tool(self):
        @tool
        def decorated(x: int) -> int:
            return x

        assert isinstance(decorated, StructuredTool)

    def test_decorator_tool_is_executable(self):
        @tool
        def calculate(a: int, b: int) -> int:
            return a + b

        result = calculate.run(a=5, b=3)
        assert result == 8

    def test_decorator_tool_has_schema(self):
        @tool
        def search(query: str, limit: int = 10) -> str:
            return query

        schema = search.get_schema()

        assert schema['name'] == 'search'
        assert 'query' in schema['parameters']['properties']
        assert 'limit' in schema['parameters']['properties']

    def test_decorator_async_tool_works(self):
        @tool
        async def async_tool(data: str) -> str:
            await asyncio.sleep(0.01)
            return data.upper()

        async def run_test():
            return await async_tool.arun(data='hello')

        result = asyncio.run(run_test())
        assert result == 'HELLO'


@pytest.mark.integration
class TestToolProtocolCompatibility:
    def test_structured_tool_implements_protocol(self):
        def func(x: int) -> int:
            return x

        tool = StructuredTool.from_function(func)

        assert isinstance(tool, ToolProtocol)

    def test_decorated_tool_implements_protocol(self):
        @tool
        def decorated(x: int) -> int:
            return x

        assert isinstance(decorated, ToolProtocol)

    def test_protocol_attributes_present(self):
        @tool
        def protocol_test(value: str) -> str:
            return value

        assert hasattr(protocol_test, 'name')
        assert hasattr(protocol_test, 'description')
        assert callable(getattr(protocol_test, 'run', None))
        assert callable(getattr(protocol_test, 'get_schema', None))


@pytest.mark.integration
class TestAvailableToolsIntegration:
    def setup_method(self):
        AvailableTools.clear_agent_tools()

    def teardown_method(self):
        AvailableTools.clear_agent_tools()

    def test_can_add_structured_tool_to_registry(self):
        @tool
        def custom_tool(x: int) -> int:
            return x * 2

        AvailableTools.add_agent_tool('custom', custom_tool)

        agent_tools = AvailableTools.get_agent_tools()
        assert 'custom' in agent_tools

    def test_added_tool_can_be_retrieved(self):
        @tool
        def retrievable(data: str) -> str:
            return data

        AvailableTools.add_agent_tool('retrievable', retrievable)

        instance = AvailableTools.get_tool_instance('retrievable')

        assert instance is not None
        assert instance is retrievable

    def test_added_tool_appears_in_all_available(self):
        @tool
        def visible(x: int) -> int:
            return x

        AvailableTools.add_agent_tool('visible', visible)

        all_tools = AvailableTools.get_all_available_tools()

        assert 'visible' in all_tools

    def test_cannot_add_duplicate_tool(self):
        @tool
        def first(x: int) -> int:
            return x

        @tool
        def second(x: int) -> int:
            return x * 2

        AvailableTools.add_agent_tool('duplicate', first)

        with pytest.raises(ValueError, match='already registered'):
            AvailableTools.add_agent_tool('duplicate', second)

    def test_clear_agent_tools_removes_all(self):
        @tool
        def temp1(x: int) -> int:
            return x

        @tool
        def temp2(x: int) -> int:
            return x

        AvailableTools.add_agent_tool('temp1', temp1)
        AvailableTools.add_agent_tool('temp2', temp2)

        assert len(AvailableTools.get_agent_tools()) >= 2

        AvailableTools.clear_agent_tools()

        assert len(AvailableTools.get_agent_tools()) == 0


@pytest.mark.integration
class TestSchemaProviderCompatibility:
    def test_schema_has_openai_withpatible_structure(self):
        @tool
        def openai_withpatible(
            query: str,
            limit: int = 10,
            filters: Optional[Dict[str, str]] = None,
        ) -> str:
            return query

        schema = openai_withpatible.get_schema()

        assert 'name' in schema
        assert 'description' in schema
        assert 'parameters' in schema

        params = schema['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params

    def test_schema_property_types_are_valid(self):
        @tool
        def typed_tool(
            string_val: str,
            int_val: int,
            float_val: float,
            bool_val: bool,
            list_val: List[str],
        ) -> str:
            return string_val

        schema = typed_tool.get_schema()
        props = schema['parameters']['properties']

        valid_types = {
            'string',
            'integer',
            'number',
            'boolean',
            'array',
            'object',
        }

        for prop_name, prop_schema in props.items():
            if 'type' in prop_schema:
                assert prop_schema['type'] in valid_types, (
                    f'{prop_name} has invalid type'
                )

    def test_injected_args_not_in_provider_schema(self):
        @tool
        def with_injection(
            query: str,
            call_id: Annotated[str, InjectedToolCallId],
            state: Annotated[Dict[str, Any], InjectedState],
        ) -> str:
            return query

        schema = with_injection.get_schema()
        props = schema['parameters']['properties']

        assert 'query' in props
        assert 'call_id' not in props
        assert 'state' not in props


@pytest.mark.integration
class TestRealWorldScenarios:
    def test_weather_tool_scenario(self):
        @tool(args_schema=WeatherInput)
        def get_weather(city: str, units: str = 'celsius') -> str:
            temp = 25 if units == 'celsius' else 77
            return f'Temperature in {city}: {temp}°{"C" if units == "celsius" else "F"}'

        result = get_weather.run(city='Sao Paulo')
        assert 'Sao Paulo' in result
        assert '25' in result

        result = get_weather.run(city='New York', units='fahrenheit')
        assert 'New York' in result
        assert '77' in result

    def test_database_query_scenario(self):
        @tool(args_schema=DatabaseQueryInput)
        def query_database(
            query: str, limit: int = 100, timeout: float = 30.0
        ) -> str:
            return f'Executed: {query} (limit={limit}, timeout={timeout})'

        result = query_database.run(query='SELECT * FROM users')
        assert 'SELECT * FROM users' in result
        assert 'limit=100' in result

        result = query_database.run(
            query='SELECT * FROM orders', limit=50, timeout=10.0
        )
        assert 'limit=50' in result
        assert 'timeout=10.0' in result

    def test_calculator_with_validation_scenario(self):
        class CalculatorInput(BaseModel):
            expression: str = Field(
                description='Expressao matematica (apenas +, -, *, /)'
            )

            def validate_expression(self):
                allowed = set('0123456789+-*/. ()')
                if not all(c in allowed for c in self.expression):
                    raise ValueError('Expression contains invalid characters')

        @tool(args_schema=CalculatorInput)
        def calculate(expression: str) -> str:
            try:
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f'Erro: {e}'

        assert calculate.run(expression='2 + 2') == '4'
        assert calculate.run(expression='10 * 5') == '50'
        assert calculate.run(expression='(3 + 2) * 4') == '20'

    def test_async_api_call_scenario(self):
        @tool
        async def fetch_user(user_id: int) -> Dict[str, Any]:
            await asyncio.sleep(0.01)
            return {
                'id': user_id,
                'name': f'User {user_id}',
                'email': f'user{user_id}@example.with',
            }

        async def run_test():
            result = await fetch_user.arun(user_id=123)
            return result

        result = asyncio.run(run_test())

        assert result['id'] == 123
        assert 'User 123' in result['name']

    def test_tool_with_state_injection_scenario(self):
        @tool
        def stateful_action(
            action: str,
            state: Annotated[Dict[str, Any], InjectedState],
        ) -> str:
            user = state.get('user', 'anonymous')
            return f'User {user} executed: {action}'

        schema = stateful_action.get_schema()
        assert 'state' not in schema['parameters']['properties']
        assert 'action' in schema['parameters']['properties']

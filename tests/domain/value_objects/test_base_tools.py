from typing import Any, Dict, Optional

import pytest
from pydantic import BaseModel, Field

from createagents.domain import BaseTool


# Pydantic models for test tools
class ConcreteTestInput(BaseModel):
    """Input schema for ConcreteTestTool."""

    input: str = Field(description='Test input')


class MinimalTestInput(BaseModel):
    """Input schema for MinimalTestTool - no required fields."""

    pass


class ComplexParametersInput(BaseModel):
    """Input schema for ComplexParametersTool."""

    query: str = Field(description='Search query')
    limit: int = Field(default=10, description='Result limit')
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description='Optional filters'
    )


class ConcreteTestTool(BaseTool):
    name = 'test_tool'
    description = 'A tool for testing purposes'
    args_schema = ConcreteTestInput

    def _run(self, input: str) -> str:
        return f'Executed with: {input}'


class MinimalTestTool(BaseTool):
    name = 'minimal_tool'
    description = 'Minimal tool implementation'
    args_schema = MinimalTestInput

    def _run(self) -> str:
        return 'Minimal execution'


class ComplexParametersTool(BaseTool):
    name = 'complex_tool'
    description = 'Tool with complex parameters'
    args_schema = ComplexParametersInput

    def _run(
        self, query: str, limit: int = 10, filters: Optional[dict] = None
    ) -> str:
        return f'Query: {query}, Limit: {limit}, Filters: {filters}'


@pytest.mark.unit
class TestBaseTool:
    def test_base_tool_can_be_instantiated_but_not_useful(self):
        tool = BaseTool()

        assert tool.name == 'base_tool'
        assert (
            tool.description == 'Base tool description (should be overridden)'
        )

    def test_concrete_implementation_can_be_instantiated(self):
        tool = ConcreteTestTool()

        assert isinstance(tool, BaseTool)
        assert tool.name == 'test_tool'
        assert tool.description == 'A tool for testing purposes'

    def test_tool_without_run_override_has_default_behavior(self):
        class IncompleteToolNoRun(BaseTool):
            name = 'incomplete'
            description = 'No _run method override'
            args_schema = MinimalTestInput

        tool = IncompleteToolNoRun()
        result = tool._run()
        assert result is None

    def test_name_attribute_is_accessible(self):
        tool = ConcreteTestTool()

        assert hasattr(tool, 'name')
        assert isinstance(tool.name, str)
        assert tool.name == 'test_tool'

    def test_description_attribute_is_accessible(self):
        tool = ConcreteTestTool()

        assert hasattr(tool, 'description')
        assert isinstance(tool.description, str)
        assert tool.description == 'A tool for testing purposes'

    def test_args_schema_attribute_is_accessible(self):
        tool = ConcreteTestTool()

        assert hasattr(tool, 'args_schema')
        assert tool.args_schema is ConcreteTestInput

    def test_run_method_can_be_called(self):
        tool = ConcreteTestTool()

        result = tool.run(input='test')

        assert result == 'Executed with: test'
        assert isinstance(result, str)

    def test_run_with_no_arguments(self):
        tool = MinimalTestTool()

        result = tool.run()

        assert result == 'Minimal execution'

    def test_run_with_multiple_arguments(self):
        tool = ComplexParametersTool()

        result = tool.run(
            query='search term', limit=5, filters={'category': 'tech'}
        )

        assert 'search term' in result
        assert '5' in result
        assert 'tech' in result


@pytest.mark.unit
class TestGetSchema:
    def test_get_schema_returns_dict(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert isinstance(schema, dict)

    def test_get_schema_contains_name(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'name' in schema
        assert schema['name'] == tool.name

    def test_get_schema_contains_description(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'description' in schema
        assert schema['description'] == tool.description

    def test_get_schema_contains_parameters(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert 'parameters' in schema
        assert 'properties' in schema['parameters']
        assert 'input' in schema['parameters']['properties']

    def test_get_schema_has_all_required_fields(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()

        assert set(schema.keys()) == {'name', 'description', 'parameters'}

    def test_get_schema_with_minimal_tool(self):
        tool = MinimalTestTool()

        schema = tool.get_schema()

        assert schema['name'] == 'minimal_tool'
        assert schema['description'] == 'Minimal tool implementation'
        assert schema['parameters']['type'] == 'object'

    def test_get_schema_with_complex_parameters(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()

        assert 'query' in schema['parameters']['properties']
        assert 'limit' in schema['parameters']['properties']
        assert 'filters' in schema['parameters']['properties']
        assert 'required' in schema['parameters']
        assert 'query' in schema['parameters']['required']

    def test_get_schema_returns_new_dict_each_time(self):
        tool = ConcreteTestTool()

        schema1 = tool.get_schema()
        schema2 = tool.get_schema()

        assert schema1 == schema2
        assert schema1 is not schema2

    def test_get_schema_can_be_modified_without_affecting_tool(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()
        schema['name'] = 'modified_name'

        assert tool.name == 'test_tool'
        new_schema = tool.get_schema()
        assert new_schema['name'] == 'test_tool'

    def test_get_schema_without_args_schema_raises_error(self):
        class NoSchemaTool(BaseTool):
            name = 'no_schema'
            description = 'Tool without args_schema'

            def _run(self) -> str:
                return 'no schema'

        tool = NoSchemaTool()

        with pytest.raises(NotImplementedError):
            tool.get_schema()


@pytest.mark.unit
class TestToolInheritance:
    def test_multiple_tools_have_independent_schemas(self):
        tool1 = ConcreteTestTool()
        tool2 = MinimalTestTool()

        schema1 = tool1.get_schema()
        schema2 = tool2.get_schema()

        assert schema1['name'] != schema2['name']
        assert schema1['description'] != schema2['description']

    def test_tool_can_be_subclassed_further(self):
        class ExtendedTool(ConcreteTestTool):
            name = 'extended_tool'
            description = 'Extended version'

            def _run(self, input: str) -> str:
                base_result = ConcreteTestTool._run(self, input=input)
                return f'Extended: {base_result}'

        tool = ExtendedTool()

        assert tool.name == 'extended_tool'
        result = tool.run(input='test')
        assert 'Extended' in result
        assert 'Executed with: test' in result

    def test_tools_are_isinstance_of_basetool(self):
        tools = [
            ConcreteTestTool(),
            MinimalTestTool(),
            ComplexParametersTool(),
        ]

        for tool in tools:
            assert isinstance(tool, BaseTool)

    def test_tool_attributes_are_class_attributes(self):
        assert hasattr(ConcreteTestTool, 'name')
        assert hasattr(ConcreteTestTool, 'description')
        assert hasattr(ConcreteTestTool, 'args_schema')


@pytest.mark.unit
class TestToolParameterSchemas:
    def test_parameters_follow_json_schema_structure(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()
        params = schema['parameters']
        assert params['type'] == 'object'
        assert isinstance(params['properties'], dict)

    def test_parameters_with_required_fields(self):
        tool = ConcreteTestTool()

        schema = tool.get_schema()
        params = schema['parameters']
        assert 'required' in params
        assert isinstance(params['required'], list)
        assert 'input' in params['required']

    def test_parameters_with_optional_fields(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        params = schema['parameters']
        required = params.get('required', [])
        all_props = params['properties'].keys()

        optional = set(all_props) - set(required)
        assert 'limit' in optional or 'filters' in optional

    def test_parameters_with_default_values(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        limit_param = schema['parameters']['properties']['limit']
        assert 'default' in limit_param
        assert limit_param['default'] == 10


@pytest.mark.unit
class TestToolExecution:
    def test_run_returns_value(self):
        tool = ConcreteTestTool()

        result = tool.run(input='test')

        assert result is not None

    def test_run_with_different_inputs(self):
        tool = ConcreteTestTool()

        inputs = ['simple', 'with spaces', 'special!@#$%', '123', '']
        for inp in inputs:
            result = tool.run(input=inp)
            assert inp in result

    def test_run_can_raise_exceptions(self):
        class StrictInput(BaseModel):
            value: str = Field(description='Value')

        class StrictTool(BaseTool):
            name = 'strict'
            description = 'Raises on empty input'
            args_schema = StrictInput

            def _run(self, value: str) -> str:
                if not value:
                    raise ValueError('Value cannot be empty')
                return value

        tool = StrictTool()

        with pytest.raises(ValueError, match='cannot be empty'):
            tool.run(value='')

    def test_run_with_kwargs(self):
        tool = ComplexParametersTool()

        result = tool.run(query='test', limit=20)

        assert 'test' in result
        assert '20' in result

    def test_run_with_default_arguments(self):
        tool = ComplexParametersTool()

        result = tool.run(query='test')

        assert 'test' in result
        assert '10' in result


@pytest.mark.unit
class TestPydanticValidation:
    def test_run_validates_input_with_pydantic(self):
        tool = ConcreteTestTool()

        result = tool.run(input='valid')
        assert 'valid' in result

    def test_run_rejects_missing_required_field(self):
        tool = ConcreteTestTool()

        with pytest.raises(Exception):
            tool.run()

    def test_run_validates_with_complex_schema(self):
        tool = ComplexParametersTool()

        result = tool.run(query='test', limit=5)
        assert 'test' in result

    def test_run_uses_default_values(self):
        tool = ComplexParametersTool()

        result = tool.run(query='test')
        assert 'Limit: 10' in result


@pytest.mark.unit
class TestToolDocumentation:
    def test_description_is_informative(self):
        tool = ConcreteTestTool()

        assert len(tool.description) > 10
        assert (
            tool.description != 'Base tool description (should be overridden)'
        )

    def test_complex_tool_has_detailed_schema(self):
        tool = ComplexParametersTool()

        schema = tool.get_schema()
        assert len(schema['parameters']['properties']) >= 3
        assert 'required' in schema['parameters']


@pytest.mark.unit
class TestToolEdgeCases:
    def test_tool_with_empty_parameters(self):
        class EmptyInput(BaseModel):
            pass

        class NoParamsTool(BaseTool):
            name = 'no_params'
            description = 'Tool with no parameters'
            args_schema = EmptyInput

            def _run(self) -> str:
                return 'no params'

        tool = NoParamsTool()
        schema = tool.get_schema()

        assert schema['parameters']['properties'] == {}

    def test_tool_name_with_special_characters(self):
        class SpecialInput(BaseModel):
            pass

        class SpecialNameTool(BaseTool):
            name = 'special_tool_123'
            description = 'Tool with special name'
            args_schema = SpecialInput

            def _run(self) -> str:
                return 'special'

        tool = SpecialNameTool()

        assert tool.name == 'special_tool_123'
        assert '_' in tool.name
        assert '123' in tool.name

    def test_tool_with_long_description(self):
        long_desc = 'A' * 1000

        class LongInput(BaseModel):
            pass

        class LongDescTool(BaseTool):
            name = 'long_desc'
            description = long_desc
            args_schema = LongInput

            def _run(self) -> str:
                return 'long'

        tool = LongDescTool()

        assert len(tool.description) == 1000
        assert tool.description == long_desc

    def test_tool_run_returns_different_types(self):
        class EmptyInput(BaseModel):
            pass

        class StringTool(BaseTool):
            name = 'string_tool'
            description = 'Returns string'
            args_schema = EmptyInput

            def _run(self) -> str:
                return 'string result'

        class DictTool(BaseTool):
            name = 'dict_tool'
            description = 'Returns dict'
            args_schema = EmptyInput

            def _run(self) -> dict:
                return {'key': 'value'}

        string_tool = StringTool()
        dict_tool = DictTool()

        assert isinstance(string_tool.run(), str)
        assert isinstance(dict_tool.run(), dict)

    def test_multiple_tool_instances_are_independent(self):
        tool1 = ConcreteTestTool()
        tool2 = ConcreteTestTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.get_schema() == tool2.get_schema()

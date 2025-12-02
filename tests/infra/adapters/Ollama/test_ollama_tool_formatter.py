import pytest
from pydantic import BaseModel, Field

from createagents.domain import BaseTool
from createagents.infra import OllamaToolSchemaFormatter


class MockToolInput(BaseModel):
    param1: str = Field(description='First parameter')


class MockTool(BaseTool):
    name = 'mock_tool'
    description = 'A mock tool for testing'
    args_schema = MockToolInput

    def _run(self, param1: str) -> str:
        return f'Executed with {param1}'


class EmptyInput(BaseModel):
    pass


@pytest.mark.unit
class TestOllamaToolFormatter:
    def test_format_single_tool(self):
        tool = MockTool()
        formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

        assert len(formatted) == 1
        assert formatted[0]['type'] == 'function'
        assert formatted[0]['function']['name'] == 'mock_tool'
        assert (
            formatted[0]['function']['description']
            == 'A mock tool for testing'
        )
        assert 'parameters' in formatted[0]['function']

    def test_format_multiple_tools(self):
        class Tool1(BaseTool):
            name = 'tool1'
            description = 'First tool'
            args_schema = EmptyInput

            def _run(self):
                pass

        class Tool2(BaseTool):
            name = 'tool2'
            description = 'Second tool'
            args_schema = EmptyInput

            def _run(self):
                pass

        tools = [Tool1(), Tool2()]
        formatted = OllamaToolSchemaFormatter.format_tools_for_ollama(tools)

        assert len(formatted) == 2
        assert formatted[0]['function']['name'] == 'tool1'
        assert formatted[1]['function']['name'] == 'tool2'

    def test_format_empty_tools_list(self):
        formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([])
        assert formatted == []

    def test_tool_schema_structure(self):
        tool = MockTool()
        formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

        func_schema = formatted[0]['function']
        assert func_schema['name'] == 'mock_tool'
        assert func_schema['description'] == 'A mock tool for testing'
        assert func_schema['parameters']['type'] == 'object'
        assert 'param1' in func_schema['parameters']['properties']

    def test_tool_parameters_preserved(self):
        tool = MockTool()
        formatted = OllamaToolSchemaFormatter.format_tools_for_ollama([tool])

        params = formatted[0]['function']['parameters']
        assert params['type'] == 'object'
        assert 'param1' in params['properties']
        assert 'required' in params
        assert 'param1' in params['required']

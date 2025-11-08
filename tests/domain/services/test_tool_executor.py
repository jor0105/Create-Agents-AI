import json
import time

import pytest

from src.domain import BaseTool, ToolExecutionResult, ToolExecutor


class MockCalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs basic mathematical calculations"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate",
            }
        },
        "required": ["expression"],
    }

    def execute(self, expression: str) -> str:
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")


class MockGreeterTool(BaseTool):
    name = "greeter"
    description = "Greets people by name"
    parameters = {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Name to greet"}},
        "required": ["name"],
    }

    def execute(self, name: str) -> str:
        return f"Hello, {name}!"


class TestToolExecutor:
    def test_initialization_with_tools(self):
        tools = [MockCalculatorTool(), MockGreeterTool()]
        executor = ToolExecutor(tools)

        assert executor.get_available_tool_names() == ["calculator", "greeter"]

    def test_initialization_without_tools(self):
        executor = ToolExecutor([])

        assert executor.get_available_tool_names() == []

    def test_has_tool(self):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        assert executor.has_tool("calculator") is True
        assert executor.has_tool("nonexistent") is False

    def test_execute_tool_success(self):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("calculator", expression="2 + 2")

        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert result.tool_name == "calculator"
        assert "4" in result.result
        assert result.error is None
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    def test_execute_tool_with_kwargs(self):
        tools = [MockGreeterTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("greeter", name="Alice")

        assert result.success is True
        assert "Alice" in result.result

    def test_execute_nonexistent_tool(self):
        executor = ToolExecutor([])

        result = executor.execute_tool("nonexistent", arg="value")

        assert result.success is False
        assert result.tool_name == "nonexistent"
        assert "not found" in result.error.lower()
        assert result.execution_time_ms is not None

    def test_execute_tool_with_invalid_arguments(self):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("calculator")

        assert result.success is False
        assert "invalid arguments" in result.error.lower()

    def test_execute_tool_with_execution_error(self):
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("calculator", expression="invalid + syntax")

        assert result.success is False
        assert result.error is not None

    def test_execute_multiple_tools(self):
        tools = [MockCalculatorTool(), MockGreeterTool()]
        executor = ToolExecutor(tools)

        tool_calls = [
            {"name": "calculator", "arguments": {"expression": "10 * 5"}},
            {"name": "greeter", "arguments": {"name": "Bob"}},
        ]

        results = executor.execute_multiple_tools(tool_calls)

        assert len(results) == 2
        assert results[0].success is True
        assert "50" in results[0].result
        assert results[1].success is True
        assert "Bob" in results[1].result

    def test_execute_multiple_tools_with_json_string_arguments(self):
        tools = [MockGreeterTool()]
        executor = ToolExecutor(tools)

        tool_calls = [
            {"name": "greeter", "arguments": json.dumps({"name": "Charlie"})},
        ]

        results = executor.execute_multiple_tools(tool_calls)

        assert len(results) == 1
        assert results[0].success is True
        assert "Charlie" in results[0].result

    def test_execute_multiple_tools_with_invalid_json(self):
        tools = [MockGreeterTool()]
        executor = ToolExecutor(tools)

        tool_calls = [
            {"name": "greeter", "arguments": "invalid json {{{"},
        ]

        results = executor.execute_multiple_tools(tool_calls)

        assert len(results) == 1
        assert results[0].success is False
        assert "invalid json" in results[0].error.lower()

    def test_tool_execution_result_to_dict(self):
        result = ToolExecutionResult(
            tool_name="test_tool",
            success=True,
            result="Test result",
            execution_time_ms=123.45,
        )

        result_dict = result.to_dict()

        assert result_dict["tool_name"] == "test_tool"
        assert result_dict["success"] is True
        assert result_dict["result"] == "Test result"
        assert result_dict["error"] is None
        assert result_dict["execution_time_ms"] == 123.45

    def test_tool_execution_result_to_llm_message_success(self):
        result = ToolExecutionResult(
            tool_name="calculator", success=True, result="Result: 42"
        )

        message = result.to_llm_message()

        assert "calculator" in message
        assert "successfully" in message.lower()
        assert "42" in message

    def test_tool_execution_result_to_llm_message_failure(self):
        result = ToolExecutionResult(
            tool_name="calculator", success=False, error="Invalid input"
        )

        message = result.to_llm_message()

        assert "calculator" in message
        assert "failed" in message.lower()
        assert "Invalid input" in message


@pytest.mark.unit
class TestToolExecutorEdgeCases:
    def test_execute_tool_with_none_value_argument(self):
        class NullableTool(BaseTool):
            name = "nullable"
            description = "Accepts None values"

            def execute(self, value=None) -> str:
                return f"Value: {value}"

        tools = [NullableTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("nullable", value=None)

        assert result.success is True
        assert "None" in result.result

    def test_execute_tool_tracks_execution_time(self):
        class SlowTool(BaseTool):
            name = "slow"
            description = "Slow tool"

            def execute(self) -> str:
                time.sleep(0.01)
                return "done"

        tools = [SlowTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("slow")

        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 10

    def test_execute_tool_tracks_time_on_failure(self):
        class FailingTool(BaseTool):
            name = "failing"
            description = "Always fails"

            def execute(self) -> str:
                raise RuntimeError("Tool error")

        tools = [FailingTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("failing")

        assert result.success is False
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    def test_execute_tool_with_extra_kwargs(self):
        class SimpleToolWithKwargs(BaseTool):
            name = "simple"
            description = "Simple tool"

            def execute(self, arg1: str) -> str:
                return arg1

        tools = [SimpleToolWithKwargs()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("simple", arg1="value", extra="ignored")

        assert result.success is False
        assert (
            "invalid arguments" in result.error.lower()
            or "unexpected" in result.error.lower()
        )

    def test_execute_tool_with_complex_return_types(self):
        class ComplexReturnTool(BaseTool):
            name = "complex"
            description = "Returns complex data"

            def execute(self) -> dict:
                return {"data": [1, 2, 3], "nested": {"key": "value"}}

        tools = [ComplexReturnTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("complex")

        assert result.success is True
        assert isinstance(result.result, dict)

    def test_execute_multiple_tools_with_empty_list(self):
        executor = ToolExecutor([])

        results = executor.execute_multiple_tools([])

        assert results == []
        assert isinstance(results, list)

    def test_execute_multiple_tools_handles_partial_failures(self):
        class SuccessTool(BaseTool):
            name = "success"
            description = "Always succeeds"

            def execute(self) -> str:
                return "success"

        class FailTool(BaseTool):
            name = "fail"
            description = "Always fails"

            def execute(self) -> str:
                raise ValueError("Expected failure")

        tools = [SuccessTool(), FailTool()]
        executor = ToolExecutor(tools)

        tool_calls = [
            {"name": "success", "arguments": {}},
            {"name": "fail", "arguments": {}},
            {"name": "success", "arguments": {}},
        ]

        results = executor.execute_multiple_tools(tool_calls)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    def test_execute_multiple_tools_continues_after_failure(self):
        class CounterTool(BaseTool):
            name = "counter"
            description = "Counts calls"
            call_count = 0

            def execute(self) -> str:
                CounterTool.call_count += 1
                return f"Call {CounterTool.call_count}"

        tools = [CounterTool()]
        executor = ToolExecutor(tools)

        CounterTool.call_count = 0

        tool_calls = [
            {"name": "counter", "arguments": {}},
            {"name": "nonexistent", "arguments": {}},
            {"name": "counter", "arguments": {}},
        ]

        results = executor.execute_multiple_tools(tool_calls)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert CounterTool.call_count == 2

    def test_get_available_tool_names_after_initialization(self):
        class Tool1(BaseTool):
            name = "tool_one"
            description = "First tool"

            def execute(self) -> str:
                return "one"

        class Tool2(BaseTool):
            name = "tool_two"
            description = "Second tool"

            def execute(self) -> str:
                return "two"

        tools = [Tool1(), Tool2()]
        executor = ToolExecutor(tools)

        names = executor.get_available_tool_names()

        assert len(names) == 2
        assert "tool_one" in names
        assert "tool_two" in names

    def test_executor_with_duplicate_tool_names(self):
        class Tool1(BaseTool):
            name = "duplicate"
            description = "First duplicate"

            def execute(self) -> str:
                return "first"

        class Tool2(BaseTool):
            name = "duplicate"
            description = "Second duplicate"

            def execute(self) -> str:
                return "second"

        tools = [Tool1(), Tool2()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("duplicate")

        assert result.success is True
        assert result.result == "second"

    def test_execute_tool_with_unicode_arguments(self):
        class UnicodeTool(BaseTool):
            name = "unicode"
            description = "Handles unicode"

            def execute(self, text: str) -> str:
                return f"Received: {text}"

        tools = [UnicodeTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("unicode", text="你好世界 🌍")

        assert result.success is True
        assert "你好世界" in result.result
        assert "🌍" in result.result

    def test_tool_execution_result_to_dict_with_none_values(self):
        result = ToolExecutionResult(
            tool_name="test",
            success=False,
            result=None,
            error=None,
            execution_time_ms=None,
        )

        result_dict = result.to_dict()

        assert result_dict["result"] is None
        assert result_dict["error"] is None
        assert result_dict["execution_time_ms"] is None

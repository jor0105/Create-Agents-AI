from src.domain import BaseTool, ToolExecutionResult, ToolExecutor


class MockCalculatorTool(BaseTool):
    """Mock calculator tool for testing."""

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
        """Execute calculation."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")


class MockGreeterTool(BaseTool):
    """Mock greeter tool for testing."""

    name = "greeter"
    description = "Greets people by name"
    parameters = {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Name to greet"}},
        "required": ["name"],
    }

    def execute(self, name: str) -> str:
        """Execute greeting."""
        return f"Hello, {name}!"


class TestToolExecutor:
    """Test suite for ToolExecutor."""

    def test_initialization_with_tools(self):
        """Test executor initialization with tools."""
        tools = [MockCalculatorTool(), MockGreeterTool()]
        executor = ToolExecutor(tools)

        assert executor.get_available_tool_names() == ["calculator", "greeter"]

    def test_initialization_without_tools(self):
        """Test executor initialization without tools."""
        executor = ToolExecutor()

        assert executor.get_available_tool_names() == []

    def test_has_tool(self):
        """Test checking if tool exists."""
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        assert executor.has_tool("calculator") is True
        assert executor.has_tool("nonexistent") is False

    def test_execute_tool_success(self):
        """Test successful tool execution."""
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
        """Test tool execution with keyword arguments."""
        tools = [MockGreeterTool()]
        executor = ToolExecutor(tools)

        result = executor.execute_tool("greeter", name="Alice")

        assert result.success is True
        assert "Alice" in result.result

    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        executor = ToolExecutor([])

        result = executor.execute_tool("nonexistent", arg="value")

        assert result.success is False
        assert result.tool_name == "nonexistent"
        assert "not found" in result.error.lower()
        assert result.execution_time_ms is not None

    def test_execute_tool_with_invalid_arguments(self):
        """Test tool execution with invalid arguments."""
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        # Missing required argument
        result = executor.execute_tool("calculator")

        assert result.success is False
        assert "invalid arguments" in result.error.lower()

    def test_execute_tool_with_execution_error(self):
        """Test tool that raises an error during execution."""
        tools = [MockCalculatorTool()]
        executor = ToolExecutor(tools)

        # Invalid expression that will cause eval to fail
        result = executor.execute_tool("calculator", expression="invalid + syntax")

        assert result.success is False
        assert result.error is not None

    def test_execute_multiple_tools(self):
        """Test executing multiple tools in sequence."""
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
        """Test multiple tool execution with JSON string arguments."""
        import json

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
        """Test multiple tool execution with invalid JSON arguments."""
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
        """Test converting ToolExecutionResult to dictionary."""
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
        """Test formatting successful result as LLM message."""
        result = ToolExecutionResult(
            tool_name="calculator", success=True, result="Result: 42"
        )

        message = result.to_llm_message()

        assert "calculator" in message
        assert "successfully" in message.lower()
        assert "42" in message

    def test_tool_execution_result_to_llm_message_failure(self):
        """Test formatting failed result as LLM message."""
        result = ToolExecutionResult(
            tool_name="calculator", success=False, error="Invalid input"
        )

        message = result.to_llm_message()

        assert "calculator" in message
        assert "failed" in message.lower()
        assert "Invalid input" in message

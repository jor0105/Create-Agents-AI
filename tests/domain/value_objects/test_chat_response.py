"""
Tests for ChatResponse and ToolCallInfo value objects.
"""

import pytest

from src.domain.value_objects.chat_response import ChatResponse, ToolCallInfo


@pytest.mark.unit
class TestToolCallInfo:
    """Test suite for ToolCallInfo value object."""

    def test_create_tool_call_info_with_all_fields(self):
        """Test creating ToolCallInfo with all fields."""
        tool_call = ToolCallInfo(
            tool_name="web_search",
            arguments={"query": "Python tutorials"},
            result="Found 10 results",
            success=True,
        )

        assert tool_call.tool_name == "web_search"
        assert tool_call.arguments == {"query": "Python tutorials"}
        assert tool_call.result == "Found 10 results"
        assert tool_call.success is True

    def test_create_tool_call_info_minimal(self):
        """Test creating ToolCallInfo with minimal required fields."""
        tool_call = ToolCallInfo(
            tool_name="calculator",
            arguments={"expression": "2+2"},
            result="4",
        )

        assert tool_call.tool_name == "calculator"
        assert tool_call.arguments == {"expression": "2+2"}
        assert tool_call.result == "4"
        assert tool_call.success is True  # default value

    def test_tool_call_info_is_frozen(self):
        """Test that ToolCallInfo is immutable."""
        tool_call = ToolCallInfo(
            tool_name="test",
            arguments={},
            result="result",
        )

        with pytest.raises(AttributeError):
            tool_call.tool_name = "modified"

    def test_tool_call_info_with_failed_execution(self):
        """Test ToolCallInfo with failed execution."""
        tool_call = ToolCallInfo(
            tool_name="api_call",
            arguments={"endpoint": "/users"},
            result="Error: Connection timeout",
            success=False,
        )

        assert tool_call.success is False
        assert "Error" in tool_call.result

    def test_tool_call_info_with_empty_arguments(self):
        """Test ToolCallInfo with empty arguments."""
        tool_call = ToolCallInfo(
            tool_name="time",
            arguments={},
            result="2024-01-01 12:00:00",
        )

        assert tool_call.arguments == {}
        assert len(tool_call.arguments) == 0

    def test_tool_call_info_with_complex_arguments(self):
        """Test ToolCallInfo with complex nested arguments."""
        complex_args = {
            "query": "search term",
            "filters": {
                "category": "tech",
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            },
            "limit": 10,
        }
        tool_call = ToolCallInfo(
            tool_name="advanced_search",
            arguments=complex_args,
            result="Results found",
        )

        assert tool_call.arguments == complex_args
        assert "filters" in tool_call.arguments
        assert tool_call.arguments["filters"]["category"] == "tech"

    def test_tool_call_info_with_long_result(self):
        """Test ToolCallInfo with long result string."""
        long_result = "A" * 10000
        tool_call = ToolCallInfo(
            tool_name="large_data",
            arguments={},
            result=long_result,
        )

        assert len(tool_call.result) == 10000
        assert tool_call.result == long_result

    def test_tool_call_info_with_special_characters(self):
        """Test ToolCallInfo with special characters in result."""
        tool_call = ToolCallInfo(
            tool_name="translate",
            arguments={"text": "Hello"},
            result="你好 🌟 Bonjour!",
        )

        assert "你好" in tool_call.result
        assert "🌟" in tool_call.result
        assert "Bonjour" in tool_call.result

    def test_tool_call_info_equality(self):
        """Test equality of ToolCallInfo instances."""
        tool_call1 = ToolCallInfo(
            tool_name="test",
            arguments={"x": 1},
            result="result",
            success=True,
        )
        tool_call2 = ToolCallInfo(
            tool_name="test",
            arguments={"x": 1},
            result="result",
            success=True,
        )
        tool_call3 = ToolCallInfo(
            tool_name="test",
            arguments={"x": 2},
            result="result",
            success=True,
        )

        assert tool_call1 == tool_call2
        assert tool_call1 != tool_call3

    def test_tool_call_info_with_different_argument_types(self):
        """Test ToolCallInfo with various argument types."""
        tool_call = ToolCallInfo(
            tool_name="multi_type",
            arguments={
                "string": "text",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "list": [1, 2, 3],
                "none": None,
            },
            result="Processed",
        )

        assert isinstance(tool_call.arguments["string"], str)
        assert isinstance(tool_call.arguments["integer"], int)
        assert isinstance(tool_call.arguments["float"], float)
        assert isinstance(tool_call.arguments["boolean"], bool)
        assert isinstance(tool_call.arguments["list"], list)
        assert tool_call.arguments["none"] is None


@pytest.mark.unit
class TestChatResponse:
    """Test suite for ChatResponse value object."""

    def test_create_chat_response_with_content_only(self):
        """Test creating ChatResponse with content only."""
        response = ChatResponse(content="Hello, how can I help you?")

        assert response.content == "Hello, how can I help you?"
        assert response.tool_calls == []
        assert isinstance(response.tool_calls, list)

    def test_create_chat_response_with_tool_calls(self):
        """Test creating ChatResponse with tool calls."""
        tool_call = ToolCallInfo(
            tool_name="calculator",
            arguments={"expression": "2+2"},
            result="4",
        )
        response = ChatResponse(
            content="The result is 4",
            tool_calls=[tool_call],
        )

        assert response.content == "The result is 4"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].tool_name == "calculator"

    def test_create_chat_response_with_multiple_tool_calls(self):
        """Test ChatResponse with multiple tool calls."""
        tool_calls = [
            ToolCallInfo("tool1", {"arg": "1"}, "result1"),
            ToolCallInfo("tool2", {"arg": "2"}, "result2"),
            ToolCallInfo("tool3", {"arg": "3"}, "result3"),
        ]
        response = ChatResponse(
            content="Executed 3 tools",
            tool_calls=tool_calls,
        )

        assert len(response.tool_calls) == 3
        assert response.tool_calls[0].tool_name == "tool1"
        assert response.tool_calls[1].tool_name == "tool2"
        assert response.tool_calls[2].tool_name == "tool3"

    def test_chat_response_is_frozen(self):
        """Test that ChatResponse is immutable."""
        response = ChatResponse(content="Test")

        with pytest.raises(AttributeError):
            response.content = "Modified"

    def test_has_tool_calls_returns_false_when_empty(self):
        """Test has_tool_calls returns False when no tools were called."""
        response = ChatResponse(content="No tools used")

        assert response.has_tool_calls() is False

    def test_has_tool_calls_returns_true_when_present(self):
        """Test has_tool_calls returns True when tools were called."""
        tool_call = ToolCallInfo("test", {}, "result")
        response = ChatResponse(content="Used tool", tool_calls=[tool_call])

        assert response.has_tool_calls() is True

    def test_has_tool_calls_with_multiple_tools(self):
        """Test has_tool_calls with multiple tool calls."""
        tool_calls = [
            ToolCallInfo("tool1", {}, "result1"),
            ToolCallInfo("tool2", {}, "result2"),
        ]
        response = ChatResponse(content="Used tools", tool_calls=tool_calls)

        assert response.has_tool_calls() is True
        assert len(response.tool_calls) == 2

    def test_to_dict_with_no_tool_calls(self):
        """Test to_dict conversion with no tool calls."""
        response = ChatResponse(content="Simple response")

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result["content"] == "Simple response"
        assert result["tool_calls"] == []

    def test_to_dict_with_tool_calls(self):
        """Test to_dict conversion with tool calls."""
        tool_call = ToolCallInfo(
            tool_name="calculator",
            arguments={"expression": "5*5"},
            result="25",
            success=True,
        )
        response = ChatResponse(content="Result is 25", tool_calls=[tool_call])

        result = response.to_dict()

        assert result["content"] == "Result is 25"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool_name"] == "calculator"
        assert result["tool_calls"][0]["arguments"] == {"expression": "5*5"}
        assert result["tool_calls"][0]["result"] == "25"
        assert result["tool_calls"][0]["success"] is True

    def test_to_dict_with_multiple_tool_calls(self):
        """Test to_dict with multiple tool calls."""
        tool_calls = [
            ToolCallInfo("search", {"q": "python"}, "Found 100 results", True),
            ToolCallInfo("filter", {"type": "tutorial"}, "Filtered", True),
        ]
        response = ChatResponse(content="Search completed", tool_calls=tool_calls)

        result = response.to_dict()

        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["tool_name"] == "search"
        assert result["tool_calls"][1]["tool_name"] == "filter"

    def test_to_dict_structure(self):
        """Test that to_dict returns correct structure."""
        response = ChatResponse(content="Test")

        result = response.to_dict()

        assert set(result.keys()) == {"content", "tool_calls"}
        assert isinstance(result["content"], str)
        assert isinstance(result["tool_calls"], list)

    def test_chat_response_with_empty_content(self):
        """Test ChatResponse with empty content string."""
        response = ChatResponse(content="")

        assert response.content == ""
        assert response.has_tool_calls() is False

    def test_chat_response_with_long_content(self):
        """Test ChatResponse with very long content."""
        long_content = "A" * 100000
        response = ChatResponse(content=long_content)

        assert len(response.content) == 100000
        assert response.content == long_content

    def test_chat_response_with_multiline_content(self):
        """Test ChatResponse with multiline content."""
        multiline = "Line 1\nLine 2\nLine 3"
        response = ChatResponse(content=multiline)

        assert "\n" in response.content
        assert response.content.count("\n") == 2

    def test_chat_response_with_special_characters(self):
        """Test ChatResponse with special characters."""
        special = "Hello! 你好 🤖 @#$%^&*()"
        response = ChatResponse(content=special)

        assert "你好" in response.content
        assert "🤖" in response.content

    def test_chat_response_equality(self):
        """Test equality of ChatResponse instances."""
        response1 = ChatResponse(content="Test")
        response2 = ChatResponse(content="Test")
        response3 = ChatResponse(content="Different")

        assert response1 == response2
        assert response1 != response3

    def test_chat_response_with_failed_tool_call(self):
        """Test ChatResponse with failed tool execution."""
        failed_call = ToolCallInfo(
            tool_name="api_call",
            arguments={"url": "http://example.com"},
            result="Error: Connection refused",
            success=False,
        )
        response = ChatResponse(
            content="Tool execution failed",
            tool_calls=[failed_call],
        )

        assert response.has_tool_calls() is True
        assert response.tool_calls[0].success is False
        assert "Error" in response.tool_calls[0].result

    def test_to_dict_preserves_all_tool_call_fields(self):
        """Test that to_dict preserves all ToolCallInfo fields."""
        tool_call = ToolCallInfo(
            tool_name="test_tool",
            arguments={"key": "value"},
            result="test result",
            success=True,
        )
        response = ChatResponse(content="Test", tool_calls=[tool_call])

        result = response.to_dict()
        tool_dict = result["tool_calls"][0]

        assert "tool_name" in tool_dict
        assert "arguments" in tool_dict
        assert "result" in tool_dict
        assert "success" in tool_dict

    def test_chat_response_default_tool_calls(self):
        """Test that tool_calls defaults to empty list."""
        response = ChatResponse(content="Test")

        assert response.tool_calls == []
        assert isinstance(response.tool_calls, list)
        assert len(response.tool_calls) == 0


@pytest.mark.unit
class TestChatResponseEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_response_with_tool_call_without_result(self):
        """Test response with tool call that has no result."""
        tool_call = ToolCallInfo(
            tool_name="void_tool",
            arguments={},
            result="",
        )
        response = ChatResponse(content="Void call", tool_calls=[tool_call])

        assert response.has_tool_calls() is True
        assert response.tool_calls[0].result == ""

    def test_response_with_mixed_success_tool_calls(self):
        """Test response with both successful and failed tool calls."""
        tool_calls = [
            ToolCallInfo("success1", {}, "OK", success=True),
            ToolCallInfo("failed", {}, "Error", success=False),
            ToolCallInfo("success2", {}, "OK", success=True),
        ]
        response = ChatResponse(content="Mixed results", tool_calls=tool_calls)

        assert len(response.tool_calls) == 3
        successful = [tc for tc in response.tool_calls if tc.success]
        failed = [tc for tc in response.tool_calls if not tc.success]

        assert len(successful) == 2
        assert len(failed) == 1

    def test_to_dict_with_complex_nested_arguments(self):
        """Test to_dict with deeply nested tool arguments."""
        complex_args = {
            "level1": {
                "level2": {"level3": {"level4": {"data": "deep"}}},
                "array": [1, 2, {"nested": "value"}],
            }
        }
        tool_call = ToolCallInfo("complex", complex_args, "result")
        response = ChatResponse(content="Test", tool_calls=[tool_call])

        result = response.to_dict()
        args = result["tool_calls"][0]["arguments"]

        assert args["level1"]["level2"]["level3"]["level4"]["data"] == "deep"
        assert args["level1"]["array"][2]["nested"] == "value"

    def test_has_tool_calls_is_consistent(self):
        """Test that has_tool_calls is consistent with tool_calls list."""
        # No tools
        response1 = ChatResponse(content="Test")
        assert response1.has_tool_calls() == (len(response1.tool_calls) > 0)

        # With tools
        tool_call = ToolCallInfo("test", {}, "result")
        response2 = ChatResponse(content="Test", tool_calls=[tool_call])
        assert response2.has_tool_calls() == (len(response2.tool_calls) > 0)

    def test_multiple_responses_are_independent(self):
        """Test that multiple ChatResponse instances are independent."""
        tool_call1 = ToolCallInfo("tool1", {}, "result1")
        response1 = ChatResponse(content="Response 1", tool_calls=[tool_call1])

        tool_call2 = ToolCallInfo("tool2", {}, "result2")
        response2 = ChatResponse(content="Response 2", tool_calls=[tool_call2])

        assert response1.content != response2.content
        assert response1.tool_calls[0].tool_name != response2.tool_calls[0].tool_name

    def test_to_dict_returns_new_dict(self):
        """Test that to_dict returns a new dict each time."""
        response = ChatResponse(content="Test")

        dict1 = response.to_dict()
        dict2 = response.to_dict()

        assert dict1 == dict2
        assert dict1 is not dict2

    def test_response_with_json_like_content(self):
        """Test response with JSON-formatted content."""
        json_content = '{"key": "value", "number": 42}'
        response = ChatResponse(content=json_content)

        assert response.content == json_content
        assert "{" in response.content
        assert "}" in response.content

    def test_tool_call_info_with_none_result(self):
        """Test ToolCallInfo with None as result."""
        tool_call = ToolCallInfo(
            tool_name="none_tool",
            arguments={},
            result="None",  # String "None", not None object
        )

        assert tool_call.result == "None"
        assert isinstance(tool_call.result, str)

    def test_large_number_of_tool_calls(self):
        """Test ChatResponse with many tool calls."""
        tool_calls = [
            ToolCallInfo(f"tool_{i}", {"index": i}, f"result_{i}") for i in range(100)
        ]
        response = ChatResponse(content="Many tools", tool_calls=tool_calls)

        assert len(response.tool_calls) == 100
        assert response.has_tool_calls() is True
        result_dict = response.to_dict()
        assert len(result_dict["tool_calls"]) == 100

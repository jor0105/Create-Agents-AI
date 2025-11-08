import pytest

from src.infra.adapters.Ollama.ollama_tool_call_parser import OllamaToolCallParser


@pytest.mark.unit
class TestOllamaToolCallParser:
    def test_has_tool_calls_with_empty_string(self):
        result = OllamaToolCallParser.has_tool_calls("")

        assert result is False

    def test_has_tool_calls_with_none(self):
        result = OllamaToolCallParser.has_tool_calls(None)

        assert result is False

    def test_has_tool_calls_with_non_string(self):
        result = OllamaToolCallParser.has_tool_calls(12345)

        assert result is False

    def test_has_tool_calls_with_xml_tool_call(self):
        response = """
        <tool_call>
          <name>web_search</name>
          <arguments>
            <query>Python tutorials</query>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.has_tool_calls(response)

        assert result is True

    def test_has_tool_calls_with_json_tool_call(self):
        response = """
        <tool_call>
        {
          "name": "web_search",
          "arguments": {"query": "Python tutorials"}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.has_tool_calls(response)

        assert result is True

    def test_has_tool_calls_with_mixed_content(self):
        response = """
        Let me search for that information.
        <tool_call>
          <name>search</name>
          <arguments><query>test</query></arguments>
        </tool_call>
        Here's what I found.
        """

        result = OllamaToolCallParser.has_tool_calls(response)

        assert result is True

    def test_has_tool_calls_without_tool_calls(self):
        response = "This is just regular text without any tool calls."

        result = OllamaToolCallParser.has_tool_calls(response)

        assert result is False

    def test_extract_tool_calls_from_empty_string(self):
        result = OllamaToolCallParser.extract_tool_calls("")

        assert result == []

    def test_extract_tool_calls_from_plain_text(self):
        response = "Just some plain text"

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert result == []

    def test_extract_tool_calls_xml_single_tool(self):
        response = """
        <tool_call>
          <name>get_weather</name>
          <arguments>
            <location>Paris</location>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["arguments"] == {"location": "Paris"}

    def test_extract_tool_calls_xml_multiple_arguments(self):
        response = """
        <tool_call>
          <name>get_weather</name>
          <arguments>
            <location>Tokyo</location>
            <unit>celsius</unit>
            <include_forecast>true</include_forecast>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["arguments"]["location"] == "Tokyo"
        assert result[0]["arguments"]["unit"] == "celsius"
        assert result[0]["arguments"]["include_forecast"] is True

    def test_extract_tool_calls_xml_no_arguments(self):
        response = """
        <tool_call>
          <name>get_current_time</name>
          <arguments></arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "get_current_time"
        assert result[0]["arguments"] == {}

    def test_extract_tool_calls_xml_missing_arguments_element(self):
        response = """
        <tool_call>
          <name>no_params_tool</name>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "no_params_tool"
        assert result[0]["arguments"] == {}

    def test_extract_tool_calls_json_single_tool(self):
        response = """
        <tool_call>
        {
          "name": "web_search",
          "arguments": {"query": "Python tutorials"}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "web_search"
        assert result[0]["arguments"] == {"query": "Python tutorials"}

    def test_extract_tool_calls_json_multiple_arguments(self):
        response = """
        <tool_call>
        {
          "name": "search",
          "arguments": {
            "query": "test",
            "limit": 10,
            "sort": "desc",
            "include_archived": false
          }
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["arguments"]["limit"] == 10
        assert result[0]["arguments"]["include_archived"] is False

    def test_extract_tool_calls_json_nested_arguments(self):
        response = """
        <tool_call>
        {
          "name": "advanced_search",
          "arguments": {
            "query": "test",
            "filters": {
              "date_from": "2024-01-01",
              "categories": ["tech", "science"]
            }
          }
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["arguments"]["filters"]["date_from"] == "2024-01-01"
        assert result[0]["arguments"]["filters"]["categories"] == ["tech", "science"]

    def test_extract_tool_calls_multiple_tools(self):
        response = """
        First, I'll search for information.
        <tool_call>
          <name>web_search</name>
          <arguments><query>AI trends</query></arguments>
        </tool_call>
        Then I'll get the weather.
        <tool_call>
        {
          "name": "get_weather",
          "arguments": {"location": "Tokyo"}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 2
        assert result[0]["name"] == "web_search"
        assert result[1]["name"] == "get_weather"

    def test_extract_tool_calls_xml_value_type_conversion(self):
        response = """
        <tool_call>
          <name>test_tool</name>
          <arguments>
            <count>42</count>
            <price>19.99</price>
            <active>true</active>
            <disabled>false</disabled>
            <name>test</name>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        args = result[0]["arguments"]
        assert args["count"] == 42
        assert args["price"] == 19.99
        assert args["active"] is True
        assert args["disabled"] is False
        assert args["name"] == "test"

    def test_extract_tool_calls_skips_invalid_xml(self):
        response = """
        <tool_call>
          <name>good_tool</name>
          <arguments><query>test</query></arguments>
        </tool_call>
        <tool_call>
          <name>bad_tool
          <arguments><incomplete
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "good_tool"

    def test_extract_tool_calls_skips_invalid_json(self):
        response = """
        <tool_call>
        {"name": "good_tool", "arguments": {}}
        </tool_call>
        <tool_call>
        {name: bad_json arguments: {}}
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "good_tool"

    def test_extract_tool_calls_json_without_name_fails(self):
        response = """
        <tool_call>
        {
          "arguments": {"query": "test"}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 0

    def test_extract_tool_calls_xml_without_name_fails(self):
        response = """
        <tool_call>
          <arguments><query>test</query></arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 0

    def test_extract_tool_calls_json_with_non_dict_arguments_fails(self):
        response = """
        <tool_call>
        {
          "name": "test_tool",
          "arguments": "not a dict"
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 0

    def test_extract_tool_calls_json_with_non_dict_root_fails(self):
        response = """
        <tool_call>
        ["array", "not", "object"]
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 0

    def test_remove_tool_calls_from_response(self):
        response = """
        Here is some text.
        <tool_call>
          <name>test</name>
          <arguments></arguments>
        </tool_call>
        More text after.
        """

        result = OllamaToolCallParser.remove_tool_calls_from_response(response)

        assert "<tool_call>" not in result
        assert "</tool_call>" not in result
        assert "Here is some text" in result
        assert "More text after" in result

    def test_remove_tool_calls_preserves_text_without_calls(self):
        response = "This is plain text without any tool calls"

        result = OllamaToolCallParser.remove_tool_calls_from_response(response)

        assert result == response

    def test_format_tool_results_for_llm(self):
        result = OllamaToolCallParser.format_tool_results_for_llm(
            tool_name="get_weather", result="Weather is sunny"
        )

        assert "<tool_result>" in result
        assert "</tool_result>" in result
        assert "<name>get_weather</name>" in result
        assert "<result>Weather is sunny</result>" in result

    def test_format_tool_results_with_multiline_result(self):
        multiline_result = """Line 1
Line 2
Line 3"""

        result = OllamaToolCallParser.format_tool_results_for_llm(
            tool_name="test", result=multiline_result
        )

        assert "Line 1" in result
        assert "Line 2" in result
        assert "\n" in result

    def test_format_tool_results_with_special_characters(self):
        special_result = "Result with <html> & special chars: 你好"

        result = OllamaToolCallParser.format_tool_results_for_llm(
            tool_name="test", result=special_result
        )

        assert "你好" in result
        assert "<html>" in result

    def test_extract_tool_calls_case_insensitive_tags(self):
        response = """
        <TOOL_CALL>
          <name>test_tool</name>
          <arguments><param>value</param></arguments>
        </TOOL_CALL>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "test_tool"

    def test_extract_tool_calls_with_whitespace_variations(self):
        response = """<tool_call>

        <name>test_tool</name>

        <arguments>

            <param>value</param>

        </arguments>

        </tool_call>"""

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "test_tool"

    def test_extract_tool_calls_xml_with_empty_string_values(self):
        response = """
        <tool_call>
          <name>test_tool</name>
          <arguments>
            <param></param>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["arguments"]["param"] == ""

    def test_extract_tool_calls_json_empty_arguments(self):
        response = """
        <tool_call>
        {
          "name": "no_params_tool",
          "arguments": {}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["arguments"] == {}

    def test_convert_value_handles_boolean_variations(self):
        assert OllamaToolCallParser._convert_value("true") is True
        assert OllamaToolCallParser._convert_value("True") is True
        assert OllamaToolCallParser._convert_value("TRUE") is True
        assert OllamaToolCallParser._convert_value("false") is False
        assert OllamaToolCallParser._convert_value("False") is False
        assert OllamaToolCallParser._convert_value("FALSE") is False

    def test_convert_value_handles_integers(self):
        assert OllamaToolCallParser._convert_value("42") == 42
        assert OllamaToolCallParser._convert_value("-10") == -10
        assert OllamaToolCallParser._convert_value("0") == 0

    def test_convert_value_handles_floats(self):
        assert OllamaToolCallParser._convert_value("3.14") == 3.14
        assert OllamaToolCallParser._convert_value("-2.5") == -2.5
        assert OllamaToolCallParser._convert_value("0.0") == 0.0

    def test_convert_value_keeps_strings(self):
        assert OllamaToolCallParser._convert_value("hello") == "hello"
        assert OllamaToolCallParser._convert_value("test123") == "test123"
        assert OllamaToolCallParser._convert_value("") == ""

    def test_extract_tool_calls_preserves_order(self):
        response = """
        <tool_call>
          <name>first_tool</name>
          <arguments></arguments>
        </tool_call>
        <tool_call>
          <name>second_tool</name>
          <arguments></arguments>
        </tool_call>
        <tool_call>
          <name>third_tool</name>
          <arguments></arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 3
        assert result[0]["name"] == "first_tool"
        assert result[1]["name"] == "second_tool"
        assert result[2]["name"] == "third_tool"

    def test_extract_tool_calls_handles_mixed_xml_json(self):
        response = """
        <tool_call>
          <name>xml_tool</name>
          <arguments><param>xml_value</param></arguments>
        </tool_call>
        <tool_call>
        {"name": "json_tool", "arguments": {"param": "json_value"}}
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 2
        assert result[0]["name"] == "xml_tool"
        assert result[0]["arguments"]["param"] == "xml_value"
        assert result[1]["name"] == "json_tool"
        assert result[1]["arguments"]["param"] == "json_value"

    def test_has_tool_calls_with_incomplete_tag(self):
        response = "<tool_call>incomplete"

        result = OllamaToolCallParser.has_tool_calls(response)

        assert result is False

    def test_extract_tool_calls_logs_parse_errors(self, caplog):
        import logging

        caplog.set_level(logging.ERROR)

        response = """
        <tool_call>
          {invalid json}
        </tool_call>
        """

        OllamaToolCallParser.extract_tool_calls(response)

    def test_remove_tool_calls_with_multiple_occurrences(self):
        response = """
        Text before
        <tool_call>first</tool_call>
        Middle text
        <tool_call>second</tool_call>
        Text after
        """

        result = OllamaToolCallParser.remove_tool_calls_from_response(response)

        assert result.count("<tool_call>") == 0
        assert result.count("</tool_call>") == 0
        assert "Text before" in result
        assert "Middle text" in result
        assert "Text after" in result

    def test_format_tool_results_with_empty_result(self):
        result = OllamaToolCallParser.format_tool_results_for_llm(
            tool_name="test", result=""
        )

        assert "<tool_result>" in result
        assert "<name>test</name>" in result
        assert "<result></result>" in result

    def test_extract_tool_calls_with_numeric_tool_names(self):
        response = """
        <tool_call>
          <name>tool_v2_updated</name>
          <arguments><param>value</param></arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["name"] == "tool_v2_updated"

    def test_extract_tool_calls_with_unicode_in_xml(self):
        response = """
        <tool_call>
          <name>translate_tool</name>
          <arguments>
            <text>你好世界</text>
            <target>English</target>
          </arguments>
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert result[0]["arguments"]["text"] == "你好世界"

    def test_extract_tool_calls_with_unicode_in_json(self):
        response = """
        <tool_call>
        {
          "name": "emoji_tool",
          "arguments": {"message": "Hello 🌍 World 🚀"}
        }
        </tool_call>
        """

        result = OllamaToolCallParser.extract_tool_calls(response)

        assert len(result) == 1
        assert "🌍" in result[0]["arguments"]["message"]
        assert "🚀" in result[0]["arguments"]["message"]

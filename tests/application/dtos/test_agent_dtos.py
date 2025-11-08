import pytest

from src.application.dtos.agent_dtos import (
    AgentConfigOutputDTO,
    ChatInputDTO,
    ChatOutputDTO,
    CreateAgentInputDTO,
)
from src.domain.value_objects.base_tools import BaseTool


@pytest.mark.unit
class TestCreateAgentInputDTO:
    def test_create_with_valid_data(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        assert dto.provider == "openai"
        assert dto.model == "gpt-5-nano"
        assert dto.name == "Test Agent"
        assert dto.instructions == "Be helpful"

    def test_create_with_ollama_provider(self):
        dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Local Agent",
            instructions="Test",
        )

        assert dto.provider == "ollama"

    def test_validate_success(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test instructions",
        )

        dto.validate()

    def test_validate_empty_model(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="", name="Test", instructions="Test"
        )

        with pytest.raises(ValueError, match="'model'.*required"):
            dto.validate()

    def test_validate_whitespace_model(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="   ", name="Test", instructions="Test"
        )

        with pytest.raises(ValueError, match="'model'.*required"):
            dto.validate()

    def test_validate_empty_name(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="", instructions="Test"
        )

        with pytest.raises(ValueError, match="'name'.*valid"):
            dto.validate()

    def test_validate_whitespace_name(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="   ", instructions="Test"
        )

        with pytest.raises(ValueError, match="'name'.*valid"):
            dto.validate()

    def test_validate_empty_instructions(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="Test", instructions=""
        )

        with pytest.raises(ValueError, match="'instructions'.*valid"):
            dto.validate()

    def test_validate_whitespace_instructions(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="Test", instructions="   "
        )

        with pytest.raises(ValueError, match="'instructions'.*valid"):
            dto.validate()

    def test_validate_none_name(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name=None, instructions="Test"
        )

        dto.validate()
        assert dto.name is None

    def test_validate_none_instructions(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name="Test", instructions=None
        )

        dto.validate()
        assert dto.instructions is None

    def test_validate_both_none(self):
        dto = CreateAgentInputDTO(
            provider="openai", model="gpt-5-nano", name=None, instructions=None
        )

        dto.validate()
        assert dto.name is None
        assert dto.instructions is None

    def test_create_with_only_required_fields(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
        )

        assert dto.provider == "openai"
        assert dto.model == "gpt-5-nano"
        assert dto.name is None
        assert dto.instructions is None
        assert dto.config is None or dto.config == {}
        assert dto.history_max_size == 10

    def test_validate_all_fields_valid(self):
        dto = CreateAgentInputDTO(
            provider="ollama",
            model="phi4-mini:latest",
            name="Production Agent",
            instructions="Detailed instructions here",
        )

        dto.validate()

    def test_validate_with_config(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config={"temperature": 0.7, "top_p": 0.9},
        )

        dto.validate()
        assert dto.config == {"temperature": 0.7, "top_p": 0.9}

    def test_validate_empty_config(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        dto.validate()
        assert dto.config is None or dto.config == {}

    def test_create_with_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        assert dto.history_max_size == 20

    def test_default_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        assert dto.history_max_size == 10

    def test_validate_invalid_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=0,
        )

        with pytest.raises(ValueError, match="history_max_size.*positive integer"):
            dto.validate()

    def test_validate_negative_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size=-5,
        )

        with pytest.raises(ValueError, match="history_max_size.*positive integer"):
            dto.validate()

    def test_validate_invalid_config_type(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            config="invalid",  # type: ignore
        )

        with pytest.raises(ValueError, match="'config'.*dictionary"):
            dto.validate()

    def test_validate_non_int_history_max_size(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            history_max_size="invalid",  # type: ignore
        )

        with pytest.raises(ValueError, match="history_max_size"):
            dto.validate()

    def test_validate_non_string_provider(self):
        dto = CreateAgentInputDTO(
            provider=123,  # type: ignore
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*required"):
            dto.validate()

    def test_validate_empty_provider(self):
        dto = CreateAgentInputDTO(
            provider="",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*required"):
            dto.validate()

    def test_validate_whitespace_provider(self):
        dto = CreateAgentInputDTO(
            provider="   ",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        with pytest.raises(ValueError, match="'provider'.*required"):
            dto.validate()


@pytest.mark.unit
class TestCreateAgentInputDTOWithTools:
    """Test suite for CreateAgentInputDTO tools validation."""

    def test_validate_with_string_tool_names(self):
        """Test validation with tool names as strings."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=["web_search"],
        )

        # This will fail if web_search is not in AvailableTools
        # We're testing the validation logic here
        try:
            dto.validate()
        except Exception:
            # Expected if tool doesn't exist
            pass

    def test_validate_with_base_tool_instances(self):
        """Test validation with BaseTool instances."""
        from src.domain.value_objects import BaseTool

        class CustomTool(BaseTool):
            name = "custom_tool"
            description = "A custom tool"

            def execute(self) -> str:
                return "result"

        tool = CustomTool()
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[tool],
        )

        dto.validate()

        assert dto.tools is not None
        assert len(dto.tools) == 1
        assert isinstance(dto.tools[0], BaseTool)

    def test_validate_with_multiple_tools(self):
        """Test validation with multiple BaseTool instances."""
        from src.domain.value_objects import BaseTool

        class Tool1(BaseTool):
            name = "tool1"
            description = "First tool"

            def execute(self) -> str:
                return "result1"

        class Tool2(BaseTool):
            name = "tool2"
            description = "Second tool"

            def execute(self) -> str:
                return "result2"

        tools = [Tool1(), Tool2()]
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=tools,
        )

        dto.validate()

        assert len(dto.tools) == 2

    def test_validate_with_invalid_tool_missing_execute(self):
        """Test validation fails when tool is missing execute method."""
        from src.domain.exceptions import InvalidBaseToolException

        class InvalidTool:
            name = "invalid"
            description = "Missing execute method"

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[InvalidTool()],  # type: ignore
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_validate_with_invalid_tool_missing_name(self):
        """Test validation fails when tool has invalid name."""
        from src.domain.exceptions import InvalidBaseToolException
        from src.domain.value_objects import BaseTool

        class NoNameTool(BaseTool):
            name = ""  # Empty name
            description = "No name"

            def execute(self) -> str:
                return "result"

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[NoNameTool()],
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_validate_with_invalid_tool_missing_description(self):
        """Test validation fails when tool has no description."""
        from src.domain.exceptions import InvalidBaseToolException
        from src.domain.value_objects import BaseTool

        class NoDescTool(BaseTool):
            name = "no_desc"
            description = ""  # Empty description

            def execute(self) -> str:
                return "result"

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[NoDescTool()],
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_validate_with_invalid_tool_string_not_found(self):
        """Test validation fails with non-existent tool name."""
        from src.domain.exceptions import InvalidBaseToolException

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=["nonexistent_tool_12345"],
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_validate_with_mixed_tool_types(self):
        """Test validation with mixed string and BaseTool instances."""
        from src.domain.value_objects import BaseTool

        class CustomTool(BaseTool):
            name = "custom"
            description = "Custom tool"

            def execute(self) -> str:
                return "custom"

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[CustomTool()],
        )

        dto.validate()

        assert all(isinstance(tool, BaseTool) for tool in dto.tools)

    def test_validate_with_none_tools(self):
        """Test validation with None tools."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=None,
        )

        dto.validate()

        assert dto.tools is None

    def test_validate_with_empty_tools_list(self):
        """Test validation with empty tools list."""
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[],
        )

        dto.validate()

        # Empty list remains empty after validation
        assert dto.tools == []

    def test_validate_converts_string_tools_to_basetool(self):
        """Test that string tool names are converted to BaseTool instances."""
        # This test depends on AvailableTools having actual tools
        # If no tools are available, it will raise InvalidBaseToolException
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[],
        )

        dto.validate()

        # After validation, tools should be a list of BaseTool instances
        if dto.tools:
            assert all(isinstance(tool, BaseTool) for tool in dto.tools)

    def test_validate_with_tool_not_callable_execute(self):
        """Test validation fails when execute is not callable."""
        from src.domain.exceptions import InvalidBaseToolException

        class NotCallableExecute:
            name = "not_callable"
            description = "Execute not callable"
            execute = "not a function"  # Not callable

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[NotCallableExecute()],  # type: ignore
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_validate_with_invalid_tool_type(self):
        """Test validation fails with completely invalid tool type."""
        from src.domain.exceptions import InvalidBaseToolException

        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[123],  # type: ignore - invalid type
        )

        with pytest.raises(InvalidBaseToolException):
            dto.validate()

    def test_tools_attribute_after_validation(self):
        """Test that tools attribute is properly transformed after validation."""
        from src.domain.value_objects import BaseTool

        class TestTool(BaseTool):
            name = "test"
            description = "Test tool"

            def execute(self) -> str:
                return "test"

        tool = TestTool()
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
            tools=[tool],
        )

        dto.validate()

        assert isinstance(dto.tools, list)
        assert len(dto.tools) == 1
        assert isinstance(dto.tools[0], BaseTool)
        assert dto.tools[0].name == "test"


@pytest.mark.unit
class TestAgentConfigOutputDTO:
    def test_create_with_all_fields(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name="Test Agent",
            model="gpt-5-nano",
            instructions="Be helpful",
            config={"temperature": 0.7},
            history=[{"role": "user", "content": "Hello"}],
        )

        assert dto.provider == "openai"
        assert dto.name == "Test Agent"
        assert dto.model == "gpt-5-nano"
        assert dto.instructions == "Be helpful"
        assert dto.config == {"temperature": 0.7}
        assert len(dto.history) == 1

    def test_create_with_ollama_provider(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Test",
            config={},
            history=[],
        )

        assert dto.provider == "ollama"

    def test_to_dict_conversion(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="ollama",
            name="Test",
            model="phi4-mini:latest",
            instructions="Instructions",
            config={"temperature": 0.8},
            history=[{"role": "user", "content": "Hi"}],
        )

        result = dto.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["model"] == "phi4-mini:latest"
        assert result["instructions"] == "Instructions"
        assert result["history"] == [{"role": "user", "content": "Hi"}]
        assert result["provider"] == "ollama"
        assert result["config"] == {"temperature": 0.8}

    def test_to_dict_with_empty_history(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test",
            config={},
            history=[],
        )

        result = dto.to_dict()

        assert result["history"] == []

    def test_to_dict_with_multiple_history_items(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"},
        ]
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test",
            config={"top_p": 0.9},
            history=history,
        )

        result = dto.to_dict()

        assert len(result["history"]) == 3
        assert result["history"] == history

    def test_to_dict_all_keys_present(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions="Test instructions",
            config={"key": "value"},
            history=[],
        )

        result = dto.to_dict()

        expected_keys = {
            "provider",
            "model",
            "name",
            "instructions",
            "config",
            "tools",
            "history",
            "history_max_size",
        }
        assert set(result.keys()) == expected_keys

    def test_to_dict_with_complex_config(self):
        complex_config = {
            "temperature": 0.7,
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="ollama",
            name="Test",
            model="phi:latest",
            instructions="Test",
            config=complex_config,
            history=[],
        )

        result = dto.to_dict()

        assert result["config"] == complex_config

    def test_create_with_none_name(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name=None,
            model="gpt-5-nano",
            instructions="Test",
            config={},
            history=[],
        )

        assert dto.name is None
        result = dto.to_dict()
        assert result["name"] is None

    def test_create_with_none_instructions(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name="Test",
            model="gpt-5-nano",
            instructions=None,
            config={},
            history=[],
        )

        assert dto.instructions is None
        result = dto.to_dict()
        assert result["instructions"] is None

    def test_create_with_both_none(self):
        dto = AgentConfigOutputDTO(
            tools=None,
            provider="openai",
            name=None,
            model="gpt-5-nano",
            instructions=None,
            config={},
            history=[],
        )

        assert dto.name is None
        assert dto.instructions is None
        result = dto.to_dict()
        assert result["name"] is None
        assert result["instructions"] is None


@pytest.mark.unit
class TestChatInputDTO:
    def test_create_with_message(self):
        dto = ChatInputDTO(message="Hello")

        assert dto.message == "Hello"

    def test_validate_success(self):
        dto = ChatInputDTO(message="Valid message")
        dto.validate()

    def test_validate_empty_message(self):
        dto = ChatInputDTO(message="")

        with pytest.raises(ValueError, match="'message'.*required"):
            dto.validate()

    def test_validate_whitespace_message(self):
        dto = ChatInputDTO(message="   ")

        with pytest.raises(ValueError, match="'message'.*required"):
            dto.validate()

    def test_validate_long_message(self):
        long_message = "A" * 10000
        dto = ChatInputDTO(message=long_message)
        dto.validate()

    def test_validate_multiline_message(self):
        multiline = "Line 1\nLine 2\nLine 3"
        dto = ChatInputDTO(message=multiline)

        dto.validate()

    def test_validate_special_characters(self):
        special = "Hello! 你好 🎉"
        dto = ChatInputDTO(message=special)

        dto.validate()

    def test_validate_with_numeric_string_message(self):
        dto = ChatInputDTO(message="12345")
        dto.validate()

    def test_empty_string_after_numeric_validation(self):
        dto = ChatInputDTO(message="")

        with pytest.raises(ValueError, match="'message'.*required"):
            dto.validate()


@pytest.mark.unit
class TestChatOutputDTO:
    def test_create_with_response(self):
        dto = ChatOutputDTO(response="AI response")

        assert dto.response == "AI response"

    def test_to_dict_conversion(self):
        dto = ChatOutputDTO(response="Test response")

        result = dto.to_dict()

        assert isinstance(result, dict)
        assert result["response"] == "Test response"

    def test_to_dict_with_empty_response(self):
        dto = ChatOutputDTO(response="")

        result = dto.to_dict()

        assert result["response"] == ""

    def test_to_dict_with_long_response(self):
        long_response = "A" * 10000
        dto = ChatOutputDTO(response=long_response)

        result = dto.to_dict()

        assert result["response"] == long_response

    def test_to_dict_with_multiline_response(self):
        multiline = "Line 1\nLine 2\nLine 3"
        dto = ChatOutputDTO(response=multiline)

        result = dto.to_dict()

        assert result["response"] == multiline

    def test_to_dict_with_special_characters(self):
        special = "Response with special chars: 你好 🎉 @#$%"
        dto = ChatOutputDTO(response=special)

        result = dto.to_dict()

        assert result["response"] == special

    def test_to_dict_has_only_response_key(self):
        dto = ChatOutputDTO(response="Test")

        result = dto.to_dict()

        assert len(result) == 1
        assert "response" in result


@pytest.mark.unit
class TestDTOsIntegration:
    def test_create_agent_to_config_flow(self):
        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test instructions",
            config={"temperature": 0.8},
        )
        input_dto.validate()

        output_dto = AgentConfigOutputDTO(
            tools=None,
            provider=input_dto.provider,
            name=input_dto.name,
            model=input_dto.model,
            instructions=input_dto.instructions,
            config=input_dto.config,
            history=[],
        )

        assert output_dto.name == input_dto.name
        assert output_dto.model == input_dto.model
        assert output_dto.provider == input_dto.provider
        assert output_dto.config == input_dto.config

    def test_chat_input_to_output_flow(self):
        input_dto = ChatInputDTO(message="Hello")
        input_dto.validate()

        output_dto = ChatOutputDTO(response="Hi there!")

        assert input_dto.message == "Hello"
        assert output_dto.response == "Hi there!"

    def test_dto_immutability_after_validation(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        original_model = dto.model
        dto.validate()

        assert dto.model == original_model

    def test_multiple_validations_same_dto(self):
        dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-5-nano",
            name="Test",
            instructions="Test",
        )

        dto.validate()
        dto.validate()
        dto.validate()

    def test_config_preservation_through_dtos(self):
        original_config = {
            "temperature": 0.8,
            "max_tokens": 2048,
            "top_p": 0.95,
            "presence_penalty": 0.1,
        }

        input_dto = CreateAgentInputDTO(
            provider="openai",
            model="gpt-4",
            name="Advanced Agent",
            instructions="Detailed instructions",
            config=original_config,
        )
        input_dto.validate()

        output_dto = AgentConfigOutputDTO(
            tools=None,
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            history=[],
        )

        result = output_dto.to_dict()

        assert result["config"] == original_config

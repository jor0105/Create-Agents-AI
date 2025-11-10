from unittest.mock import MagicMock, Mock, patch

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter

IA_OLLAMA_TEST_1: str = "phi4-mini:latest"
IA_OLLAMA_TEST_2: str = "gemma3:4b"


def _mock_response(content="Response", tool_calls=None, get_return=None):
    m = MagicMock()
    m.message = MagicMock()
    m.message.content = content
    m.message.tool_calls = tool_calls
    m.get.return_value = get_return
    return m


@pytest.mark.unit
class TestOllamaChatAdapter:
    def test_initialization(self):
        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert hasattr(adapter, "_OllamaChatAdapter__logger")
        assert hasattr(adapter, "_OllamaChatAdapter__metrics")
        assert hasattr(adapter, "_OllamaChatAdapter__host")
        assert hasattr(adapter, "_OllamaChatAdapter__max_retries")

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_valid_input(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Ollama response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Be helpful",
            config={},
            tools=None,
            history=[],
            user_ask="Hello",
        )

        assert response == "Ollama response"
        mock_chat.assert_called_once()

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_constructs_messages_correctly(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="System instruction",
            config={},
            tools=None,
            history=[{"role": "user", "content": "Previous message"}],
            user_ask="User question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "System instruction"}
        assert messages[1] == {"role": "user", "content": "Previous message"}
        assert messages[2] == {"role": "user", "content": "User question"}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Instructions",
            config={},
            tools=None,
            history=[],
            user_ask="Question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 2

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiple_history_items(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Msg 2"},
            {"role": "assistant", "content": "Reply 2"},
        ]

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Instructions",
            config={},
            tools=None,
            history=history,
            user_ask="New question",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 6

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_correct_model(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs["model"] == IA_OLLAMA_TEST_1

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_response_raises_error(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match="Ollama returned multiple empty responses"
        ):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_none_response_raises_error(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content=None, tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match="Ollama returned multiple empty responses"
        ):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_missing_message_key_raises_error(self, mock_chat):
        class BadMessage:
            tool_calls = None

            @property
            def content(self):
                raise AttributeError("'dict' object has no attribute 'content'")

        mock_response = MagicMock()
        mock_response.message = BadMessage()
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match="An error occurred while communicating with Ollama"
        ):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_attribute_error_raises_chat_exception(self, mock_chat):
        class BadResponse:
            @property
            def message(self):
                raise AttributeError("'ChatResponse' object has no attribute 'message'")

        mock_chat.return_value = BadResponse()

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match="An error occurred while communicating with Ollama"
        ):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_type_error_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = TypeError("Invalid type")

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="A type error occurred"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_generic_exception_raises_chat_exception(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Connection error")

        adapter = OllamaChatAdapter()

        with pytest.raises(
            ChatException, match="An error occurred while communicating with Ollama"
        ):
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_preserves_original_error(self, mock_chat):
        original_error = RuntimeError("Original error")
        mock_chat.side_effect = original_error

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )
        except ChatException as e:
            assert e.original_error is original_error

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_propagates_chat_exception(self, mock_chat):
        original_exception = ChatException("Original chat error")
        mock_chat.side_effect = original_exception

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

        assert exc_info.value is original_exception

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_special_characters(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Resposta com 你好 e emojis 🎉", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test 你好",
            config={},
            tools=None,
            history=[],
            user_ask="Question 🎉",
        )

        assert "你好" in response
        assert "🎉" in response

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_multiline_content(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Line 1\nLine 2\nLine 3", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Multi\nline\ninstructions",
            config={},
            tools=None,
            history=[],
            user_ask="Multi\nline\nquestion",
        )

        assert "\n" in response
        assert "Line 1" in response

    def test_adapter_implements_chat_repository_interface(self):
        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_metrics_on_success(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Success response", tool_calls=None, get_return=100
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 100
        assert metrics[0].latency_ms > 0

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_metrics_on_failure(self, mock_chat):
        mock_chat.side_effect = RuntimeError("Test error")

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_2
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_collects_multiple_metrics(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test 1",
        )

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test 2",
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[1].model == IA_OLLAMA_TEST_2

    def test_get_metrics_returns_copy(self):
        adapter = OllamaChatAdapter()

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        assert metrics1 is not metrics2

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_string_in_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Previous response"},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=history,
            user_ask="New question",
        )

        assert response == "Response"
        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 4

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_long_history(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        history = []
        for i in range(25):
            history.append({"role": "user", "content": f"Message {i}"})
            history.append({"role": "assistant", "content": f"Reply {i}"})

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            tools=None,
            history=history,
            user_ask="Final question",
        )

        assert response == "Response"
        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 52

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_config_parameter(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        config = {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9}

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config=config,
            tools=None,
            history=[],
            user_ask="Test",
        )

        assert response == "Response"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_key_error_raises_chat_exception(self, mock_chat):
        mock_response = MagicMock()
        mock_response.message.tool_calls = None
        type(mock_response.message).content = property(
            lambda self: (_ for _ in ()).throw(KeyError("test_key"))
        )
        mock_chat.return_value = mock_response

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException, match="invalid format.*Missing key"):
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_metrics_contain_error_message_on_empty_response(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].error_message is not None
        assert metrics[0].success is False

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_temperature_config(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={"temperature": 0.7},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs.get("options") == {"temperature": 0.7}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_max_tokens_as_num_predict(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={"max_tokens": 500},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs.get("options") == {"num_predict": 500}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_top_p_config(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={"top_p": 0.9},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs.get("options") == {"top_p": 0.9}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_passes_all_configs(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9,
        }

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config=config,
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        expected_options = {
            "temperature": 0.7,
            "num_predict": 500,
            "top_p": 0.9,
        }
        assert call_args.kwargs.get("options") == expected_options

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_empty_config_does_not_pass_options(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        assert call_args.kwargs.get("options") in (None, {})
        assert "model" in call_args.kwargs
        assert "messages" in call_args.kwargs

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.subprocess.run")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_stop_model_is_called_after_chat(self, mock_chat, mock_subprocess):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )
        mock_subprocess.return_value = Mock()

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == ["ollama", "stop", IA_OLLAMA_TEST_1]

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.subprocess.run")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_stop_model_called_even_on_error(self, mock_chat, mock_subprocess):
        mock_chat.side_effect = Exception("Chat error")
        mock_subprocess.return_value = Mock()

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model=IA_OLLAMA_TEST_2,
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )
        except Exception:
            pass

        mock_subprocess.assert_called_once()

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.subprocess.run")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_stop_model_handles_file_not_found(self, mock_chat, mock_subprocess):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )
        mock_subprocess.side_effect = FileNotFoundError("ollama not found")

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        assert response == "Response"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.subprocess.run")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_stop_model_handles_timeout(self, mock_chat, mock_subprocess):
        import subprocess

        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ollama", 10)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        assert response == "Response"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.subprocess.run")
    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_stop_model_handles_generic_exception(self, mock_chat, mock_subprocess):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )
        mock_subprocess.side_effect = RuntimeError("Unknown error")

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        assert response == "Response"

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_none_instructions_omits_system_message(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions=None,
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Test"}

    @patch("src.infra.adapters.Ollama.ollama_chat_adapter.chat")
    def test_chat_with_whitespace_only_instructions(self, mock_chat):
        mock_chat.return_value = _mock_response(
            content="Response", tool_calls=None, get_return=None
        )

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="   \n\t  ",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        call_args = mock_chat.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_initialization_reads_environment_variables(self):
        with patch(
            "src.infra.adapters.Ollama.ollama_chat_adapter.EnvironmentConfig.get_env"
        ) as mock_get_env:
            mock_get_env.side_effect = lambda key, default: {
                "OLLAMA_HOST": "http://custom-host:11434",
                "OLLAMA_MAX_RETRIES": "5",
            }.get(key, default)

            OllamaChatAdapter()

            assert mock_get_env.call_count >= 2

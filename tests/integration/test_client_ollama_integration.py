import os

import pytest

from src.domain.exceptions import ChatException
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter

IA_OLLAMA_TEST_1: str = "granite4:latest"  # aceita tools e configs
IA_OLLAMA_TEST_2: str = "gemma3:4b"  # não aceita tools, aceita configs


def _check_ollama_available():
    import subprocess

    if os.getenv("CI"):
        pytest.skip("Skipping real Ollama integration test on CI (set CI=0 to run)")

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        if result.returncode != 0:
            pytest.skip("Ollama is not available or not running")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("Ollama is not installed or not responding")


def _check_model_available(model: str):
    import subprocess

    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        if model not in result.stdout:
            pytest.skip(
                f"Model {model} is not available in Ollama. Run: ollama pull {model}"
            )
    except Exception as e:
        pytest.skip(f"Could not verify available models: {e}")


@pytest.fixture(scope="session", autouse=True)
def teardown_ollama_models():
    yield

    import subprocess

    if os.getenv("CI"):
        return

    models = [IA_OLLAMA_TEST_1, IA_OLLAMA_TEST_2]

    try:
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=3)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return

    for m in models:
        try:
            subprocess.run(["ollama", "stop", m], capture_output=True, timeout=10)
        except Exception:
            continue


@pytest.mark.integration
class TestOllamaChatAdapterIntegration:
    def test_adapter_initialization(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        assert adapter is not None
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)
        assert hasattr(adapter, "get_metrics")
        assert callable(adapter.get_metrics)

    def test_chat_with_real_ollama_simple_question(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="What is 2+2?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response or "four" in response.lower()

    def test_chat_with_second_model(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant. Answer with one word only.",
            config={},
            tools=None,
            history=[],
            user_ask="What color is the sky? Answer with one word.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_history(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            tools=None,
            history=history,
            user_ask="What is my name?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "alice" in response.lower()

    def test_chat_with_complex_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a math teacher. Explain concepts simply and clearly.",
            config={},
            tools=None,
            history=[],
            user_ask="What is a prime number?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert any(
            word in response.lower()
            for word in ["prime", "number", "divisible", "divide"]
        )

    def test_chat_with_multiple_history_items(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = [
            {"role": "user", "content": "I like pizza."},
            {"role": "assistant", "content": "Pizza is delicious!"},
            {"role": "user", "content": "My favorite is pepperoni."},
            {"role": "assistant", "content": "Pepperoni is a classic choice!"},
        ]

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a friendly assistant.",
            config={},
            tools=None,
            history=history,
            user_ask="What food did I mention?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "pizza" in response.lower()

    def test_chat_with_special_characters(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Respond briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="Say hello in Chinese (你好) and add a celebration emoji 🎉",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_multiline_input(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        multiline_question = """
        Please answer this question:
        What are the three primary colors?
        List them one per line.
        """

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant.",
            config={},
            tools=None,
            history=[],
            user_ask=multiline_question,
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_collects_metrics_on_success(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="Say 'test'.",
        )

        assert response is not None

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[0].success is True
        assert metrics[0].latency_ms > 0
        assert metrics[0].error_message is None

    def test_chat_with_invalid_model_raises_error(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        with pytest.raises(ChatException):
            adapter.chat(
                model="invalid-model-that-does-not-exist",
                instructions="Test",
                config={},
                tools=None,
                history=[],
                user_ask="Test",
            )

    def test_chat_collects_metrics_on_failure(self):
        _check_ollama_available()

        adapter = OllamaChatAdapter()

        try:
            adapter.chat(
                model="invalid-model-xyz-123",
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
        assert metrics[0].model == "invalid-model-xyz-123"
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    def test_chat_with_empty_user_ask(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            tools=None,
            history=[],
            user_ask="",
        )

        assert response is not None
        assert isinstance(response, str)

    def test_chat_with_empty_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="",
            config={},
            tools=None,
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_none_instructions(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions=None,
            config={},
            tools=None,
            history=[],
            user_ask="What is 1+1?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_multiple_sequential_chats(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="Say 'first'.",
        )

        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="Say 'second'.",
        )

        assert response1 is not None
        assert response2 is not None
        assert response1 != response2

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert all(m.success for m in metrics)

    def test_chat_with_both_models(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="What is Python?",
        )

        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Answer briefly.",
            config={},
            tools=None,
            history=[],
            user_ask="What is Python?",
        )

        assert response1 is not None
        assert response2 is not None
        assert isinstance(response1, str)
        assert isinstance(response2, str)

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OLLAMA_TEST_1
        assert metrics[1].model == IA_OLLAMA_TEST_2
        assert all(m.success for m in metrics)

    def test_adapter_implements_chat_repository_interface(self):
        _check_ollama_available()

        from src.application.interfaces.chat_repository import ChatRepository

        adapter = OllamaChatAdapter()

        assert isinstance(adapter, ChatRepository)

    def test_chat_with_long_conversation_history(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        history = []
        for i in range(5):
            history.append({"role": "user", "content": f"Message number {i+1}"})
            history.append(
                {"role": "assistant", "content": f"Response to message {i+1}"}
            )

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant.",
            config={},
            tools=None,
            history=history,
            user_ask="How many messages did I send before this one?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_response_is_not_empty(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="You are a helpful assistant.",
            config={},
            tools=None,
            history=[],
            user_ask="Hello!",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert response.strip() != ""

    def test_get_metrics_returns_copy(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Test",
            config={},
            tools=None,
            history=[],
            user_ask="Test",
        )

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        assert metrics1 is not metrics2
        assert len(metrics1) == len(metrics2)

    def test_chat_with_config_parameter(self):
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.7,
            "max_tokens": 100,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config=config,
            tools=None,
            history=[],
            user_ask="Say hello.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestOllamaChatAdapterToolsIntegration:
    """Comprehensive tests for tools integration with Ollama adapter."""

    def test_chat_with_currentdate_tool_get_date(self):
        """Test CurrentDateTool with 'date' action using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_currentdate_tool_get_time(self):
        """Test CurrentDateTool with 'time' action using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask="What time is it now in UTC? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_currentdate_tool_multiple_actions(self):
        """Test CurrentDateTool with different actions using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        # Test timestamp
        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask="What is the current Unix timestamp? Use the current_date tool.",
        )

        assert response1 is not None
        assert isinstance(response1, str)
        assert len(response1) > 0

        # Test datetime
        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask="What is the current date and time in America/New_York? Use the current_date tool.",
        )

        assert response2 is not None
        assert isinstance(response2, str)
        assert len(response2) > 0

    def test_chat_with_currentdate_tool_different_timezones(self):
        """Test CurrentDateTool with multiple timezones using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        timezones = ["UTC", "America/Sao_Paulo"]

        for tz in timezones:
            response = adapter.chat(
                model=IA_OLLAMA_TEST_1,
                instructions="You are a helpful assistant. Use tools when appropriate.",
                config={},
                tools=tools,
                history=[],
                user_ask=f"What time is it in {tz}? Use the current_date tool.",
            )

            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0

    def test_chat_with_readlocalfile_tool_text_file(self):
        """Test ReadLocalFileTool with a text file using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        import os

        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        # Check if ReadLocalFileTool is available
        tool_names = [t.name for t in tools]
        if "read_local_file" not in tool_names:
            pytest.skip(
                "ReadLocalFileTool not available (missing optional dependencies)"
            )

        file_path = os.path.abspath(".fixtures/sample_text.txt")

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask=f"Read the file at {file_path} and tell me how many lines it has. Use the read_local_file tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_readlocalfile_tool_csv_file(self):
        """Test ReadLocalFileTool with a CSV file using Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        import os

        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        # Check if ReadLocalFileTool is available
        tool_names = [t.name for t in tools]
        if "read_local_file" not in tool_names:
            pytest.skip(
                "ReadLocalFileTool not available (missing optional dependencies)"
            )

        file_path = os.path.abspath(".fixtures/sample_data.csv")

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask=f"Read the CSV file at {file_path} and tell me the names in it. Use the read_local_file tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_tools_and_configs_combined(self):
        """Test using tools and configs simultaneously with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        config = {
            "temperature": 0.7,
            "max_tokens": 200,
            "top_p": 0.9,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config=config,
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC? Use the current_date tool.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        # Check metrics reflect config usage
        metrics = adapter.get_metrics()
        assert len(metrics) > 0
        assert metrics[-1].success

    def test_chat_with_multiple_tool_calls_in_conversation(self):
        """Test multiple tool calls in a conversation with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)
        from src.infra.config.available_tools import AvailableTools

        adapter = OllamaChatAdapter()
        tools = list(AvailableTools.get_available_tools().values())

        # First tool call
        response1 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=[],
            user_ask="What is today's date in UTC?",
        )

        assert response1 is not None
        history = [
            {"role": "user", "content": "What is today's date in UTC?"},
            {"role": "assistant", "content": response1},
        ]

        # Second tool call
        response2 = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="You are a helpful assistant. Use tools when appropriate.",
            config={},
            tools=tools,
            history=history,
            user_ask="What time is it now in America/Sao_Paulo?",
        )

        assert response2 is not None
        assert isinstance(response2, str)
        assert len(response2) > 0


@pytest.mark.integration
class TestOllamaChatAdapterConfigEdgeCases:
    """Comprehensive tests for config edge cases and combinations with Ollama."""

    def test_chat_with_all_configs_combined(self):
        """Test all configs combined with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.5,
            "max_tokens": 100,
            "top_p": 0.8,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config=config,
            tools=None,
            history=[],
            user_ask="What is Python?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_only_temperature_config(self):
        """Test using only temperature config with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {"temperature": 0.3}

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Answer briefly.",
            config=config,
            tools=None,
            history=[],
            user_ask="Say hello.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_only_max_tokens_config(self):
        """Test using only max_tokens config with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {"max_tokens": 50}

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Be very brief.",
            config=config,
            tools=None,
            history=[],
            user_ask="What is AI?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_only_top_p_config(self):
        """Test using only top_p config with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {"top_p": 0.7}

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer briefly.",
            config=config,
            tools=None,
            history=[],
            user_ask="Explain ML.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_temperature_and_max_tokens(self):
        """Test combining temperature and max_tokens with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.4,
            "max_tokens": 80,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Be concise.",
            config=config,
            tools=None,
            history=[],
            user_ask="What is coding?",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_temperature_and_top_p(self):
        """Test combining temperature and top_p with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_2)

        adapter = OllamaChatAdapter()

        config = {
            "temperature": 0.6,
            "top_p": 0.85,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_2,
            instructions="Be helpful.",
            config=config,
            tools=None,
            history=[],
            user_ask="Tell me about data.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_max_tokens_and_top_p(self):
        """Test combining max_tokens and top_p with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        config = {
            "max_tokens": 120,
            "top_p": 0.75,
        }

        response = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Answer concisely.",
            config=config,
            tools=None,
            history=[],
            user_ask="Explain algorithms.",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_boundary_temperature_values(self):
        """Test temperature boundary values with Ollama."""
        _check_ollama_available()
        _check_model_available(IA_OLLAMA_TEST_1)

        adapter = OllamaChatAdapter()

        # Min temperature
        config_min = {"temperature": 0.0}
        response_min = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Be consistent.",
            config=config_min,
            tools=None,
            history=[],
            user_ask="Say hi.",
        )

        assert response_min is not None
        assert isinstance(response_min, str)

        # Max temperature
        config_max = {"temperature": 2.0}
        response_max = adapter.chat(
            model=IA_OLLAMA_TEST_1,
            instructions="Be creative.",
            config=config_max,
            tools=None,
            history=[],
            user_ask="Say hello.",
        )

        assert response_max is not None
        assert isinstance(response_max, str)

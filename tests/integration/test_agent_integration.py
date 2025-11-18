import os

import pytest

from createagents.application import CreateAgent
from createagents.domain import InvalidAgentConfigException

IA_OLLAMA_TEST_1: str = "granite4:latest"
IA_OLLAMA_TEST_2: str = "gpt-oss:120b-cloud"
IA_OPENAI_TEST_1: str = "gpt-4.1-mini"
IA_OPENAI_TEST_2: str = "gpt-5-nano"


def _get_openai_api_key():
    from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI
    from createagents.infra.config.environment import EnvironmentConfig

    if os.getenv("CI"):
        pytest.skip("Skipping real API integration test on CI (set CI=0 to run)")

    try:
        api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
        return api_key
    except EnvironmentError:
        pytest.skip(
            f"Skipping integration test: {ClientOpenAI.API_OPENAI_NAME} not found in .env file"
        )


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


def _check_ollama_model_available(model: str):
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


@pytest.mark.integration
class TestCreateAgentInitializationErrors:
    def test_initialization_with_empty_model_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider="openai",
                model="",
                name="Test Agent",
                instructions="Be helpful",
            )

    def test_initialization_with_empty_name_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider="openai",
                model="gpt-5-mini",
                name="",
                instructions="Be helpful",
            )

    def test_initialization_with_empty_instructions_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            CreateAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="",
            )

    def test_initialization_with_none_name(self):
        agent = CreateAgent(
            provider="openai",
            model="gpt-5-mini",
            name=None,
            instructions="Be helpful",
        )
        configs = agent.get_configs()
        assert configs["name"] is None

    def test_initialization_with_none_instructions(self):
        agent = CreateAgent(
            provider="openai",
            model="gpt-5-mini",
            name="Test Agent",
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs["instructions"] is None

    def test_initialization_with_both_none(self):
        agent = CreateAgent(
            provider="openai",
            model="gpt-5-mini",
            name=None,
            instructions=None,
        )
        configs = agent.get_configs()
        assert configs["name"] is None
        assert configs["instructions"] is None

    def test_initialization_with_only_required_fields(self):
        agent = CreateAgent(
            provider="openai",
            model="gpt-5-mini",
        )
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == "gpt-5-mini"
        assert configs["name"] is None
        assert configs["instructions"] is None

    def test_initialization_with_invalid_provider_raises_error(self):
        with pytest.raises(Exception):
            CreateAgent(
                provider="invalid_provider_xyz",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
            )

    def test_initialization_with_zero_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            CreateAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size_raises_error(self):
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            CreateAgent(
                provider="openai",
                model="gpt-5-mini",
                name="Test Agent",
                instructions="Be helpful",
                history_max_size=-5,
            )


@pytest.mark.integration
class TestCreateAgentInitializationSuccessOpenAI:
    def test_initialization_with_openai_gpt4_mini(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Test Agent OpenAI",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_1
        assert configs["name"] == "Test Agent OpenAI"

    def test_initialization_with_openai_gpt4_nano(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_2,
            name="Test Agent Nano",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_2

    def test_initialization_with_custom_config_openai(self):
        _get_openai_api_key()

        custom_config = {"temperature": 0.7, "max_tokens": 500, "top_p": 0.9}

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Custom Config Agent",
            instructions="Be creative",
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs["config"] == custom_config

    def test_initialization_with_custom_history_size_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Large History Agent",
            instructions="Remember our conversation",
            history_max_size=50,
        )

        configs = agent.get_configs()
        assert configs["history_max_size"] == 50


@pytest.mark.integration
class TestCreateAgentInitializationSuccessOllama:
    def test_initialization_with_ollama_phi4(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Test Agent Ollama",
            instructions="You are a helpful assistant",
        )

        assert agent is not None
        configs = agent.get_configs()
        assert configs["provider"] == "ollama"
        assert configs["model"] == IA_OLLAMA_TEST_1
        assert configs["name"] == "Test Agent Ollama"

    def test_initialization_with_custom_config_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        custom_config = {
            "temperature": 0.5,
        }

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Custom Config Ollama",
            instructions="Be precise",
            config=custom_config,
        )

        configs = agent.get_configs()
        assert configs["config"] == custom_config

    def test_initialization_with_custom_history_size_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Small History Agent",
            instructions="Keep context",
            history_max_size=5,
        )

        configs = agent.get_configs()
        assert configs["history_max_size"] == 5


@pytest.mark.integration
class TestCreateAgentChatOpenAI:
    def test_simple_chat_with_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Chat Agent",
            instructions="You are a helpful assistant. Answer briefly.",
        )

        response = agent.chat("What is 2+2?")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response

    def test_multiple_chats_with_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="History Agent",
            instructions="You are a helpful assistant. Remember the context.",
        )

        response1 = agent.chat("My name is Jordan")
        assert response1 is not None

        response2 = agent.chat("What is my name?")
        assert response2 is not None
        assert "Jordan" in response2 or "jordan" in response2.lower()

    def test_chat_with_empty_message_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Empty Test Agent",
            instructions="Answer any question",
        )

        try:
            response = agent.chat("")
            assert isinstance(response, str)
        except Exception:
            pass

    def test_chat_with_long_message_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Long Message Agent",
            instructions="Summarize the text briefly.",
        )

        long_message = "This is a test. " * 100
        response = agent.chat(long_message)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_with_unicode_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Unicode Agent",
            instructions="You are a multilingual assistant.",
        )

        response = agent.chat("Olá! Como você está? 你好 🌍")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestCreateAgentChatOllama:
    def test_simple_chat_with_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_2)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_2,
            name="Chat Ollama Agent",
            instructions="You are a helpful assistant. Answer briefly.",
        )

        response = agent.chat("What is 2+2?")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_multiple_chats_with_history_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="History Ollama Agent",
            instructions="You are a helpful assistant. Always remember and recall information from previous messages when asked.",
        )

        response1 = agent.chat("My favorite color is blue")
        assert response1 is not None

        response2 = agent.chat("What is my favorite color?")
        assert response2 is not None
        assert "blue" in response2.lower() or "color" in response2.lower()

    def test_chat_with_unicode_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Unicode Ollama Agent",
            instructions="You are a multilingual assistant.",
        )

        response = agent.chat("Olá! 🌍")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestCreateAgentHistory:
    def test_clear_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Clear History Agent",
            instructions="Remember our conversation.",
        )

        agent.chat("My name is Jordan")

        configs = agent.get_configs()
        assert len(configs["history"]) > 0

        agent.clear_history()

        configs = agent.get_configs()
        assert len(configs["history"]) == 0

    def test_clear_history_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Clear History Ollama",
            instructions="Remember context.",
        )

        agent.chat("Hello")

        configs = agent.get_configs()
        assert len(configs["history"]) > 0

        agent.clear_history()

        configs = agent.get_configs()
        assert len(configs["history"]) == 0

    def test_history_max_size_enforcement_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Small History Agent",
            instructions="Chat briefly.",
            history_max_size=2,
        )

        agent.chat("First message")
        agent.chat("Second message")
        agent.chat("Third message")

        configs = agent.get_configs()
        assert len(configs["history"]) <= 2


@pytest.mark.integration
class TestCreateAgentMetrics:
    def test_get_metrics_after_chat_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Metrics Agent",
            instructions="Answer briefly.",
        )

        agent.chat("Hello")

        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0

        first_metric = metrics[0]
        assert hasattr(first_metric, "model")
        assert hasattr(first_metric, "latency_ms")
        assert first_metric.latency_ms > 0

    def test_get_metrics_after_multiple_chats_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Multi Metrics Agent",
            instructions="Answer briefly.",
        )

        agent.chat("First")
        agent.chat("Second")
        agent.chat("Third")

        metrics = agent.get_metrics()

        assert len(metrics) >= 3

    def test_export_metrics_json_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="JSON Metrics Agent",
            instructions="Answer briefly.",
        )

        agent.chat("Test")

        json_str = agent.export_metrics_json()

        assert json_str is not None
        assert isinstance(json_str, str)
        assert "summary" in json_str
        assert "metrics" in json_str

    def test_export_metrics_prometheus_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Prom Metrics Agent",
            instructions="Answer briefly.",
        )

        agent.chat("Test")

        prom_str = agent.export_metrics_prometheus()

        assert prom_str is not None
        assert isinstance(prom_str, str)
        assert "chat_requests_total" in prom_str

    def test_get_metrics_after_chat_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_1)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_1,
            name="Metrics Ollama Agent",
            instructions="Answer briefly.",
        )

        agent.chat("Hello")

        metrics = agent.get_metrics()

        assert metrics is not None
        assert isinstance(metrics, list)
        assert len(metrics) > 0


@pytest.mark.integration
class TestCreateAgentGetConfigs:
    def test_get_configs_returns_all_fields_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Config Test Agent",
            instructions="Test instructions",
            config={"temperature": 0.7},
            history_max_size=15,
        )

        configs = agent.get_configs()

        assert "provider" in configs
        assert "model" in configs
        assert "name" in configs
        assert "instructions" in configs
        assert "config" in configs
        assert "history" in configs
        assert "history_max_size" in configs

        assert configs["provider"] == "openai"
        assert configs["model"] == IA_OPENAI_TEST_1
        assert configs["name"] == "Config Test Agent"
        assert configs["history_max_size"] == 15

    def test_get_configs_returns_all_fields_ollama(self):
        _check_ollama_available()
        _check_ollama_model_available(IA_OLLAMA_TEST_2)

        agent = CreateAgent(
            provider="ollama",
            model=IA_OLLAMA_TEST_2,
            name="Config Ollama Agent",
            instructions="Test ollama",
            config={"temperature": 0.5},
            history_max_size=20,
        )

        configs = agent.get_configs()

        assert configs["provider"] == "ollama"
        assert configs["model"] == IA_OLLAMA_TEST_2
        assert configs["history_max_size"] == 20


@pytest.mark.integration
class TestCreateAgentEdgeCases:
    def test_agent_with_very_long_instructions_openai(self):
        _get_openai_api_key()

        long_instructions = "You are a helpful assistant. " * 100

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Long Instructions Agent",
            instructions=long_instructions,
        )

        response = agent.chat("Hello")

        assert response is not None
        assert isinstance(response, str)

    def test_agent_with_special_characters_in_name(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent-Test_123!@#",
            instructions="Be helpful",
        )

        configs = agent.get_configs()
        assert configs["name"] == "Agent-Test_123!@#"

    def test_chat_after_clear_history_openai(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Clear and Chat Agent",
            instructions="Remember context",
        )

        response1 = agent.chat("My name is Alice")
        assert response1 is not None

        agent.clear_history()

        response2 = agent.chat("What is my name?")
        assert response2 is not None

    def test_multiple_agents_same_model_independent(self):
        _get_openai_api_key()

        agent1 = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent 1",
            instructions="You are agent 1",
        )

        agent2 = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_1,
            name="Agent 2",
            instructions="You are agent 2",
        )

        agent1.chat("Hello from agent 1")

        configs2 = agent2.get_configs()
        assert len(configs2["history"]) == 0

    def test_agent_with_minimal_config(self):
        _get_openai_api_key()

        agent = CreateAgent(
            provider="openai",
            model=IA_OPENAI_TEST_2,
            name="Minimal Agent",
            instructions="Be helpful",
        )

        response = agent.chat("Hi")
        assert response is not None

        configs = agent.get_configs()
        assert configs["history_max_size"] == 10
        assert configs["config"] == {}

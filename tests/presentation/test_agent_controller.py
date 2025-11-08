from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions import InvalidAgentConfigException
from src.presentation.agent_controller import AIAgent


@pytest.mark.unit
class TestAIAgentInitialization:
    def test_initialization_creates_agent(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test Agent",
            instructions="Be helpful",
        )

        assert hasattr(controller, "_AIAgent__agent")

    def test_initialization_with_ollama_provider(self):
        controller = AIAgent(
            provider="ollama", model="gemma3:4b", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__agent")

    def test_initialization_creates_chat_use_case(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__chat_use_case")

    def test_initialization_creates_get_config_use_case(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        assert hasattr(controller, "_AIAgent__get_config_use_case")

    def test_initialization_with_invalid_data_raises_error(self):
        with pytest.raises(InvalidAgentConfigException):
            AIAgent(provider="openai", model="", name="Test", instructions="Test")

    def test_initialization_with_custom_config(self):
        config = {"temperature": 0.7, "max_tokens": 1000}
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            config=config,
        )

        agent = controller._AIAgent__agent
        assert agent.config == config

    def test_initialization_with_custom_history_max_size(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            history_max_size=20,
        )

        agent = controller._AIAgent__agent
        assert agent.history.max_size == 20

    def test_initialization_with_default_history_max_size(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.history.max_size == 10

    def test_initialization_with_invalid_provider_raises_error(self):
        with pytest.raises(Exception):
            AIAgent(
                provider="invalid_provider",
                model="gpt-5",
                name="Test",
                instructions="Test",
            )

    def test_initialization_with_none_name(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=None,
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.name is None

    def test_initialization_with_none_instructions(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions=None,
        )

        agent = controller._AIAgent__agent
        assert agent.instructions is None

    def test_initialization_with_both_none(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=None,
            instructions=None,
        )

        agent = controller._AIAgent__agent
        assert agent.name is None
        assert agent.instructions is None

    def test_initialization_with_only_required_fields(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
        )

        agent = controller._AIAgent__agent
        assert agent.provider == "openai"
        assert agent.model == "gpt-5"
        assert agent.name is None
        assert agent.instructions is None


@pytest.mark.unit
class TestAIAgentChat:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_returns_response(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "AI response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        response = controller.chat("Hello")

        assert response == "AI response"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_calls_use_case_with_correct_params(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        controller.chat("Test message")

        assert mock_use_case.execute.called
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == "Test message"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_empty_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        response = controller.chat("")

        assert response == "Response"
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == ""

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_when_use_case_raises_exception(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = Exception("API Error")
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        with pytest.raises(Exception, match="API Error"):
            controller.chat("Hello")

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_multiple_chat_calls(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.chat("Message 1")
        controller.chat("Message 2")

        assert mock_use_case.execute.call_count == 2

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_updates_agent_history(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "AI Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Hello")

        agent = controller._AIAgent__agent
        assert len(agent.history) == 2


@pytest.mark.unit
class TestAIAgentGetConfigs:
    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_returns_dict(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {
            "name": "Test",
            "model": "gpt-5-nano",
            "instructions": "Test",
            "history": [],
            "provider": "openai",
        }
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        config = controller.get_configs()

        assert isinstance(config, dict)
        assert "name" in config
        assert "model" in config

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_calls_use_case(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.to_dict.return_value = {}
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.get_configs()

        assert mock_use_case.execute.called

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_returns_all_expected_fields(self, mock_create_config):
        mock_use_case = Mock()
        mock_output = Mock()
        expected_config = {
            "name": "Test Agent",
            "model": "gpt-5",
            "instructions": "Be helpful",
            "history": [],
            "provider": "openai",
            "config": {"temperature": 0.7},
            "history_max_size": 10,
        }
        mock_output.to_dict.return_value = expected_config
        mock_use_case.execute.return_value = mock_output
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test Agent",
            instructions="Be helpful",
        )

        config = controller.get_configs()

        assert config == expected_config

    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_when_use_case_raises_exception(self, mock_create_config):
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = Exception("Config Error")
        mock_create_config.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        with pytest.raises(Exception, match="Config Error"):
            controller.get_configs()


@pytest.mark.unit
class TestAIAgentClearHistory:
    def test_clear_history_method_exists(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert hasattr(controller, "clear_history")
        assert callable(controller.clear_history)

    def test_clear_history_clears_agent_history(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        agent = controller._AIAgent__agent
        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")
        agent.add_user_message("Message 2")
        agent.add_assistant_message("Response 2")

        assert len(agent.history) == 4

        controller.clear_history()

        assert len(agent.history) == 0

    def test_clear_history_preserves_agent_config(self):
        controller = AIAgent(
            provider="ollama",
            model="gpt-5-nano",
            name="Test Agent",
            instructions="Be helpful",
        )

        agent = controller._AIAgent__agent
        original_model = agent.model
        original_name = agent.name
        original_instructions = agent.instructions
        original_provider = agent.provider

        controller.clear_history()

        assert agent.model == original_model
        assert agent.name == original_name
        assert agent.instructions == original_instructions
        assert agent.provider == original_provider

    def test_clear_history_can_be_called_multiple_times(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        agent = controller._AIAgent__agent
        agent.add_user_message("Message 1")
        agent.add_assistant_message("Response 1")
        assert len(controller._AIAgent__agent.history) > 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

        agent.add_user_message("Message 2")
        agent.add_assistant_message("Response 2")
        assert len(controller._AIAgent__agent.history) > 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

    def test_clear_history_on_empty_history(self):
        controller = AIAgent(
            provider="openai", model="gpt-5-mini", name="Test", instructions="Test"
        )

        assert len(controller._AIAgent__agent.history) == 0

        controller.clear_history()

        assert len(controller._AIAgent__agent.history) == 0

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_get_configs_after_clear_history_shows_empty_history(
        self, mock_create_config, mock_create_chat
    ):
        mock_chat_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_chat_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_chat_use_case

        mock_config_use_case = Mock()
        mock_create_config.return_value = mock_config_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.chat("Message 1")

        controller.clear_history()

        controller.get_configs()

        call_args = mock_config_use_case.execute.call_args
        agent_passed = call_args[0][0]
        assert len(agent_passed.history) == 0


@pytest.mark.unit
class TestAIAgentMetrics:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_returns_list(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert isinstance(metrics, list)
        assert len(metrics) == 1
        assert isinstance(metrics[0], ChatMetrics)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_calls_use_case_method(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        controller.get_metrics()

        mock_use_case.get_metrics.assert_called_once()

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_when_adapter_has_no_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert metrics == []

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_with_multiple_metrics(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50),
            ChatMetrics(model="gpt-5-nano", latency_ms=150.0, tokens_used=75),
            ChatMetrics(model="gpt-5-nano", latency_ms=120.0, tokens_used=60),
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        metrics = controller.get_metrics()

        assert len(metrics) == 3
        assert all(isinstance(m, ChatMetrics) for m in metrics)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert "gpt-5-nano" in json_str
        assert "summary" in json_str

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json_to_file(self, mock_create_chat, tmp_path):
        import json

        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0, tokens_used=50)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        filepath = tmp_path / "metrics.json"
        controller.export_metrics_json(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "summary" in data
        assert "metrics" in data

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        assert "chat_requests_total" in prom_text

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus_to_file(self, mock_create_chat, tmp_path):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5-nano", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        filepath = tmp_path / "metrics.prom"
        controller.export_metrics_prometheus(str(filepath))

        assert filepath.exists()

        with open(filepath, "r") as f:
            content = f.read()

        assert "chat_requests_total" in content

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json_with_empty_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert "summary" in json_str

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus_with_empty_metrics(self, mock_create_chat):
        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = []
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5-nano", name="Test", instructions="Test"
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)


@pytest.mark.unit
class TestAIAgentIntegration:
    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_and_get_configs_together(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        response = controller.chat("Hello")
        assert response == "Response"

        configs = controller.get_configs()
        assert isinstance(configs, dict)

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_clear_history_chat_again(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Message 1")
        agent = controller._AIAgent__agent
        assert len(agent.history) == 2

        controller.clear_history()
        assert len(agent.history) == 0

        controller.chat("Message 2")
        assert len(agent.history) == 2

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_metrics_accumulate_after_multiple_chats(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output

        metrics_list = []

        def get_metrics_side_effect():
            return metrics_list.copy()

        def execute_side_effect(agent, input_dto):
            metrics_list.append(ChatMetrics(model="gpt-5", latency_ms=100.0))
            return mock_output

        mock_use_case.get_metrics.side_effect = get_metrics_side_effect
        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Message 1")
        controller.chat("Message 2")
        controller.chat("Message 3")

        metrics = controller.get_metrics()
        assert len(metrics) == 3


@pytest.mark.unit
class TestAIAgentEdgeCases:
    def test_initialization_with_very_long_instructions(self):
        long_instructions = "A" * 10000
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions=long_instructions,
        )

        agent = controller._AIAgent__agent
        assert agent.instructions == long_instructions

    def test_initialization_with_special_characters_in_name(self):
        special_name = "Test-Agent_123!@#$%"
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=special_name,
            instructions="Test",
        )

        agent = controller._AIAgent__agent
        assert agent.name == special_name

    def test_initialization_with_unicode_characters(self):
        unicode_name = "测试代理 🤖"
        unicode_instructions = "Seja útil e educado 你好"

        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=unicode_name,
            instructions=unicode_instructions,
        )

        agent = controller._AIAgent__agent
        assert agent.name == unicode_name
        assert agent.instructions == unicode_instructions

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_very_long_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        long_message = "A" * 50000
        response = controller.chat(long_message)

        assert response == "Response"
        call_args = mock_use_case.execute.call_args
        assert call_args[0][1].message == long_message

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_with_unicode_message(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "回复"
        mock_use_case.execute.return_value = mock_output
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        unicode_message = "你好，世界！ 🌍"
        response = controller.chat(unicode_message)

        assert response == "回复"

    def test_initialization_with_history_max_size_zero(self):
        with pytest.raises(InvalidAgentConfigException, match="history_max_size"):
            AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                history_max_size=0,
            )

    def test_initialization_with_negative_history_max_size(self):
        try:
            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                history_max_size=-1,
            )
            assert hasattr(controller, "_AIAgent__agent")
        except (ValueError, InvalidAgentConfigException):
            pass

    def test_initialization_with_empty_config_dict(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            config={},
        )

        agent = controller._AIAgent__agent
        assert agent.config == {}

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_to_nonexistent_directory(self, mock_create_chat, tmp_path):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        nonexistent_path = tmp_path / "nonexistent" / "metrics.json"

        try:
            controller.export_metrics_json(str(nonexistent_path))
        except (FileNotFoundError, OSError):
            pass

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_chat_preserves_message_order(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("First message")
        controller.chat("Second message")
        controller.chat("Third message")

        agent = controller._AIAgent__agent
        history = agent.history.get_messages()

        assert len(history) == 6
        assert history[0].content == "First message"
        assert history[2].content == "Second message"
        assert history[4].content == "Third message"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_get_metrics_does_not_modify_internal_state(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()

        def get_metrics_side_effect():
            return [ChatMetrics(model="gpt-5", latency_ms=100.0)]

        mock_use_case.get_metrics.side_effect = get_metrics_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        metrics1 = controller.get_metrics()
        metrics1.clear()
        metrics2 = controller.get_metrics()
        assert len(metrics2) == 1

    def test_controller_has_all_required_methods(self):
        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        required_methods = [
            "chat",
            "get_configs",
            "clear_history",
            "get_metrics",
            "export_metrics_json",
            "export_metrics_prometheus",
        ]

        for method_name in required_methods:
            assert hasattr(controller, method_name), f"Missing method: {method_name}"
            assert callable(
                getattr(controller, method_name)
            ), f"{method_name} is not callable"

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_json_without_filepath(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        json_str = controller.export_metrics_json()

        assert isinstance(json_str, str)
        assert len(json_str) > 0
        assert "summary" in json_str

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_export_metrics_prometheus_without_filepath(self, mock_create_chat):
        from src.infra.config.metrics import ChatMetrics

        mock_use_case = Mock()
        mock_use_case.get_metrics.return_value = [
            ChatMetrics(model="gpt-5", latency_ms=100.0)
        ]
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        prom_text = controller.export_metrics_prometheus()

        assert isinstance(prom_text, str)
        assert len(prom_text) > 0

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    @patch("src.presentation.agent_controller.AgentComposer.create_get_config_use_case")
    def test_controller_workflow_chat_config_clear_repeat(
        self, mock_create_config, mock_create_chat
    ):
        mock_chat_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_chat_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_chat_use_case

        mock_config_use_case = Mock()
        mock_config_output = Mock()
        mock_config_output.to_dict.return_value = {
            "name": "Test",
            "model": "gpt-5",
            "history": [],
        }
        mock_config_use_case.execute.return_value = mock_config_output
        mock_create_config.return_value = mock_config_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Hello")
        agent = controller._AIAgent__agent
        assert len(agent.history) == 2

        configs = controller.get_configs()
        assert isinstance(configs, dict)

        controller.clear_history()
        assert len(agent.history) == 0

        controller.chat("New conversation")
        assert len(agent.history) == 2

        configs2 = controller.get_configs()
        assert isinstance(configs2, dict)

    def test_initialization_with_all_optional_params_none(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name=None,
            instructions=None,
            config=None,
        )

        agent = controller._AIAgent__agent
        assert agent.name is None
        assert agent.instructions is None
        assert agent.config == {}

    @patch("src.presentation.agent_controller.AgentComposer.create_chat_use_case")
    def test_multiple_consecutive_clear_history_calls(self, mock_create_chat):
        mock_use_case = Mock()
        mock_output = Mock()
        mock_output.response = "Response"

        def execute_side_effect(agent, input_dto):
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(mock_output.response)
            return mock_output

        mock_use_case.execute.side_effect = execute_side_effect
        mock_create_chat.return_value = mock_use_case

        controller = AIAgent(
            provider="openai", model="gpt-5", name="Test", instructions="Test"
        )

        controller.chat("Message")
        assert len(controller._AIAgent__agent.history) == 2

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

        controller.clear_history()
        assert len(controller._AIAgent__agent.history) == 0

    def test_initialization_provider_case_variations(self):
        providers = ["openai", "OPENAI", "OpenAI", "oPeNaI"]

        for provider in providers:
            controller = AIAgent(
                provider=provider, model="gpt-5", name="Test", instructions="Test"
            )

            agent = controller._AIAgent__agent
            assert agent.provider.lower() == "openai"

    def test_initialization_with_tools_none(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            tools=None,
        )

        agent = controller._AIAgent__agent
        assert agent.tools is None

    def test_initialization_with_tools_empty_list(self):
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            tools=[],
        )

        agent = controller._AIAgent__agent
        assert agent.tools == []

    def test_initialization_with_single_tool(self):
        from src.domain import BaseTool

        class TestTool(BaseTool):
            name = "test_tool"
            description = "A test tool"

            def execute(self, **kwargs):
                return "result"

        tool = TestTool()
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            tools=[tool],
        )

        agent = controller._AIAgent__agent
        assert len(agent.tools) == 1
        assert agent.tools[0] is tool

    def test_initialization_with_multiple_tools(self):
        from src.domain import BaseTool

        class Tool1(BaseTool):
            name = "tool1"
            description = "First tool"

            def execute(self, **kwargs):
                return "result1"

        class Tool2(BaseTool):
            name = "tool2"
            description = "Second tool"

            def execute(self, **kwargs):
                return "result2"

        tools = [Tool1(), Tool2()]
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            tools=tools,
        )

        agent = controller._AIAgent__agent
        assert len(agent.tools) == 2

    def test_initialization_with_string_tool_name(self):
        from src.infra import AvailableTools

        available = AvailableTools.get_available_tools()
        if available:
            tool_name = list(available.keys())[0]
            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[tool_name],
            )

            agent = controller._AIAgent__agent
            assert agent.tools is not None
        else:
            pytest.skip("No available tools to test")

    def test_initialization_with_mixed_tool_types(self):
        from src.domain import BaseTool
        from src.infra import AvailableTools

        class TestTool(BaseTool):
            name = "test_tool"
            description = "A test tool"

            def execute(self, **kwargs):
                return "result"

        tool = TestTool()
        available = AvailableTools.get_available_tools()
        if available:
            tool_name = list(available.keys())[0]
            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[tool, tool_name],
            )

            agent = controller._AIAgent__agent
            assert agent.tools is not None
        else:
            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[tool],
            )
            agent = controller._AIAgent__agent
            assert len(agent.tools) == 1

    def test_get_configs_includes_tools(self):
        from src.domain import BaseTool

        class TestTool(BaseTool):
            name = "test_tool"
            description = "A test tool"

            def execute(self, **kwargs):
                return "result"

        tool = TestTool()
        controller = AIAgent(
            provider="openai",
            model="gpt-5",
            name="Test",
            instructions="Test",
            tools=[tool],
        )

        config = controller.get_configs()

        assert "tools" in config

    def test_initialization_tools_preserved_through_chat(self):
        from unittest.mock import Mock, patch

        from src.domain import BaseTool

        class TestTool(BaseTool):
            name = "test_tool"
            description = "A test tool"

            def execute(self, **kwargs):
                return "result"

        tool = TestTool()

        with patch(
            "src.presentation.agent_controller.AgentComposer.create_chat_use_case"
        ) as mock_create_chat:
            mock_use_case = Mock()
            mock_output = Mock()
            mock_output.response = "Response"
            mock_use_case.execute.return_value = mock_output
            mock_create_chat.return_value = mock_use_case

            controller = AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[tool],
            )

            controller.chat("Hello")

            agent = controller._AIAgent__agent
            assert len(agent.tools) == 1

    def test_initialization_with_invalid_tool_type_raises_error(self):
        with pytest.raises(Exception):
            AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[123],
            )

    def test_initialization_with_tool_missing_attributes_raises_error(self):
        class InvalidTool:
            pass

        with pytest.raises(Exception):
            AIAgent(
                provider="openai",
                model="gpt-5",
                name="Test",
                instructions="Test",
                tools=[InvalidTool()],
            )

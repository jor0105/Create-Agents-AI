from unittest.mock import Mock, patch

import pytest

from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter
from src.infra.factories.chat_adapter_factory import ChatAdapterFactory


@pytest.mark.unit
class TestChatAdapterFactory:
    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_openai_adapter_with_gpt5(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert isinstance(adapter, OpenAIChatAdapter)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_openai_adapter_with_gpt5_mini(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert isinstance(adapter, OpenAIChatAdapter)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_openai_adapter_with_uppercase_gpt(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="GPT-5-NANO")

        assert isinstance(adapter, OpenAIChatAdapter)

    def test_create_ollama_adapter_with_phi4(self):
        adapter = ChatAdapterFactory.create(provider="ollama", model="phi4-mini:latest")

        assert isinstance(adapter, OllamaChatAdapter)

    def test_create_ollama_adapter_with_gemma(self):
        adapter = ChatAdapterFactory.create(provider="ollama", model="gemma3:4b")

        assert isinstance(adapter, OllamaChatAdapter)

    def test_create_with_invalid_provider(self):
        with pytest.raises(ValueError, match="Provider inválido"):
            ChatAdapterFactory.create(provider="invalid", model="gpt-5")

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_returns_cached_adapter(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert adapter1 is adapter2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_create_different_models_are_independent(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-nano")
        adapter2 = ChatAdapterFactory.create(provider="ollama", model="gemma3:4b")

        assert adapter1 is not adapter2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_cache_key_is_case_insensitive(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="GPT-5")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert adapter1 is adapter2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_cache_considers_provider(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="model-name")
        adapter2 = ChatAdapterFactory.create(provider="ollama", model="model-name")

        assert adapter1 is not adapter2
        assert isinstance(adapter1, OpenAIChatAdapter)
        assert isinstance(adapter2, OllamaChatAdapter)

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_clear_cache_forces_new_instances(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        ChatAdapterFactory.clear_cache()

        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert adapter1 is not adapter2

    @patch(
        "src.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch("src.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client")
    def test_factory_returns_chat_repository_interface(
        self, mock_get_client, mock_get_api_key
    ):
        from src.application.interfaces.chat_repository import ChatRepository

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert isinstance(adapter, ChatRepository)

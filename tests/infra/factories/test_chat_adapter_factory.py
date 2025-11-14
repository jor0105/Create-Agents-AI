from unittest.mock import Mock, patch

import pytest

from arcadiumai.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from arcadiumai.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter
from arcadiumai.infra.factories.chat_adapter_factory import ChatAdapterFactory


@pytest.mark.unit
class TestChatAdapterFactory:
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_create_openai_adapter_with_gpt5(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert isinstance(adapter, OpenAIChatAdapter)

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_create_openai_adapter_with_gpt5_mini(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert isinstance(adapter, OpenAIChatAdapter)

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
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
        with pytest.raises(ValueError, match="Invalid provider"):
            ChatAdapterFactory.create(provider="invalid", model="gpt-5")

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_create_returns_cached_adapter(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert adapter1 is adapter2

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
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
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_cache_key_is_case_insensitive(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="GPT-5")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert adapter1 is adapter2

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
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
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_clear_cache_forces_new_instances(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        ChatAdapterFactory.clear_cache()

        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5-mini")

        assert adapter1 is not adapter2

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_factory_returns_chat_repository_interface(
        self, mock_get_client, mock_get_api_key
    ):
        from arcadiumai.application.interfaces.chat_repository import ChatRepository

        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert isinstance(adapter, ChatRepository)

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_create_with_empty_provider_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="Invalid provider"):
            ChatAdapterFactory.create(provider="", model="gpt-5")

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_cache_persists_across_calls(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert mock_get_client.call_count == 1

        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert mock_get_client.call_count == 1
        assert adapter1 is adapter2

    def test_create_ollama_does_not_require_api_key(self):
        adapter = ChatAdapterFactory.create(provider="ollama", model="phi4")

        assert isinstance(adapter, OllamaChatAdapter)

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_cache_key_with_mixed_case(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="OpenAI", model="GPT-5")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")
        adapter3 = ChatAdapterFactory.create(provider="OPENAI", model="Gpt-5")

        assert adapter1 is adapter2
        assert adapter2 is adapter3

    def test_create_with_none_provider_raises_error(self):
        with pytest.raises((ValueError, AttributeError)):
            ChatAdapterFactory.create(provider=None, model="gpt-5")

    def test_create_with_none_model(self):
        try:
            adapter = ChatAdapterFactory.create(provider="ollama", model=None)
            assert adapter is not None
        except (ValueError, AttributeError, TypeError):
            pass

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_clear_cache_is_effective(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_get_client.side_effect = [mock_client1, mock_client2]

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        ChatAdapterFactory.clear_cache()

        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")

        assert adapter1 is not adapter2

    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
    )
    @patch(
        "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
    )
    def test_multiple_models_same_provider(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = "test-api-key"
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        ChatAdapterFactory.clear_cache()

        adapter1 = ChatAdapterFactory.create(provider="openai", model="gpt-4")
        adapter2 = ChatAdapterFactory.create(provider="openai", model="gpt-5")
        adapter3 = ChatAdapterFactory.create(provider="openai", model="gpt-3")

        assert adapter1 is not adapter2
        assert adapter2 is not adapter3
        assert adapter1 is not adapter3

    def test_create_with_special_characters_in_model_name(self):
        adapter = ChatAdapterFactory.create(provider="ollama", model="phi4-mini:latest")

        assert isinstance(adapter, OllamaChatAdapter)

    def test_provider_validation_is_case_insensitive(self):
        valid_providers = ["openai", "OPENAI", "OpenAI", "oPeNaI"]

        for provider_variant in valid_providers:
            with patch(
                "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key"
            ) as mock_get_api_key:
                with patch(
                    "arcadiumai.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client"
                ) as mock_get_client:
                    mock_get_api_key.return_value = "test-api-key"
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client

                    ChatAdapterFactory.clear_cache()

                    adapter = ChatAdapterFactory.create(
                        provider=provider_variant, model="gpt-5"
                    )

                    assert isinstance(adapter, OpenAIChatAdapter)

from unittest.mock import Mock, patch

import pytest

IA_OPENAI_TEST_1: str = "gpt-5-nano"
IA_OPENAI_TEST_2: str = "gpt-5-mini"
IA_OPENAI_TEST_3: str = "gpt-4-mini"


@pytest.mark.unit
class TestClientOpenAI:
    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_creates_client_with_api_key(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("test-api-key")

        assert client is mock_client
        mock_openai.assert_called_once_with(api_key="test-api-key")

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_returns_openai_instance(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("any-key")

        assert client is not None

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_with_different_keys(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        keys = ["key1", "key2", "sk-test-123"]

        for key in keys:
            ClientOpenAI.get_client(key)

        assert mock_openai.call_count == len(keys)

    def test_api_openai_name_constant(self):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert ClientOpenAI.API_OPENAI_NAME == "OPENAI_API_KEY"

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_is_static_method(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("test-key")

        assert client is not None

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_called_with_positional_and_keyword(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        ClientOpenAI.get_client("positional-key")
        ClientOpenAI.get_client(api_key="keyword-key")

        mock_openai.assert_any_call(api_key="positional-key")
        mock_openai.assert_any_call(api_key="keyword-key")

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_accepts_non_string_keys(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        key_obj = object()
        ClientOpenAI.get_client(key_obj)

        mock_openai.assert_called_with(api_key=key_obj)

    def test_api_openai_name_constant_type(self):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert isinstance(ClientOpenAI.API_OPENAI_NAME, str)
        assert ClientOpenAI.API_OPENAI_NAME != ""

    def test_get_client_callable_from_instance(self):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        attr = getattr(ClientOpenAI, "get_client")
        assert callable(attr)

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_handles_initialization_error(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_openai.side_effect = Exception("OpenAI initialization failed")

        with pytest.raises(Exception, match="OpenAI initialization failed"):
            ClientOpenAI.get_client("test-key")

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_with_empty_string_key(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client = Mock()
        mock_openai.return_value = mock_client

        client = ClientOpenAI.get_client("")
        assert client is mock_client
        mock_openai.assert_called_with(api_key="")

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_returns_different_clients_for_different_keys(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_openai.side_effect = [mock_client1, mock_client2]

        client1 = ClientOpenAI.get_client("key1")
        client2 = ClientOpenAI.get_client("key2")

        assert client1 is mock_client1
        assert client2 is mock_client2
        assert client1 is not client2

    def test_api_openai_name_is_uppercase(self):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        assert ClientOpenAI.API_OPENAI_NAME.isupper()

    @patch("createagents.infra.adapters.OpenAI.client_openai.OpenAI")
    def test_get_client_with_none_key_raises_error(self, mock_openai):
        from createagents.infra.adapters.OpenAI.client_openai import ClientOpenAI

        mock_openai.side_effect = TypeError("api_key cannot be None")

        with pytest.raises(TypeError):
            ClientOpenAI.get_client(None)

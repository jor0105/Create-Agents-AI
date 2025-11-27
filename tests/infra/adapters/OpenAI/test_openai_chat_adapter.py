from unittest.mock import MagicMock, Mock, patch

import pytest

from createagents.domain import ChatException
from createagents.infra import OpenAIChatAdapter

IA_OPENAI_TEST_1: str = 'gpt-5-mini'
IA_OPENAI_TEST_2: str = 'gpt-5-nano'


def _make_client_response(
    mock_get_client, output_text='', usage_attrs: dict | None = None
):
    mock_client = Mock()
    mock_response = MagicMock()
    mock_response.output_text = output_text
    if usage_attrs is not None:
        mock_usage = MagicMock()
        for k, v in usage_attrs.items():
            setattr(mock_usage, k, v)
        mock_response.usage = mock_usage
    else:
        mock_response.usage = None
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.tool_calls = None
    mock_client.responses.create.return_value = mock_response
    mock_get_client.return_value = mock_client
    return mock_client, mock_response


@pytest.mark.unit
class TestOpenAIChatAdapter:
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_initialization_success(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        assert adapter is not None
        mock_get_api_key.assert_called_once_with('OPENAI_API_KEY')
        mock_get_client.assert_called_once_with('test-api-key')

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    def test_initialization_with_missing_api_key_raises_error(
        self, mock_get_api_key
    ):
        mock_get_api_key.side_effect = EnvironmentError('API key not found')

        with pytest.raises(ChatException, match='Error configuring OpenAI'):
            OpenAIChatAdapter()

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_valid_input(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='OpenAI response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Be helpful',
            config={},
            tools=None,
            user_ask='Hello',
            history=[],
        )

        assert response == 'OpenAI response'
        mock_client.responses.create.assert_called_once()

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_constructs_messages_correctly(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='System instruction',
            config={},
            tools=None,
            user_ask='User question',
            history=[{'role': 'user', 'content': 'Previous message'}],
        )

        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']

        assert len(messages) == 3
        assert messages[0] == {
            'role': 'system',
            'content': 'System instruction',
        }
        assert messages[1] == {'role': 'user', 'content': 'Previous message'}
        assert messages[2] == {'role': 'user', 'content': 'User question'}

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_empty_history(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Instructions',
            config={},
            tools=None,
            user_ask='Question',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']

        assert len(messages) == 2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_multiple_history_items(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        history = [
            {'role': 'user', 'content': 'Msg 1'},
            {'role': 'assistant', 'content': 'Reply 1'},
            {'role': 'user', 'content': 'Msg 2'},
            {'role': 'assistant', 'content': 'Reply 2'},
        ]

        adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Instructions',
            config={},
            tools=None,
            user_ask='New question',
            history=history,
        )

        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']

        assert len(messages) == 6

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_passes_correct_model(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['model'] == IA_OPENAI_TEST_1

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_empty_response_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client, output_text='', usage_attrs=None
        )

        adapter = OpenAIChatAdapter()

        with pytest.raises(
            ChatException, match='OpenAI returned an empty response'
        ):
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_none_response_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client, output_text=None, usage_attrs=None
        )

        adapter = OpenAIChatAdapter()

        with pytest.raises(
            ChatException, match='OpenAI returned an empty response'
        ):
            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_missing_output_text_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()

        class BadResponse:
            @property
            def output_text(self):
                raise AttributeError(
                    "'Response' object has no attribute 'output_text'"
                )

            @property
            def usage(self):
                return Mock()

        mock_client.responses.create.return_value = BadResponse()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(
            ChatException, match='Error accessing OpenAI response'
        ):
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_attribute_error_raises_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_client.responses.create.side_effect = AttributeError(
            'Missing attribute'
        )
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(
            ChatException, match='Error accessing OpenAI response'
        ):
            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_index_error_raises_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_client.responses.create.side_effect = IndexError(
            'Index out of range'
        )
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException, match='unexpected format'):
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_generic_exception_raises_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_client.responses.create.side_effect = RuntimeError('API error')
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(
            ChatException, match='Error communicating with OpenAI'
        ):
            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_preserves_original_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        original_error = RuntimeError('Original error')
        mock_client = Mock()
        mock_client.responses.create.side_effect = original_error
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        try:
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )
        except ChatException as e:
            assert e.original_error is original_error

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_propagates_chat_exception(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        original_exception = ChatException('Original chat error')
        mock_client = Mock()
        mock_client.responses.create.side_effect = original_exception
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        with pytest.raises(ChatException) as exc_info:
            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

        assert exc_info.value is original_exception

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_special_characters(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Resposta com 你好 e emojis 🎉',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test 你好',
            config={},
            tools=None,
            user_ask='Question 🎉',
            history=[],
        )

        assert '你好' in response
        assert '🎉' in response

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_multiline_content(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Line 1\nLine 2\nLine 3',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Multi\nline\ninstructions',
            config={},
            tools=None,
            user_ask='Multi\nline\nquestion',
            history=[],
        )

        assert '\n' in response
        assert 'Line 1' in response

    def test_adapter_implements_chat_repository_interface(self):
        from createagents.application.interfaces.chat_repository import (
            ChatRepository,
        )

        with patch(
            'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
        ) as mock_get_api_key:
            with patch(
                'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
            ) as mock_get_client:
                mock_get_api_key.return_value = 'test-api-key'
                mock_client = Mock()
                mock_get_client.return_value = mock_client

                adapter = OpenAIChatAdapter()

                assert isinstance(adapter, ChatRepository)
                assert hasattr(adapter, 'chat')
                assert callable(adapter.chat)

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_collects_metrics_on_success(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Success response',
            usage_attrs={
                'total_tokens': 150,
                'prompt_tokens': 75,
                'completion_tokens': 75,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 150
        assert metrics[0].prompt_tokens == 75
        assert metrics[0].completion_tokens == 75
        assert metrics[0].latency_ms > 0

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_collects_metrics_on_failure(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_client.responses.create.side_effect = RuntimeError('Test error')
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        try:
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].model == IA_OPENAI_TEST_2
        assert metrics[0].success is False
        assert metrics[0].error_message is not None
        assert metrics[0].latency_ms > 0

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_collects_multiple_metrics(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test 1',
            history=[],
        )

        adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test 2',
            history=[],
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].model == IA_OPENAI_TEST_1
        assert metrics[1].model == IA_OPENAI_TEST_2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_get_metrics_returns_copy(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        metrics1 = adapter.get_metrics()
        metrics2 = adapter.get_metrics()

        assert metrics1 is not metrics2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_empty_string_in_history(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        history = [
            {'role': 'user', 'content': ''},
            {'role': 'assistant', 'content': 'Previous response'},
        ]

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='New question',
            history=history,
        )

        assert response == 'Response'
        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']
        assert len(messages) == 4

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_long_history(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        history = []
        for i in range(25):
            history.append({'role': 'user', 'content': f'Message {i}'})
            history.append({'role': 'assistant', 'content': f'Reply {i}'})

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Final question',
            history=history,
        )

        assert response == 'Response'
        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']
        assert len(messages) == 52

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_config_parameter(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        config = {'temperature': 0.7, 'max_tokens': 1000, 'top_p': 0.9}

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config=config,
            tools=None,
            history=[],
            user_ask='Test',
        )

        assert response == 'Response'

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_metrics_contain_error_message_on_empty_response(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client, output_text='', usage_attrs=None
        )

        adapter = OpenAIChatAdapter()

        try:
            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )
        except ChatException:
            pass

        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].error_message == 'OpenAI chat error'
        assert metrics[0].success is False

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_missing_usage_info(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client, output_text='Response', usage_attrs=None
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        assert response == 'Response'
        metrics = adapter.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].tokens_used is None
        assert metrics[0].prompt_tokens is None
        assert metrics[0].completion_tokens is None

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_env'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_initialization_loads_environment_configs(
        self, mock_get_client, mock_get_env, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'
        mock_get_env.side_effect = lambda key, default: {
            'OPENAI_TIMEOUT': '60',
            'OPENAI_MAX_RETRIES': '5',
        }.get(key, default)
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        assert adapter is not None
        assert mock_get_env.call_count >= 2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_whitespace_only_response_raises_error(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client, output_text='   \n\t  ', usage_attrs=None
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        assert response == '   \n\t  '

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_updates_metrics_list_correctly(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test 1',
            history=[],
        )

        mock_client.responses.create.side_effect = RuntimeError('Error')
        try:
            adapter.chat(
                model=IA_OPENAI_TEST_2,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test 2',
                history=[],
            )
        except ChatException:
            pass

        mock_client.responses.create.side_effect = None
        mock_client.responses.create.return_value = mock_response
        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test 3',
            history=[],
        )

        metrics = adapter.get_metrics()
        assert len(metrics) == 3
        assert metrics[0].success is True
        assert metrics[1].success is False
        assert metrics[2].success is True

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_very_long_content(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        long_text = 'A' * 10000
        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text=long_text,
            usage_attrs={
                'total_tokens': 2500,
                'input_tokens': 500,
                'output_tokens': 2000,
            },
        )

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        assert len(response) == 10000
        assert response == long_text

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_passes_temperature_config(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={'temperature': 0.7},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert 'temperature' in call_args.kwargs
        assert call_args.kwargs['temperature'] == 0.7

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_passes_max_tokens_config(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config={'max_tokens': 500},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert 'max_output_tokens' in call_args.kwargs
        assert call_args.kwargs['max_output_tokens'] == 500

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_passes_top_p_config(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={'top_p': 0.9},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert 'top_p' in call_args.kwargs
        assert call_args.kwargs['top_p'] == 0.9

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_passes_all_configs(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        config = {
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.9,
        }

        adapter.chat(
            model=IA_OPENAI_TEST_2,
            instructions='Test',
            config=config,
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs['temperature'] == 0.7
        assert call_args.kwargs['max_output_tokens'] == 500
        assert call_args.kwargs['top_p'] == 0.9

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_empty_config_does_not_pass_extra_params(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        assert 'temperature' not in call_args.kwargs
        assert 'max_output_tokens' not in call_args.kwargs
        assert 'top_p' not in call_args.kwargs
        assert 'model' in call_args.kwargs
        assert 'input' in call_args.kwargs

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_logs_debug_messages(self, mock_get_client, mock_get_api_key):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='A' * 200,
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        with patch(
            'createagents.infra.adapters.OpenAI.openai_chat_adapter.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            adapter = OpenAIChatAdapter()

            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

            assert mock_log.debug.call_count >= 2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_logs_info_on_success(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        with patch(
            'createagents.infra.adapters.OpenAI.openai_chat_adapter.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            adapter = OpenAIChatAdapter()

            adapter.chat(
                model=IA_OPENAI_TEST_1,
                instructions='Test',
                config={},
                tools=None,
                user_ask='Test',
                history=[],
            )

            assert mock_log.info.call_count >= 2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_logs_error_on_failure(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_client.responses.create.side_effect = RuntimeError('API Error')
        mock_get_client.return_value = mock_client

        with patch(
            'createagents.infra.adapters.OpenAI.openai_chat_adapter.LoggingConfig.get_logger'
        ) as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            adapter = OpenAIChatAdapter()

            try:
                adapter.chat(
                    model=IA_OPENAI_TEST_1,
                    instructions='Test',
                    config={},
                    tools=None,
                    user_ask='Test',
                    history=[],
                )
            except ChatException:
                pass

            assert mock_log.error.call_count >= 1

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_none_instructions_omits_system_message(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions=None,
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']

        assert len(messages) == 1
        assert messages[0] == {'role': 'user', 'content': 'Test'}

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_chat_with_whitespace_only_instructions(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client, mock_response = _make_client_response(
            mock_get_client,
            output_text='Response',
            usage_attrs={
                'total_tokens': 100,
                'input_tokens': 50,
                'output_tokens': 50,
            },
        )

        adapter = OpenAIChatAdapter()

        adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='   \n\t  ',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs['input']

        assert len(messages) == 1
        assert messages[0]['role'] == 'user'

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_env'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_initialization_uses_custom_timeout(
        self, mock_get_client, mock_get_env, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'
        mock_get_env.side_effect = lambda key, default: {
            'OPENAI_TIMEOUT': '60',
            'OPENAI_MAX_RETRIES': '3',
        }.get(key, default)
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        OpenAIChatAdapter()

        assert mock_get_env.call_count >= 2

    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.EnvironmentConfig.get_api_key'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_chat_adapter.ClientOpenAI.get_client'
    )
    def test_retry_decorator_is_applied(
        self, mock_get_client, mock_get_api_key
    ):
        mock_get_api_key.return_value = 'test-api-key'

        mock_client = Mock()
        mock_response = MagicMock()
        mock_response.output_text = 'Response'
        mock_response.usage.total_tokens = 100
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 50
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = None

        mock_client.responses.create.side_effect = [
            Exception('Error 1'),
            Exception('Error 2'),
            mock_response,
        ]
        mock_get_client.return_value = mock_client

        adapter = OpenAIChatAdapter()

        response = adapter.chat(
            model=IA_OPENAI_TEST_1,
            instructions='Test',
            config={},
            tools=None,
            user_ask='Test',
            history=[],
        )

        assert response == 'Response'
        assert mock_client.responses.create.call_count == 3

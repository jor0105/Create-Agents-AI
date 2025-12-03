from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from createagents.domain import ChatException
from createagents.infra.adapters.OpenAI.openai_stream_handler import (
    OpenAIStreamHandler,
)

IA_OPENAI_TEST_1: str = 'gpt-5-nano'


class FakeStream:
    def __init__(self, events):
        self._events = list(events)
        self._iterator = None

    def __aiter__(self):
        self._iterator = iter(self._events)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


@pytest.mark.unit
class TestOpenAIStreamHandler:
    def setup_method(self):
        self.mock_client = Mock()
        self.mock_client.call_api = AsyncMock()
        self.handler = OpenAIStreamHandler(self.mock_client)

    @pytest.mark.asyncio
    async def test_handle_stream_success(self):
        event1 = MagicMock()
        event1.type = 'response.output_text.delta'
        event1.delta = 'Hello'

        event2 = MagicMock()
        event2.type = 'response.output_text.delta'
        event2.delta = ' World'

        completed_response = SimpleNamespace(
            usage=SimpleNamespace(input_tokens=1, output_tokens=2)
        )
        event3 = MagicMock()
        event3.type = 'response.completed'
        event3.response = completed_response

        self.mock_client.call_api.return_value = FakeStream(
            [
                event1,
                event2,
                event3,
            ]
        )

        generator = self.handler.handle_stream(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config={'stream': True},
            tools=None,
        )

        tokens = []
        async for token in generator:
            tokens.append(token)

        assert tokens == ['Hello', ' World']
        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].tokens_used == 3

    @pytest.mark.asyncio
    @patch(
        'createagents.infra.adapters.OpenAI.openai_stream_handler.OpenAIToolCallParser'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_stream_handler.ToolExecutor'
    )
    @patch(
        'createagents.infra.adapters.OpenAI.openai_stream_handler.OpenAIToolSchemaFormatter'
    )
    async def test_handle_stream_executes_tool_calls(
        self,
        mock_formatter,
        mock_executor_cls,
        mock_parser,
    ):
        mock_formatter.format_tools_for_responses_api.return_value = [
            {'name': 'dummy'}
        ]
        mock_parser.has_tool_calls.side_effect = [True, False]
        mock_parser.get_assistant_message_with_tool_calls.return_value = []
        mock_parser.extract_tool_calls.return_value = [
            {'name': 'dummy', 'arguments': {'value': 1}, 'id': 'call_1'}
        ]
        mock_parser.format_tool_results_for_llm.return_value = {
            'role': 'tool',
            'content': 'ok',
        }

        executor_instance = Mock()
        executor_instance.execute_tool = AsyncMock(
            return_value=SimpleNamespace(success=True, result='done')
        )
        mock_executor_cls.return_value = executor_instance

        response_with_tool = SimpleNamespace(usage=None)
        event_with_tool = MagicMock()
        event_with_tool.type = 'response.completed'
        event_with_tool.response = response_with_tool

        final_response = SimpleNamespace(
            usage=SimpleNamespace(input_tokens=2, output_tokens=3)
        )
        final_events = [
            MagicMock(type='response.output_text.delta', delta='Answer'),
            MagicMock(type='response.completed', response=final_response),
        ]

        self.mock_client.call_api.side_effect = [
            FakeStream([event_with_tool]),
            FakeStream(final_events),
        ]

        tools = [SimpleNamespace(name='dummy_tool')]
        generator = self.handler.handle_stream(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config={'stream': True},
            tools=tools,
        )

        collected = []
        async for token in generator:
            collected.append(token)

        assert ''.join(collected) == 'Answer'
        executor_instance.execute_tool.assert_awaited_once_with(
            'dummy', value=1
        )
        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].completion_tokens == 3

    @pytest.mark.asyncio
    async def test_handle_stream_api_error(self):
        self.mock_client.call_api.side_effect = RuntimeError('Stream Error')

        generator = self.handler.handle_stream(
            model=IA_OPENAI_TEST_1,
            instructions='Instr',
            messages=[{'role': 'user', 'content': 'Hi'}],
            config={'stream': True},
            tools=None,
        )

        with pytest.raises(
            ChatException, match='Error during OpenAI streaming'
        ):
            async for _ in generator:
                pass

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is False
        assert 'Stream Error' in metrics[0].error_message

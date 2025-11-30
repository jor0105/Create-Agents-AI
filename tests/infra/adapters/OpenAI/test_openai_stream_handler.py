from unittest.mock import MagicMock, Mock

import pytest

from createagents.domain import ChatException
from createagents.infra.adapters.OpenAI.openai_stream_handler import (
    OpenAIStreamHandler,
)

IA_OPENAI_TEST_1: str = 'gpt-5-nano'


@pytest.mark.unit
class TestOpenAIStreamHandler:
    def setup_method(self):
        self.mock_client = Mock()
        self.handler = OpenAIStreamHandler(self.mock_client)

    def test_handle_stream_success(self):
        # Mock streaming events
        event1 = MagicMock()
        event1.type = 'response.output_text.delta'
        event1.delta = 'Hello'

        event2 = MagicMock()
        event2.type = 'response.output_text.delta'
        event2.delta = ' World'

        self.mock_client.call_api.return_value = [event1, event2]

        generator = self.handler.handle_stream(
            model=IA_OPENAI_TEST_1,
            messages=[],
            config={'stream': True},
            tools=None,
        )

        tokens = list(generator)
        assert tokens == ['Hello', ' World']

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].latency_ms > 0

    def test_handle_stream_with_tools_raises_error(self):
        tools = [Mock()]

        with pytest.raises(
            ChatException,
            match='Streaming mode is not supported with tool calling',
        ):
            list(
                self.handler.handle_stream(
                    model=IA_OPENAI_TEST_1,
                    messages=[],
                    config={'stream': True},
                    tools=tools,
                )
            )

    def test_handle_stream_api_error(self):
        self.mock_client.call_api.side_effect = RuntimeError('Stream Error')

        generator = self.handler.handle_stream(
            model=IA_OPENAI_TEST_1,
            messages=[],
            config={'stream': True},
            tools=None,
        )

        with pytest.raises(
            ChatException, match='Error during OpenAI streaming'
        ):
            list(generator)

        metrics = self.handler.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is False
        assert 'Stream Error' in metrics[0].error_message

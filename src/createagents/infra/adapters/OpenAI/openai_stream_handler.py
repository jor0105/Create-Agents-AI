import time
from typing import Any, Dict, AsyncGenerator, List, Optional

from ....domain import BaseTool, ChatException
from ...config import ChatMetrics, LoggingConfig
from .openai_client import OpenAIClient


class OpenAIStreamHandler:
    """Handles streaming responses from OpenAI."""

    def __init__(
        self,
        client: OpenAIClient,
        metrics_list: Optional[List[ChatMetrics]] = None,
    ):
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics = metrics_list if metrics_list is not None else []

    async def handle_stream(
        self,
        model: str,
        instructions: Optional[str],
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the OpenAI API as they arrive."""
        start_time = time.time()

        # Streaming mode is not compatible with tool calling
        if tools:
            raise ChatException(
                'Streaming mode is not supported with tool calling. '
                'Please use either stream=True OR tools, not both.'
            )

        self.__logger.debug('Streaming mode enabled for OpenAI')

        try:
            # Call OpenAI API with streaming enabled
            stream_response = await self.__client.call_api(
                model, instructions, messages, config, tools
            )

            self.__logger.debug(
                'Streaming response received, iterating events'
            )

            # OpenAI Responses API returns structured EVENTS
            # Key event: ResponseTextDeltaEvent with type='response.output_text.delta'
            # The event.delta IS the token string itself (not an object)
            async for event in stream_response:
                # Check event type attribute
                event_type = getattr(event, 'type', None)

                # The main streaming event is 'response.output_text.delta'
                # event.delta contains the incremental text directly as a string
                if event_type == 'response.output_text.delta':
                    if hasattr(event, 'delta'):
                        token = event.delta  # Delta IS the string token
                        if token:
                            yield token

                # Also handle content_part.added events if they exist
                elif event_type == 'response.content_part.added':
                    if hasattr(event, 'content_part'):
                        content_part = event.content_part
                        if hasattr(content_part, 'text'):
                            token = content_part.text
                            if token:
                                yield token

            # Record metrics after streaming completes
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                tokens_used=None,  # Token count not available in streaming
                prompt_tokens=None,
                completion_tokens=None,
                success=True,
            )
            self.__metrics.append(metrics)
            self.__logger.info('Streaming chat completed: %s', metrics)

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=str(e),
            )
            self.__metrics.append(metrics)
            self.__logger.error('Error during streaming: %s', e)
            raise ChatException(
                f'Error during OpenAI streaming: {str(e)}',
                original_error=e,
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """Returns the list of collected metrics."""
        return self.__metrics.copy()

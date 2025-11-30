from typing import Any, Dict, Generator, List, Optional, Union

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException
from ...config import ChatMetrics, LoggingConfig
from .openai_client import OpenAIClient
from .openai_handler import OpenAIHandler
from .openai_stream_handler import OpenAIStreamHandler


class OpenAIChatAdapter(ChatRepository):
    """Initialize the OpenAI adapter."""

    def __init__(self):
        """Initialize the OpenAI adapter.

        Raises:
            ChatException: If the API key is missing or invalid.
        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__client = OpenAIClient()

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Sends a message to OpenAI and returns the response.

        Implements tool calling loop:
        1. Send message to LLM
        2. If LLM requests tool calls, execute them
        3. Send tool results back to LLM
        4. Repeat until LLM provides final response

        Streaming mode (config={'stream': True}):
        - Returns a Generator that yields tokens as they arrive

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI configuration (supports 'stream': True/False).
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools available to the agent.

        Returns:
            Union[str, Generator[str, None, None]]:
                - str: Complete response (if stream=False or not specified)
                - Generator[str, None, None]: Token stream (if stream=True)

        Raises:
            ChatException: If a communication error occurs or if streaming
                is used with tool calling.
        """
        try:
            self.__logger.debug(
                'Starting chat with model %s on OpenAI.', model
            )

            messages = []
            if instructions and instructions.strip():
                messages.append({'role': 'system', 'content': instructions})
            messages.extend(history)
            messages.append({'role': 'user', 'content': user_ask})

            # Check if streaming mode is enabled
            if config and config.get('stream'):
                stream_handler = OpenAIStreamHandler(
                    self.__client, self.__metrics
                )
                result_stream = stream_handler.handle_stream(
                    model, messages, config, tools
                )

                return result_stream
            handler = OpenAIHandler(self.__client, self.__metrics)
            result = handler.execute_tool_loop(model, messages, config, tools)

            return result

        except ChatException:
            raise
        except Exception as e:
            self.__logger.error(
                'An error occurred while communicating with OpenAI: %s', e
            )
            raise ChatException(
                f'An error occurred while communicating with OpenAI: {str(e)}',
                original_error=e,
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics.

        Returns:
            List[ChatMetrics]: The list of metrics.
        """
        return self.__metrics.copy()

from typing import Any, Dict, AsyncGenerator, List, Optional, Union

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException
from ....domain.interfaces import LoggerInterface
from ...config import ChatMetrics, create_logger
from ..Common import MetricsRecorder, ToolPayloadBuilder
from .openai_client import OpenAIClient
from .openai_handler import OpenAIHandler
from .openai_stream_handler import OpenAIStreamHandler


class OpenAIChatAdapter(ChatRepository):
    """Adapter for communicating with OpenAI.

    This adapter follows Clean Architecture and SOLID principles:
    - Implements the ChatRepository interface (DIP)
    - Creates dependencies internally but injects them into handlers
    - All dependencies are abstracted behind interfaces

    Design:
    - Adapter pattern: Adapts OpenAI SDK to domain interface
    - Factory method: Creates handlers with proper dependencies
    """

    def __init__(
        self,
        logger: Optional[LoggerInterface] = None,
    ):
        """Initialize the OpenAI adapter.

        Args:
            logger: Optional logger instance. If None, creates from config.

        Raises:
            ChatException: If the API key is missing or invalid.
        """
        self.__logger = logger or create_logger(__name__)
        self.__metrics: List[ChatMetrics] = []
        self.__client = OpenAIClient(logger=self.__logger)
        self.__schema_builder = ToolPayloadBuilder(
            logger=self.__logger, format_style='openai'
        )
        self.__logger.info('OpenAI adapter initialized')

    async def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
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
            history: The conversation history including user message.
            tools: Optional list of tools available to the agent.
            tool_choice: Optional tool choice configuration. Can be:
                - "auto": Let the model decide
                - "none": Don't call any tool
                - "required": Force at least one tool call
                - {"type": "function", "function": {"name": "tool_name"}}

        Returns:
            Union[str, AsyncGenerator[str, None]]:
                - str: Complete response (if stream=False or not specified)
                - AsyncGenerator[str, None]: Token stream (if stream=True)

        Raises:
            ChatException: If a communication error occurs or if streaming
                is used with tool calling.
        """
        try:
            self.__logger.debug(
                'Starting chat with model %s on OpenAI.', model
            )

            # Check if streaming mode is enabled
            if config.get('stream'):
                stream_handler = self.__create_stream_handler()
                result_stream = stream_handler.handle_stream(
                    model, instructions, history, config, tools, tool_choice
                )

                return result_stream

            handler = self.__create_handler()
            result = await handler.execute_tool_loop(
                model, instructions, history, config, tools, tool_choice
            )

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

    def __create_handler(self) -> OpenAIHandler:
        """Create an OpenAI handler with injected dependencies.

        Returns:
            Configured OpenAIHandler instance.
        """
        metrics_recorder = MetricsRecorder(
            logger=self.__logger,
            metrics_list=self.__metrics,
        )
        return OpenAIHandler(
            client=self.__client,
            logger=self.__logger,
            metrics_recorder=metrics_recorder,
            schema_builder=self.__schema_builder,
        )

    def __create_stream_handler(self) -> OpenAIStreamHandler:
        """Create an OpenAI stream handler with injected dependencies.

        Returns:
            Configured OpenAIStreamHandler instance.
        """
        metrics_recorder = MetricsRecorder(
            logger=self.__logger,
            metrics_list=self.__metrics,
        )
        return OpenAIStreamHandler(
            client=self.__client,
            logger=self.__logger,
            metrics_recorder=metrics_recorder,
            schema_builder=self.__schema_builder,
        )

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics.

        Returns:
            List[ChatMetrics]: The list of metrics.
        """
        return self.__metrics.copy()

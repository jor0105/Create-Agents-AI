from typing import Any, Dict, AsyncGenerator, List, Optional, Union

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException, TraceContext
from ....domain.interfaces import ITraceLogger, LoggerInterface
from ...config import ChatMetrics, create_logger
from ..Common import MetricsRecorder, ToolPayloadBuilder
from .ollama_client import OllamaClient
from .ollama_handler import OllamaHandler
from .ollama_stream_handler import OllamaStreamHandler


class OllamaChatAdapter(ChatRepository):
    """An adapter for communicating with Ollama.

    This adapter follows Clean Architecture and SOLID principles:
    - Implements the ChatRepository interface (DIP)
    - Creates dependencies internally but injects them into handlers
    - All dependencies are abstracted behind interfaces

    Design:
    - Adapter pattern: Adapts Ollama SDK to domain interface
    - Factory method: Creates handlers with proper dependencies

    Tool calling flow:
    1. Send tools schema to Ollama API
    2. Model decides whether to call tools based on the query
    3. If tool calls are detected, execute them
    4. Send tool results back to model
    5. Model generates final response
    """

    def __init__(
        self,
        logger: Optional[LoggerInterface] = None,
        trace_logger: Optional[ITraceLogger] = None,
    ):
        """Initialize the Ollama adapter.

        Args:
            logger: Optional logger instance. If None, creates from config.
            trace_logger: Optional trace logger for persistent tracing.
        """
        self.__logger = logger or create_logger(__name__)
        self.__trace_logger = trace_logger
        self.__metrics: List[ChatMetrics] = []
        self.__client = OllamaClient(logger=self.__logger)
        self.__schema_builder = ToolPayloadBuilder(
            logger=self.__logger, format_style='ollama'
        )

        self.__logger.info('Ollama adapter initialized')

    async def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Sends a message to Ollama and returns the response.

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI settings (supports 'stream': True/False).
            history: The conversation history including user message.
            tools: Optional list of tools (native Ollama API).
            tool_choice: Optional tool choice configuration. Can be:
                - "auto": Let the model decide (default)
                - "none": Don't call any tool
                - "required": Force at least one tool call
                - {"type": "function", "function": {"name": "tool_name"}}
            trace_context: Optional trace context for distributed tracing.

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
                'Starting chat with model %s on Ollama.', model
            )

            # Prepare messages with system instructions if provided
            messages = []
            if instructions and instructions.strip():
                messages.append({'role': 'system', 'content': instructions})
            messages.extend(history)

            # Check if streaming mode is enabled
            if config.get('stream'):
                stream_handler = self.__create_stream_handler()
                self.__logger.debug('Streaming mode enabled for Ollama')
                result_stream = stream_handler.handle_stream(
                    model, messages, config, tools, tool_choice, trace_context
                )
                return result_stream

            # Non-streaming mode - Tool calling loop
            handler = self.__create_handler()
            result: str = await handler.execute_tool_loop(
                model, messages, config, tools, tool_choice, trace_context
            )
            return result

        except ChatException:
            raise
        except Exception as e:
            self.__logger.error(
                'An error occurred while communicating with Ollama: %s', e
            )
            raise ChatException(
                f'An error occurred while communicating with Ollama: {str(e)}',
                original_error=e,
            ) from e

    def __create_handler(self) -> OllamaHandler:
        """Create an Ollama handler with injected dependencies.

        Returns:
            Configured OllamaHandler instance.
        """
        metrics_recorder = MetricsRecorder(
            logger=self.__logger,
            metrics_list=self.__metrics,
        )
        return OllamaHandler(
            client=self.__client,
            logger=self.__logger,
            metrics_recorder=metrics_recorder,
            schema_builder=self.__schema_builder,
            trace_logger=self.__trace_logger,
        )

    def __create_stream_handler(self) -> OllamaStreamHandler:
        """Create an Ollama stream handler with injected dependencies.

        Returns:
            Configured OllamaStreamHandler instance.
        """
        metrics_recorder = MetricsRecorder(
            logger=self.__logger,
            metrics_list=self.__metrics,
        )
        return OllamaStreamHandler(
            client=self.__client,
            logger=self.__logger,
            metrics_recorder=metrics_recorder,
            schema_builder=self.__schema_builder,
            trace_logger=self.__trace_logger,
        )

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics.

        Returns:
            List[ChatMetrics]: The list of metrics.
        """
        return self.__metrics.copy()

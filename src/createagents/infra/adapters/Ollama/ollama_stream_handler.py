import time
from typing import Any, Dict, Generator, List, Optional

from ....domain import ChatException, BaseTool
from ...config import ChatMetrics, LoggingConfig
from .ollama_client import OllamaClient


class OllamaStreamHandler:
    """Handles streaming responses from Ollama."""

    def __init__(
        self,
        client: OllamaClient,
        metrics_list: Optional[List[ChatMetrics]] = None,
    ):
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics = metrics_list if metrics_list is not None else []

    def handle_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> Generator[str, None, None]:
        """Yields tokens from the Ollama API as they arrive."""
        start_time = time.time()
        try:
            stream_response = self.__client.call_api(
                model, messages, config, tools
            )

            for chunk in stream_response:
                if hasattr(chunk, 'message') and hasattr(
                    chunk.message, 'content'
                ):
                    token = chunk.message.content
                    if token:
                        yield token

            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                tokens_used=None,
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
                f'Error during Ollama streaming: {str(e)}', original_error=e
            ) from e
        finally:
            self.__client.stop_model(model)

    def get_metrics(self) -> List[ChatMetrics]:
        """Returns the list of collected metrics."""
        return self.__metrics.copy()

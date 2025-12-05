import asyncio
import asyncio.subprocess as async_subprocess
import threading
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from httpx import TimeoutException
from ollama import AsyncClient, ChatResponse, ResponseError

from ....domain import APITimeoutError, RateLimitError, ToolChoiceType
from ....domain.interfaces import IRateLimiter, LoggerInterface
from ...config import (
    EnvironmentConfig,
    RateLimiterFactory,
    create_logger,
    retry_with_backoff,
)


class OllamaClient:
    """
    Handles direct communication with the Ollama API.

    Features:
    - Singleton AsyncClient for connection reuse (performance)
    - Rate limiting via semaphore
    - Configurable timeout
    - Automatic retry with backoff
    - Proper error conversion for RateLimitError
    """

    _client: Optional[AsyncClient] = None
    _client_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        logger: Optional[LoggerInterface] = None,
        rate_limiter: Optional[IRateLimiter] = None,
    ):
        """
        Initialize the Ollama client.

        Args:
            logger: Optional logger instance. If None, creates from config.
            rate_limiter: Optional rate limiter. If None, uses factory singleton.
        """
        self.__logger = logger or create_logger(__name__)
        self.__host = EnvironmentConfig.get_env(
            'OLLAMA_HOST', 'http://localhost:11434'
        )
        self.__timeout = int(
            EnvironmentConfig.get_env('OLLAMA_TIMEOUT', '300') or '300'
        )
        self.__max_retries = int(
            EnvironmentConfig.get_env('OLLAMA_MAX_RETRIES', '3') or '3'
        )
        # Control whether to stop model after each request
        # Enable to free VRAM after each request (recommended for local models)
        # Disable for remote/cloud models or when you want to keep model loaded
        self.__auto_stop_model = (
            EnvironmentConfig.get_env('OLLAMA_AUTO_STOP_MODEL', 'true')
            or 'true'
        ).lower() == 'true'

        self.__rate_limiter = (
            rate_limiter
            or RateLimiterFactory.get_instance().get_limiter('ollama')
        )

        self.__logger.info(
            'Ollama client initialized (host: %s, timeout: %ss, auto_stop: %s)',
            self.__host,
            self.__timeout,
            self.__auto_stop_model,
        )

    def _get_client(self) -> AsyncClient:
        """
        Get or create the singleton AsyncClient.

        Uses double-checked locking for thread-safety.

        Returns:
            The singleton AsyncClient instance.
        """
        if OllamaClient._client is None:
            with OllamaClient._client_lock:
                if OllamaClient._client is None:
                    OllamaClient._client = AsyncClient(
                        host=self.__host,
                        timeout=float(self.__timeout),
                    )
                    self.__logger.debug(
                        'Created singleton Ollama AsyncClient (host: %s)',
                        self.__host,
                    )
        return OllamaClient._client

    @classmethod
    def reset_client(cls) -> None:
        """Reset the singleton client (mainly for testing or reconnection)."""
        with cls._client_lock:
            cls._client = None

    @retry_with_backoff(exceptions=(Exception,))
    async def call_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[ToolChoiceType] = None,
    ) -> Union[ChatResponse, AsyncIterator[ChatResponse]]:
        """
        Calls the Ollama API with rate limiting and automatic retries.

        Args:
            model: The name of the model to use.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tool schemas.
            tool_choice: Optional tool choice configuration.

        Returns:
            ChatResponse or AsyncIterator[ChatResponse] if streaming.

        Raises:
            RateLimitError: When rate limit is hit (for smart retry).
            APITimeoutError: When request times out.
        """
        async with self.__rate_limiter:
            try:
                chat_kwargs: Dict[str, Any] = {
                    'model': model,
                    'messages': messages,
                    'stream': config.get('stream', False) if config else False,
                }

                if tools:
                    chat_kwargs['tools'] = tools
                    if tool_choice:
                        self.__logger.debug(
                            'Tool choice requested: %s (Ollama may have limited support)',
                            tool_choice,
                        )

                if config:
                    config_copy = config.copy()
                    if 'stream' in config_copy:
                        config_copy.pop('stream')
                    if 'think' in config_copy:
                        chat_kwargs['think'] = config_copy.pop('think')
                    if 'max_tokens' in config_copy:
                        config_copy['num_predict'] = config_copy.pop(
                            'max_tokens'
                        )
                    if config_copy:
                        chat_kwargs['options'] = config_copy

                client = self._get_client()
                result: Union[
                    ChatResponse, AsyncIterator[ChatResponse]
                ] = await client.chat(**chat_kwargs)
                return result

            except ResponseError as e:
                if '429' in str(e) or 'rate' in str(e).lower():
                    self.__logger.warning('Ollama rate limit hit: %s', e)
                    raise RateLimitError(
                        message=f'Ollama rate limit exceeded: {str(e)}',
                        retry_after=30.0,
                        provider='ollama',
                        original_error=e,
                    ) from e
                self.__logger.error(
                    "Error calling Ollama API for model '%s': %s", model, e
                )
                raise

            except TimeoutException as e:
                self.__logger.error(
                    'Ollama request timed out after %s seconds', self.__timeout
                )
                raise APITimeoutError(
                    message=f'Ollama request timed out after {self.__timeout}s',
                    timeout_seconds=float(self.__timeout),
                    provider='ollama',
                    original_error=e,
                ) from e

            except asyncio.TimeoutError as e:
                self.__logger.error(
                    'Async timeout after %s seconds', self.__timeout
                )
                raise APITimeoutError(
                    message=f'Request timed out after {self.__timeout}s',
                    timeout_seconds=float(self.__timeout),
                    provider='ollama',
                    original_error=e,
                ) from e

            except Exception as e:
                self.__logger.error(
                    "Error calling Ollama API for model '%s': %s", model, e
                )
                raise

    async def stop_model(self, model: str) -> None:
        """Stops the Ollama model after use to free up VRAM.

        This method is controlled by the OLLAMA_AUTO_STOP_MODEL environment
        variable (default: false). It should be enabled for local models
        to free up GPU memory, but disabled for remote/cloud models.

        Args:
            model: The model name to stop.
        """
        if not self.__auto_stop_model:
            self.__logger.debug(
                'Auto-stop disabled, skipping stop for model %s', model
            )
            return

        try:
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    'ollama',
                    'stop',
                    model,
                    stdout=async_subprocess.PIPE,
                    stderr=async_subprocess.PIPE,
                ),
                timeout=10.0,
            )
            await process.wait()
            self.__logger.debug('Model %s stopped successfully.', model)
        except FileNotFoundError:
            self.__logger.debug(
                'Ollama CLI not found, cannot stop model %s', model
            )
        except asyncio.TimeoutError:
            self.__logger.warning(
                'Timeout stopping model %s (10s exceeded)', model
            )
        except OSError as e:
            self.__logger.warning('Could not stop model %s: %s', model, e)
        except Exception as e:
            self.__logger.warning(
                'Error trying to stop model %s: %s', model, e
            )

import asyncio
from typing import Any, Dict, List, Optional

from openai import APITimeoutError as OpenAITimeoutError
from openai import RateLimitError as OpenAIRateLimitError

from ....domain import (
    APITimeoutError,
    ChatException,
    RateLimitError,
    ToolChoiceType,
)
from ....domain.interfaces import IRateLimiter, LoggerInterface
from ...config import (
    EnvironmentConfig,
    RateLimiterFactory,
    create_logger,
    retry_with_backoff,
)
from .client_openai import ClientOpenAI


class OpenAIClient:
    """
    Handles direct communication with the OpenAI API.

    Features:
    - Rate limiting via semaphore (prevents 429 errors)
    - Configurable timeout
    - Automatic retry with backoff
    - Proper error conversion for RateLimitError
    """

    def __init__(
        self,
        logger: Optional[LoggerInterface] = None,
        rate_limiter: Optional[IRateLimiter] = None,
    ):
        """
        Initialize the OpenAI client.

        Args:
            logger: Optional logger instance. If None, creates from config.
            rate_limiter: Optional rate limiter. If None, uses factory singleton.

        Raises:
            ChatException: If the API key is missing or invalid.
        """
        self.__logger = logger or create_logger(__name__)
        self.__timeout = int(
            EnvironmentConfig.get_env('OPENAI_TIMEOUT') or '60'
        )
        self.__max_retries = int(
            EnvironmentConfig.get_env('OPENAI_MAX_RETRIES') or '3'
        )

        self.__rate_limiter = (
            rate_limiter
            or RateLimiterFactory.get_instance().get_limiter('openai')
        )

        try:
            api_key = EnvironmentConfig.get_api_key(
                ClientOpenAI.API_OPENAI_NAME
            )
            self.__client = ClientOpenAI.get_client(api_key, self.__timeout)
            self.__logger.info(
                'OpenAI client initialized (timeout: %ss, max_retries: %s)',
                self.__timeout,
                self.__max_retries,
            )
        except EnvironmentError as e:
            self.__logger.error('Error configuring OpenAI: %s', e)
            raise ChatException(
                f'Error configuring OpenAI: {str(e)}', e
            ) from e

    @retry_with_backoff(exceptions=(Exception,))
    async def call_api(
        self,
        model: str,
        instructions: Optional[str],
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[ToolChoiceType] = None,
    ) -> Any:
        """
        Calls the OpenAI API with rate limiting and automatic retries.

        Args:
            model: The name of the model.
            instructions: System instructions for the model.
            messages: A list of messages.
            config: Internal AI configuration.
            tools: Optional list of tool schemas for function calling.
            tool_choice: Optional tool choice configuration.

        Returns:
            The API response.

        Raises:
            RateLimitError: When rate limit is hit (for smart retry).
            APITimeoutError: When request times out.
            ChatException: For other API errors.
        """
        async with self.__rate_limiter:
            try:
                chat_kwargs: Dict[str, Any] = {
                    'model': model,
                    'instructions': instructions,
                    'input': messages,
                }

                if tools:
                    chat_kwargs['tools'] = tools
                    if tool_choice:
                        chat_kwargs['tool_choice'] = tool_choice

                if config:
                    config_copy = config.copy()

                    if 'stream' in config_copy:
                        chat_kwargs['stream'] = config_copy.pop('stream')

                    param_to_change: Dict[str, str] = {
                        'reasoning': 'think',
                        'max_output_tokens': 'max_tokens',
                    }

                    for api_key, config_key in param_to_change.items():
                        if config_key in config_copy:
                            config_copy[api_key] = config_copy.pop(config_key)

                    for key, config_data in config_copy.items():
                        if key == 'reasoning':
                            chat_kwargs['reasoning'] = {'effort': config_data}
                        else:
                            chat_kwargs[key] = config_data

                response_api = await self.__client.responses.create(
                    **chat_kwargs
                )
                return response_api

            except OpenAIRateLimitError as e:
                retry_after = self._extract_retry_after(e)
                self.__logger.warning(
                    'OpenAI rate limit hit. Retry-After: %s seconds',
                    retry_after,
                )
                raise RateLimitError(
                    message=f'OpenAI rate limit exceeded: {str(e)}',
                    retry_after=retry_after,
                    provider='openai',
                    original_error=e,
                ) from e

            except OpenAITimeoutError as e:
                self.__logger.error(
                    'OpenAI request timed out after %s seconds', self.__timeout
                )
                raise APITimeoutError(
                    message=f'OpenAI request timed out after {self.__timeout}s',
                    timeout_seconds=float(self.__timeout),
                    provider='openai',
                    original_error=e,
                ) from e

            except asyncio.TimeoutError as e:
                self.__logger.error(
                    'Async timeout after %s seconds', self.__timeout
                )
                raise APITimeoutError(
                    message=f'Request timed out after {self.__timeout}s',
                    timeout_seconds=float(self.__timeout),
                    provider='openai',
                    original_error=e,
                ) from e

    def _extract_retry_after(
        self, error: OpenAIRateLimitError
    ) -> Optional[float]:
        """
        Extract retry_after value from OpenAI rate limit error.

        Args:
            error: The OpenAI rate limit error.

        Returns:
            Seconds to wait, or None if not available.
        """
        try:
            if hasattr(error, 'response') and error.response:
                headers = getattr(error.response, 'headers', {})
                retry_after = headers.get('retry-after') or headers.get(
                    'Retry-After'
                )
                if retry_after:
                    return float(retry_after)

            if hasattr(error, 'headers'):
                retry_after = error.headers.get(
                    'retry-after'
                ) or error.headers.get('Retry-After')
                if retry_after:
                    return float(retry_after)
        except (ValueError, AttributeError, TypeError):
            pass

        return 60.0

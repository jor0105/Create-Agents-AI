import subprocess  # nosec B404
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ollama import AsyncClient, ChatResponse

from ...config import EnvironmentConfig, LoggingConfig, retry_with_backoff


class OllamaClient:
    """Handles direct communication with the Ollama API."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__host = EnvironmentConfig.get_env(
            'OLLAMA_HOST', 'http://localhost:11434'
        )
        self.__max_retries = int(
            EnvironmentConfig.get_env('OLLAMA_MAX_RETRIES', '3')
        )

    @retry_with_backoff(
        max_attempts=3, initial_delay=1.0, exceptions=(Exception,)
    )
    async def call_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Union[ChatResponse, AsyncIterator[ChatResponse]]:
        """Calls the Ollama API with automatic retries.

        Args:
            model: The name of the model to use.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tool schemas.
            tool_choice: Optional tool choice configuration.

        Returns:
            ChatResponse or AsyncIterator[ChatResponse] if streaming.
        """
        try:
            chat_kwargs: Dict[str, Any] = {
                'model': model,
                'messages': messages,
                'stream': config.get('stream', False) if config else False,
            }

            if tools:
                chat_kwargs['tools'] = tools
                # Note: Ollama's native API may not support tool_choice directly
                # but we include it for future compatibility
                if tool_choice:
                    self.__logger.debug(
                        'Tool choice requested: %s (Ollama may have limited support)',
                        tool_choice,
                    )
            if config:
                config_copy = config.copy()
                if 'think' in config_copy:
                    chat_kwargs['think'] = config_copy.pop('think')
                if 'max_tokens' in config_copy:
                    config_copy['num_predict'] = config_copy.pop('max_tokens')
                chat_kwargs['options'] = config_copy

            client = AsyncClient(host=self.__host)
            result: Union[
                ChatResponse, AsyncIterator[ChatResponse]
            ] = await client.chat(**chat_kwargs)
            return result
        except Exception as e:
            self.__logger.error(
                "Error calling Ollama API for model '%s': %s", model, e
            )
            raise

    def stop_model(self, model: str) -> None:
        """Stops the Ollama model after use to free up memory."""
        try:
            subprocess.run(  # nosec B603 B607
                ['ollama', 'stop', model],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.__logger.debug('Model %s stopped successfully.', model)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            self.__logger.warning('Could not stop model %s: %s', model, e)
        except Exception as e:
            self.__logger.warning(
                'Error trying to stop model %s: %s', model, e
            )

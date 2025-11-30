from typing import Any, Dict, List, Optional

from ....domain import ChatException
from ...config import EnvironmentConfig, LoggingConfig, retry_with_backoff
from .client_openai import ClientOpenAI


class OpenAIClient:
    """Handles direct communication with the OpenAI API."""

    def __init__(self):
        """Initialize the OpenAI client.

        Raises:
            ChatException: If the API key is missing or invalid.
        """
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__timeout = int(EnvironmentConfig.get_env('OPENAI_TIMEOUT', '30'))
        self.__max_retries = int(
            EnvironmentConfig.get_env('OPENAI_MAX_RETRIES', '3')
        )

        try:
            api_key = EnvironmentConfig.get_api_key(
                ClientOpenAI.API_OPENAI_NAME
            )
            self.__client = ClientOpenAI.get_client(api_key)
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

    @retry_with_backoff(
        max_attempts=3, initial_delay=1.0, exceptions=(Exception,)
    )
    def call_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Calls the OpenAI API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: Internal AI configuration.
            tools: Optional list of tool schemas for function calling.

        Returns:
            The API response.
        """
        chat_kwargs: Dict[str, Any] = {
            'model': model,
            'input': messages,
        }

        if tools:
            chat_kwargs['tools'] = tools
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
                if 'reasoning' == key:
                    chat_kwargs['reasoning'] = {'effort': config_data}
                else:
                    chat_kwargs[key] = config_data

        response_api = self.__client.responses.create(**chat_kwargs)

        return response_api

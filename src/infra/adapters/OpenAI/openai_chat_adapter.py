import time
from typing import Any, Dict, List, Optional

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.exceptions import ChatException
from src.infra.adapters.OpenAI.client_openai import ClientOpenAI
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OpenAIChatAdapter(ChatRepository):
    """An adapter for communicating with the OpenAI API."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__timeout = int(EnvironmentConfig.get_env("OPENAI_TIMEOUT", "30"))
        self.__max_retries = int(EnvironmentConfig.get_env("OPENAI_MAX_RETRIES", "3"))

        try:
            api_key = EnvironmentConfig.get_api_key(ClientOpenAI.API_OPENAI_NAME)
            self.__client = ClientOpenAI.get_client(api_key)
            self.__logger.info(
                f"OpenAI adapter initialized (timeout: {self.__timeout}s, "
                f"max_retries: {self.__max_retries})"
            )
        except EnvironmentError as e:
            self.__logger.error(f"Error configuring OpenAI: {str(e)}")
            raise ChatException(f"Error configuring OpenAI: {str(e)}", e)

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    def __call_openai_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> Any:
        """
        Calls the OpenAI API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: Internal AI configuration.

        Returns:
            The API response.
        """
        api_kwargs = {
            "model": model,
            "input": messages,
        }

        param_mapping = {
            "temperature": "temperature",
            "max_tokens": "max_output_tokens",
            "top_p": "top_p",
        }
        for config_key, api_key in param_mapping.items():
            if config_key in config:
                api_kwargs[api_key] = config[config_key]

        response_api = self.__client.responses.create(**api_kwargs)

        return response_api

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Sends a message to OpenAI and returns the response.

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI configuration.
            history: The conversation history.
            user_ask: The user's question.

        Returns:
            The model's response.

        Raises:
            ChatException: If a communication error occurs.
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Starting chat with model {model} on OpenAI.")

            messages = []
            if instructions and instructions.strip():
                messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            response_api = self.__call_openai_api(model, messages, config)

            content: str = response_api.output_text
            if not content:
                self.__logger.warning("OpenAI returned an empty response.")
                raise ChatException("OpenAI returned an empty response.")

            latency = (time.time() - start_time) * 1000

            usage = getattr(response_api, "usage", None)
            if usage:
                tokens_used = getattr(usage, "total_tokens", None)
                prompt_tokens = getattr(usage, "input_tokens", None)
                completion_tokens = getattr(usage, "output_tokens", None)
            else:
                tokens_used = None
                prompt_tokens = None
                completion_tokens = None

            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                success=True,
            )
            self.__metrics.append(metrics)

            self.__logger.info(f"Chat completed: {metrics}")
            self.__logger.debug(f"Response (first 100 chars): {content[:100]}...")

            return content

        except ChatException:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message="OpenAI returned an empty response.",
            )
            self.__metrics.append(metrics)
            raise
        except AttributeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Error accessing response: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Error accessing OpenAI response: {str(e)}")
            raise ChatException(
                f"Error accessing OpenAI response: {str(e)}", original_error=e
            )
        except IndexError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Unexpected format: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"OpenAI response has an unexpected format: {str(e)}")
            raise ChatException(
                f"OpenAI response has an unexpected format: {str(e)}", original_error=e
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model, latency_ms=latency, success=False, error_message=str(e)
            )
            self.__metrics.append(metrics)
            self.__logger.error(f"Error communicating with OpenAI: {str(e)}")
            raise ChatException(
                f"Error communicating with OpenAI: {str(e)}", original_error=e
            )

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()

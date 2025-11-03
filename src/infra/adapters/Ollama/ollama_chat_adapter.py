import subprocess
import time
from typing import Any, Dict, List, Optional

from ollama import ChatResponse, chat

from src.application.interfaces.chat_repository import ChatRepository
from src.domain.exceptions import ChatException
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OllamaChatAdapter(ChatRepository):
    """An adapter for communicating with Ollama."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__host = EnvironmentConfig.get_env("OLLAMA_HOST", "http://localhost:11434")
        self.__max_retries = int(EnvironmentConfig.get_env("OLLAMA_MAX_RETRIES", "3"))

        self.__logger.info(
            f"Ollama adapter initialized (host: {self.__host}, "
            f"max_retries: {self.__max_retries})"
        )

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    def __call_ollama_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Dict[str, Any],
    ) -> ChatResponse:
        """
        Calls the Ollama API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: Internal AI settings.

        Returns:
            The API response.
        """
        if "max_tokens" in config:
            config["num_predict"] = config.pop("max_tokens")

        response_api: ChatResponse = chat(
            model=model,
            messages=messages,
            options=config,
        )

        return response_api

    def __stop_model(self, model: str) -> None:
        """
        Stops the Ollama model after use to free up memory.

        Args:
            model: The name of the model to stop.
        """
        try:
            subprocess.run(
                ["ollama", "stop", model],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.__logger.debug(f"Model {model} stopped successfully.")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.__logger.warning(f"Could not stop model {model}: {str(e)}")
        except Exception as e:
            self.__logger.warning(f"Error trying to stop model {model}: {str(e)}")

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Sends a message to Ollama and returns the response.

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI settings.
            history: The conversation history.
            user_ask: The user's question.

        Returns:
            The model's response.

        Raises:
            ChatException: If a communication error occurs.
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Starting chat with model {model} on Ollama.")

            messages = []
            if instructions and instructions.strip():
                messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            response_api = self.__call_ollama_api(model, messages, config)

            content: str = response_api.message.content
            if not content:
                self.__logger.warning("Ollama returned an empty response.")
                raise ChatException("Ollama returned an empty response.")

            latency = (time.time() - start_time) * 1000

            tokens_info = response_api.get("eval_count", None)

            metrics = ChatMetrics(
                model=model, latency_ms=latency, tokens_used=tokens_info, success=True
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
                error_message="Ollama returned an empty response.",
            )
            self.__metrics.append(metrics)
            raise
        except KeyError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Missing key: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"The Ollama response has an invalid format. Missing key: {str(e)}"
            )
            raise ChatException(
                f"The Ollama response has an invalid format. Missing key: {str(e)}",
                original_error=e,
            )
        except TypeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Type error: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"A type error occurred while processing the Ollama response: {str(e)}"
            )
            raise ChatException(
                f"A type error occurred while processing the Ollama response: {str(e)}",
                original_error=e,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model, latency_ms=latency, success=False, error_message=str(e)
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"An error occurred while communicating with Ollama: {str(e)}"
            )
            raise ChatException(
                f"An error occurred while communicating with Ollama: {str(e)}",
                original_error=e,
            )
        finally:
            self.__stop_model(model)

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()

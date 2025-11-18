from typing import Dict, Tuple

from ...application.interfaces import ChatRepository
from ..adapters import OllamaChatAdapter, OpenAIChatAdapter
from ..config import LoggingConfig


class ChatAdapterFactory:
    """
    A factory for creating chat adapters with caching.

    The caching mechanism prevents the creation of multiple instances of the same
    adapter, improving performance and reducing initialization overhead.
    """

    __cache: Dict[Tuple[str, str], ChatRepository] = {}
    __logger = LoggingConfig.get_logger(__name__)

    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
    ) -> ChatRepository:
        """
        Creates the appropriate adapter with caching.

        Args:
            model: The name of the model (e.g., "gpt-4", "llama2").
            provider: The specific provider ("openai", "ollama").

        Returns:
            An instance of the appropriate adapter, cached if it already exists.

        Raises:
            ValueError: If the provider is not "openai" or "ollama".
        """
        cache_key = (model.lower(), provider.lower())

        if cache_key in cls.__cache:
            cls.__logger.debug(
                f"Returning cached adapter for provider '{provider}' and model '{model}'"
            )
            return cls.__cache[cache_key]

        cls.__logger.info(
            f"Creating new chat adapter - Provider: {provider}, Model: {model}"
        )

        provider_lower = provider.lower()
        adapter: ChatRepository

        if provider_lower == "openai":
            cls.__logger.debug("Creating OpenAI chat adapter")
            adapter = OpenAIChatAdapter()
        elif provider_lower == "ollama":
            cls.__logger.debug("Creating Ollama chat adapter")
            adapter = OllamaChatAdapter()
        else:
            cls.__logger.error(f"Invalid provider requested: {provider}")
            raise ValueError(f"Invalid provider: {provider}.")

        cls.__cache[cache_key] = adapter
        cls.__logger.debug(f"Adapter cached with key: {cache_key}")

        return adapter

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the adapter cache."""
        cache_size = len(cls.__cache)
        cls.__cache.clear()
        cls.__logger.info(
            f"Adapter cache cleared - Removed {cache_size} cached adapter(s)"
        )

from typing import Dict, Tuple

from src.application import ChatRepository
from src.infra.adapters.Ollama.ollama_chat_adapter import OllamaChatAdapter
from src.infra.adapters.OpenAI.openai_chat_adapter import OpenAIChatAdapter


class ChatAdapterFactory:
    """
    A factory for creating chat adapters with caching.

    The caching mechanism prevents the creation of multiple instances of the same
    adapter, improving performance and reducing initialization overhead.
    """

    __cache: Dict[Tuple[str, str], ChatRepository] = {}

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
            return cls.__cache[cache_key]

        provider_lower = provider.lower()
        adapter: ChatRepository
        if provider_lower == "openai":
            adapter = OpenAIChatAdapter()
        elif provider_lower == "ollama":
            adapter = OllamaChatAdapter()
        else:
            raise ValueError(f"Invalid provider: {provider}.")

        cls.__cache[cache_key] = adapter

        return adapter

    @classmethod
    def clear_cache(cls) -> None:
        cls.__cache.clear()

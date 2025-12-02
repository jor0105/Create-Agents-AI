from typing import Dict, Tuple, Type

from ...application.interfaces import ChatRepository
from ..adapters import OllamaChatAdapter, OpenAIChatAdapter
from ..config import LoggingConfig


class ChatAdapterFactory:
    """
    A factory for creating chat adapters with caching.

    The caching mechanism prevents the creation of multiple instances of the same
    adapter, improving performance and reducing initialization overhead.

    Uses a registry pattern with O(1) lookup for efficient provider resolution.
    """

    __cache: Dict[Tuple[str, str], ChatRepository] = {}
    __logger = LoggingConfig.get_logger(__name__)

    # Strategy Pattern: Registry for O(1) lookup instead of O(n) conditional chain
    __ADAPTER_REGISTRY: Dict[str, Type[ChatRepository]] = {
        'openai': OpenAIChatAdapter,
        'ollama': OllamaChatAdapter,
    }

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
            ValueError: If the provider is not supported.
        """
        cache_key = (model.lower(), provider.lower())

        if cache_key in cls.__cache:
            cls.__logger.debug(
                "Returning cached adapter for provider '%s' and model '%s'",
                provider,
                model,
            )
            return cls.__cache[cache_key]

        cls.__logger.info(
            'Creating new chat adapter - Provider: %s, Model: %s',
            provider,
            model,
        )

        provider_lower = provider.lower()

        # O(1) lookup instead of O(n) conditional chain
        adapter_class = cls.__ADAPTER_REGISTRY.get(provider_lower)

        if adapter_class is None:
            cls.__logger.error('Invalid provider requested: %s', provider)
            raise ValueError(
                f'Invalid provider: {provider}. '
                f'Supported providers: {", ".join(cls.__ADAPTER_REGISTRY.keys())}'
            )

        cls.__logger.debug('Creating %s chat adapter', provider.title())
        adapter = adapter_class()

        cls.__cache[cache_key] = adapter
        cls.__logger.debug('Adapter cached with key: %s', cache_key)

        return adapter

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the adapter cache, forcing new instances on subsequent calls.

        This method is primarily used in testing environments to ensure proper
        isolation between test cases. By clearing the cache, each test can start
        with a fresh state, preventing cross-test contamination and ensuring
        predictable behavior.

        In production, this method should be used sparingly, only when you need
        to force the recreation of all adapter instances (e.g., after a
        configuration change or during application shutdown).

        Note:
            The method logs the number of cached adapters removed for monitoring
            and debugging purposes.
        """
        cache_size = len(cls.__cache)
        cls.__cache.clear()
        cls.__logger.info(
            'Adapter cache cleared - Removed %s cached adapter(s)', cache_size
        )

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Returns a list of all supported provider names.

        Returns:
            A list of provider names that can be used with the create() method.

        Example:
            >>> ChatAdapterFactory.get_supported_providers()
            ['openai', 'ollama']
        """
        return list(cls.__ADAPTER_REGISTRY.keys())

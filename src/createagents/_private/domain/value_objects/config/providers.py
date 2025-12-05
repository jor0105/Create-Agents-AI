from typing import Set

from ...exceptions import InvalidProviderException


class SupportedProviders:
    """
    Manages the available AI providers.

    Responsibilities:
    - Define the providers supported by the system.
    - Provide an interface for querying available providers.
    """

    __AVAILABLE_PROVIDERS: Set[str] = {'openai', 'ollama'}

    @classmethod
    def validate_provider(cls, provider: str) -> None:
        """
        Validates if the provider is supported.

        Args:
            provider: The provider to validate.

        Raises:
            InvalidProviderException: If the provider is not supported.
        """
        if provider.lower() not in cls.__AVAILABLE_PROVIDERS:
            raise InvalidProviderException(
                provider, cls.__AVAILABLE_PROVIDERS.copy()
            )

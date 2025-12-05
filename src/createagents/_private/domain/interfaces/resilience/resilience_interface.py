from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ResilienceSettings:
    """Immutable settings for resilience configuration.

    This dataclass holds all resilience-related settings that can be
    configured by the user. It's designed to be immutable (frozen=True)
    to prevent accidental modifications after configuration.

    Attributes:
        enabled: Whether internal resilience mechanisms are active.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before first retry.
        backoff_factor: Multiplier for delay between retries.
        jitter: Whether to add random variation to delays.
        respect_retry_after: Whether to honor Retry-After headers.
        openai_max_concurrent: Max concurrent requests to OpenAI.
        ollama_max_concurrent: Max concurrent requests to Ollama.
    """

    enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 0.5
    backoff_factor: float = 2.0
    jitter: bool = True
    respect_retry_after: bool = True
    openai_max_concurrent: int = 100
    ollama_max_concurrent: int = 30


class IResilienceConfig(ABC):
    """Interface for resilience configuration management.

    This interface defines the contract for managing resilience settings
    throughout the application. Implementations should provide thread-safe
    access to configuration values.
    """

    @abstractmethod
    def get_settings(self) -> ResilienceSettings:
        """Get the current resilience settings.

        Returns:
            Current ResilienceSettings instance.
        """

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if internal resilience is enabled.

        Returns:
            True if resilience mechanisms should be active.
        """

    @abstractmethod
    def get_max_retries(self) -> int:
        """Get maximum retry attempts.

        Returns:
            Number of retry attempts.
        """

    @abstractmethod
    def get_initial_delay(self) -> float:
        """Get initial delay before first retry.

        Returns:
            Delay in seconds.
        """

    @abstractmethod
    def get_backoff_factor(self) -> float:
        """Get backoff multiplication factor.

        Returns:
            Backoff factor.
        """

    @abstractmethod
    def get_max_concurrent(self, provider: str) -> int:
        """Get max concurrent requests for a provider.

        Args:
            provider: The API provider name ('openai' or 'ollama').

        Returns:
            Maximum concurrent requests allowed.
        """

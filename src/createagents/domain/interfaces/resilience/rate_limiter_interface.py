from abc import ABC, abstractmethod
from typing import Dict


class IRateLimiter(ABC):
    """
    Abstract interface for rate limiting.

    Following the Dependency Inversion Principle (DIP), this interface
    allows domain and application layers to depend on the abstraction
    rather than concrete implementations.

    Example:
        >>> class MyClient:
        ...     def __init__(self, rate_limiter: IRateLimiter):
        ...         self._rate_limiter = rate_limiter
        ...
        ...     async def call_api(self):
        ...         async with self._rate_limiter:
        ...             return await self._make_request()
    """

    @abstractmethod
    async def acquire(self) -> None:
        """
        Acquire a slot in the rate limiter.

        This method blocks until a slot is available.
        """

    @abstractmethod
    def release(self) -> None:
        """Release a slot in the rate limiter."""

    @abstractmethod
    async def __aenter__(self) -> 'IRateLimiter':
        """Async context manager entry."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""

    @property
    @abstractmethod
    def current_requests(self) -> int:
        """Return the current number of active requests."""

    @property
    @abstractmethod
    def max_concurrent(self) -> int:
        """Return the maximum concurrent requests allowed."""

    @property
    @abstractmethod
    def available_slots(self) -> int:
        """Return the number of available request slots."""


class IRateLimiterFactory(ABC):
    """
    Abstract factory for creating rate limiters.

    Following the Abstract Factory pattern combined with DIP,
    this allows different rate limiter implementations to be
    injected without changing client code.
    """

    @abstractmethod
    def get_limiter(self, provider: str) -> IRateLimiter:
        """
        Get or create a rate limiter for the specified provider.

        Args:
            provider: The API provider name (e.g., 'openai', 'ollama').

        Returns:
            IRateLimiter instance for the provider.
        """

    @abstractmethod
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all rate limiters.

        Returns:
            Dict with provider names as keys and stats as values.
        """

    @abstractmethod
    def reset(self, provider: str | None = None) -> None:
        """
        Reset rate limiter instance(s).

        Args:
            provider: If specified, reset only that provider's limiter.
                     If None, reset all limiters.
        """

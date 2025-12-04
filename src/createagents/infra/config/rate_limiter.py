import asyncio
import threading
from typing import Dict, Optional

from ...domain.interfaces.rate_limiter_interface import (
    IRateLimiter,
    IRateLimiterFactory,
)
from .environment import EnvironmentConfig
from .logging_config import create_logger


class RateLimiter(IRateLimiter):
    """
    Concrete implementation of IRateLimiter using asyncio.Semaphore.

    Controls the maximum number of concurrent requests to external APIs,
    preventing rate limit errors (HTTP 429) when many users access the
    system simultaneously.

    Example:
        >>> limiter = RateLimiterFactory.get_instance().get_limiter('openai')
        >>> async with limiter:
        ...     await make_api_call()
    """

    def __init__(self, provider: str, max_concurrent: int):
        """
        Initialize the rate limiter.

        Args:
            provider: The API provider name (e.g., 'openai', 'ollama').
            max_concurrent: Maximum number of concurrent requests allowed.
        """
        self._provider = provider
        self._max_concurrent = max_concurrent
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._current_requests = 0
        self._internal_lock = threading.Lock()
        self._logger = create_logger(__name__)

    def _get_semaphore(self) -> asyncio.Semaphore:
        """
        Get or create the semaphore for this rate limiter.

        Lazily creates the semaphore to ensure it's created in the
        correct event loop context.

        Returns:
            The asyncio.Semaphore instance.
        """
        if self._semaphore is None:
            with self._internal_lock:
                if self._semaphore is None:
                    self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    async def acquire(self) -> None:
        """Acquire a slot in the rate limiter."""
        semaphore = self._get_semaphore()
        await semaphore.acquire()
        with self._internal_lock:
            self._current_requests += 1
            self._logger.debug(
                '[%s] Request acquired. Active: %d/%d',
                self._provider,
                self._current_requests,
                self._max_concurrent,
            )

    def release(self) -> None:
        """Release a slot in the rate limiter."""
        semaphore = self._get_semaphore()
        semaphore.release()
        with self._internal_lock:
            self._current_requests -= 1
            self._logger.debug(
                '[%s] Request released. Active: %d/%d',
                self._provider,
                self._current_requests,
                self._max_concurrent,
            )

    async def __aenter__(self) -> 'RateLimiter':
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.release()

    @property
    def current_requests(self) -> int:
        """Return the current number of active requests."""
        with self._internal_lock:
            return self._current_requests

    @property
    def max_concurrent(self) -> int:
        """Return the maximum concurrent requests allowed."""
        return self._max_concurrent

    @property
    def available_slots(self) -> int:
        """Return the number of available request slots."""
        with self._internal_lock:
            return self._max_concurrent - self._current_requests


class RateLimiterFactory(IRateLimiterFactory):
    """
    Singleton factory for creating and managing rate limiters.

    Follows the Singleton pattern for global access and the
    Abstract Factory pattern for creating rate limiters.

    Uses ResilienceConfig for default concurrent request limits,
    allowing users to configure via configure_resilience().

    Example:
        >>> factory = RateLimiterFactory.get_instance()
        >>> openai_limiter = factory.get_limiter('openai')
        >>> ollama_limiter = factory.get_limiter('ollama')
    """

    _instance: Optional['RateLimiterFactory'] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        """Initialize the factory with empty limiters dict."""
        self._limiters: Dict[str, RateLimiter] = {}
        self._logger = create_logger(__name__)

    @classmethod
    def get_instance(cls) -> 'RateLimiterFactory':
        """
        Get the singleton factory instance.

        Returns:
            The singleton RateLimiterFactory instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_limiter(self, provider: str) -> IRateLimiter:
        """
        Get or create a rate limiter for the specified provider.

        Uses ResilienceConfig to get configured max_concurrent values.
        Falls back to environment variables if set.

        Args:
            provider: The API provider name ('openai' or 'ollama').

        Returns:
            IRateLimiter instance for the provider.
        """
        from .resilience_config import ResilienceConfig  # pylint: disable=import-outside-toplevel

        provider_lower = provider.lower()

        if provider_lower not in self._limiters:
            with self._lock:
                if provider_lower not in self._limiters:
                    resilience_config = ResilienceConfig.get_instance()
                    default = resilience_config.get_max_concurrent(
                        provider_lower
                    )

                    env_key = f'{provider.upper()}_MAX_CONCURRENT_REQUESTS'
                    env_value = EnvironmentConfig.get_env(env_key, '')

                    if env_value:
                        max_concurrent = int(env_value)
                    else:
                        max_concurrent = default

                    self._logger.info(
                        'Creating RateLimiter for %s with max_concurrent=%d',
                        provider,
                        max_concurrent,
                    )

                    self._limiters[provider_lower] = RateLimiter(
                        provider_lower, max_concurrent
                    )

        return self._limiters[provider_lower]

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all rate limiters.

        Returns:
            Dict with provider names as keys and stats as values.
        """
        stats = {}
        with self._lock:
            for provider, limiter in self._limiters.items():
                stats[provider] = {
                    'max_concurrent': limiter.max_concurrent,
                    'current_requests': limiter.current_requests,
                    'available_slots': limiter.available_slots,
                }
        return stats

    def reset(self, provider: str | None = None) -> None:
        """
        Reset rate limiter instance(s).

        Args:
            provider: If specified, reset only that provider's limiter.
                     If None, reset all limiters.
        """
        with self._lock:
            if provider:
                provider_lower = provider.lower()
                if provider_lower in self._limiters:
                    del self._limiters[provider_lower]
                    self._logger.info(
                        'RateLimiter for %s has been reset', provider
                    )
            else:
                self._limiters.clear()
                self._logger.info('All RateLimiter instances have been reset')

    @classmethod
    def reset_factory(cls) -> None:
        """Reset the singleton factory instance (mainly for testing)."""
        with cls._lock:
            cls._instance = None

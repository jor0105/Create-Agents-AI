import threading
from typing import Optional

from ....domain.interfaces.resilience import (
    IResilienceConfig,
    ResilienceSettings,
)
from ..environment.environment import EnvironmentConfig
from ..logging.logging_config import create_logger


class ResilienceConfig(IResilienceConfig):
    """Singleton implementation of IResilienceConfig.

    Manages global resilience settings for the application.
    Thread-safe with double-check locking pattern.

    The configuration can be set once via configure_resilience() and
    then accessed throughout the application via get_instance().

    Example:
        >>> from createagents import configure_resilience
        >>> configure_resilience(max_retries=5, initial_delay=0.3)
        >>> # Later in the code
        >>> config = ResilienceConfig.get_instance()
        >>> config.get_max_retries()  # Returns 5
    """

    _instance: Optional['ResilienceConfig'] = None
    _lock: threading.Lock = threading.Lock()
    _configured: bool = False

    def __init__(self, settings: Optional[ResilienceSettings] = None):
        """Initialize with optional settings.

        Args:
            settings: Optional settings. If None, uses defaults with env overrides.
        """
        self._logger = create_logger(__name__)

        if settings:
            self._settings = settings
        else:
            self._settings = self._create_default_settings()

        self._logger.debug(
            'ResilienceConfig initialized (enabled=%s, max_retries=%d)',
            self._settings.enabled,
            self._settings.max_retries,
        )

    def _create_default_settings(self) -> ResilienceSettings:
        """Create default settings with environment variable overrides.

        Returns:
            ResilienceSettings with defaults and env overrides applied.
        """
        return ResilienceSettings(
            enabled=(
                EnvironmentConfig.get_env('RESILIENCE_ENABLED', 'true')
                or 'true'
            ).lower()
            == 'true',
            max_retries=int(
                EnvironmentConfig.get_env('RESILIENCE_MAX_RETRIES', '2') or '2'
            ),
            initial_delay=float(
                EnvironmentConfig.get_env('RESILIENCE_INITIAL_DELAY', '0.1')
                or '0.1'
            ),
            backoff_factor=float(
                EnvironmentConfig.get_env('RESILIENCE_BACKOFF_FACTOR', '1.5')
                or '1.5'
            ),
            jitter=(
                EnvironmentConfig.get_env('RESILIENCE_JITTER', 'true')
                or 'true'
            ).lower()
            == 'true',
            respect_retry_after=(
                EnvironmentConfig.get_env(
                    'RESILIENCE_RESPECT_RETRY_AFTER', 'true'
                )
                or 'true'
            ).lower()
            == 'true',
            openai_max_concurrent=int(
                EnvironmentConfig.get_env(
                    'OPENAI_MAX_CONCURRENT_REQUESTS', '100'
                )
                or '100'
            ),
            ollama_max_concurrent=int(
                EnvironmentConfig.get_env(
                    'OLLAMA_MAX_CONCURRENT_REQUESTS', '30'
                )
                or '30'
            ),
        )

    @classmethod
    def get_instance(cls) -> 'ResilienceConfig':
        """Get the singleton instance.

        Returns:
            The singleton ResilienceConfig instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def configure(cls, settings: ResilienceSettings) -> 'ResilienceConfig':
        """Configure the singleton with specific settings.

        This should be called once at application startup.
        Subsequent calls will log a warning but still apply new settings.

        Args:
            settings: The ResilienceSettings to apply.

        Returns:
            The configured ResilienceConfig instance.
        """
        with cls._lock:
            if cls._configured:
                logger = create_logger(__name__)
                logger.warning(
                    'ResilienceConfig is being reconfigured. '
                    'This may cause inconsistent behavior.'
                )

            cls._instance = cls(settings)
            cls._configured = True

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        with cls._lock:
            cls._instance = None
            cls._configured = False

    def get_settings(self) -> ResilienceSettings:
        """Get the current resilience settings."""
        return self._settings

    def is_enabled(self) -> bool:
        """Check if internal resilience is enabled."""
        return self._settings.enabled

    def get_max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self._settings.max_retries

    def get_initial_delay(self) -> float:
        """Get initial delay before first retry."""
        return self._settings.initial_delay

    def get_backoff_factor(self) -> float:
        """Get backoff multiplication factor."""
        return self._settings.backoff_factor

    def get_max_concurrent(self, provider: str) -> int:
        """Get max concurrent requests for a provider.

        Args:
            provider: The API provider name ('openai' or 'ollama').

        Returns:
            Maximum concurrent requests allowed.
        """
        provider_lower = provider.lower()
        if provider_lower == 'openai':
            return self._settings.openai_max_concurrent
        elif provider_lower == 'ollama':
            return self._settings.ollama_max_concurrent
        else:
            return 20


def configure_resilience(
    enabled: bool = True,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    respect_retry_after: bool = True,
    openai_max_concurrent: int = 100,
    ollama_max_concurrent: int = 30,
) -> ResilienceConfig:
    """Configure global resilience settings for the application.

    This is the primary entry point for configuring retry and rate limiting
    behavior. Call this once at application startup before creating agents.

    When enabled=False, the internal rate limiter and retry mechanisms are
    disabled, allowing external systems (like API gateways with circuit
    breakers) to handle resilience.

    Args:
        enabled: Enable internal resilience mechanisms. Set to False when
                 using external rate limiting/circuit breakers. Default: True.
        max_retries: Maximum number of retry attempts. Default: 3.
        initial_delay: Initial delay in seconds before first retry. Default: 0.5.
        backoff_factor: Multiplier for delay between retries. Default: 2.0.
        jitter: Add random variation to delays (prevents thundering herd). Default: True.
        respect_retry_after: Honor Retry-After headers from APIs. Default: True.
        openai_max_concurrent: Max concurrent requests to OpenAI. Default: 100.
        ollama_max_concurrent: Max concurrent requests to Ollama. Default: 30.

    Returns:
        Configured ResilienceConfig instance.

    Example:
        >>> from createagents import configure_resilience
        >>>
        >>> # Standard configuration with custom values
        >>> configure_resilience(
        ...     max_retries=5,
        ...     initial_delay=0.3,
        ...     openai_max_concurrent=200,
        ... )
        >>>
        >>> # Disable internal resilience (using external system)
        >>> configure_resilience(enabled=False)
    """
    settings = ResilienceSettings(
        enabled=enabled,
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        respect_retry_after=respect_retry_after,
        openai_max_concurrent=openai_max_concurrent,
        ollama_max_concurrent=ollama_max_concurrent,
    )

    return ResilienceConfig.configure(settings)

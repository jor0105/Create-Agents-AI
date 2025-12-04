import asyncio
import inspect
import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from .logging_config import create_logger


def _calculate_delay(
    base_delay: float,
    jitter: bool,
    rate_limit_retry_after: Optional[float] = None,
) -> float:
    """
    Calculate the actual delay for retry.

    Args:
        base_delay: The base delay in seconds.
        jitter: Whether to add jitter to the delay.
        rate_limit_retry_after: If set, use this value instead (from 429 response).

    Returns:
        The calculated delay in seconds.
    """
    if rate_limit_retry_after is not None:
        return rate_limit_retry_after

    actual_delay = base_delay
    if jitter:
        jitter_factor = 1 + random.uniform(-0.1, 0.1)  # nosec
        actual_delay = base_delay * jitter_factor

    return actual_delay


def _is_rate_limit_error(exception: Exception) -> Tuple[bool, Optional[float]]:
    """
    Check if exception is a rate limit error and extract retry_after.

    Args:
        exception: The exception to check.

    Returns:
        Tuple of (is_rate_limit, retry_after_seconds).
    """
    from ...domain.exceptions import RateLimitError  # pylint: disable=import-outside-toplevel

    if isinstance(exception, RateLimitError):
        return True, exception.retry_after

    return False, None


def retry_with_backoff(
    max_attempts: Optional[int] = None,
    initial_delay: Optional[float] = None,
    backoff_factor: Optional[float] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: Optional[bool] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    respect_retry_after: Optional[bool] = None,
):
    """
    A decorator for retrying with exponential backoff and jitter.
    Supports both synchronous and asynchronous functions.

    Uses ResilienceConfig for default values, allowing global configuration
    via configure_resilience(). When resilience is disabled, the decorator
    becomes a no-op passthrough.

    Special handling for RateLimitError:
    - If exception has retry_after attribute, uses that delay instead of backoff
    - Logs rate limit events specially for monitoring

    Args:
        max_attempts: The maximum number of attempts. Default: from ResilienceConfig.
        initial_delay: The initial delay in seconds. Default: from ResilienceConfig.
        backoff_factor: The multiplication factor for delay. Default: from ResilienceConfig.
        exceptions: A tuple of exceptions that should trigger a retry.
        jitter: If True, adds random variation to the delay (±10%) to prevent
                the "thundering herd" problem in distributed systems.
        on_retry: An optional callback to be called on each retry, receiving
                  the attempt number and the exception.
        respect_retry_after: If True, respects Retry-After from RateLimitError.

    Returns:
        A decorator function.

    Example:
        >>> @retry_with_backoff(max_attempts=3)
        ... def api_call():
        ...     return requests.get("...")
        ...
        >>> @retry_with_backoff(max_attempts=3)
        ... async def async_api_call():
        ...     return await client.get("...")
    """
    from .resilience_config import ResilienceConfig  # pylint: disable=import-outside-toplevel

    logger = create_logger(__name__)

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        resilience_cfg = ResilienceConfig.get_instance()
        settings = resilience_cfg.get_settings()

        if not settings.enabled:
            return func

        effective_max_attempts = (
            max_attempts if max_attempts is not None else settings.max_retries
        )
        effective_initial_delay = (
            initial_delay
            if initial_delay is not None
            else settings.initial_delay
        )
        effective_backoff_factor = (
            backoff_factor
            if backoff_factor is not None
            else settings.backoff_factor
        )
        effective_jitter = jitter if jitter is not None else settings.jitter
        effective_respect_retry_after = (
            respect_retry_after
            if respect_retry_after is not None
            else settings.respect_retry_after
        )

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = effective_initial_delay
            last_exception = None

            for attempt in range(1, effective_max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == effective_max_attempts:
                        logger.error(
                            'Failure after %s attempts: %s',
                            effective_max_attempts,
                            e,
                        )
                        raise

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(
                                'Error in retry callback: %s', callback_error
                            )

                    is_rate_limit, retry_after = _is_rate_limit_error(e)

                    if (
                        is_rate_limit
                        and effective_respect_retry_after
                        and retry_after
                    ):
                        actual_delay = _calculate_delay(
                            delay,
                            jitter=False,
                            rate_limit_retry_after=retry_after,
                        )
                        logger.warning(
                            'Rate limit hit (attempt %s/%s). '
                            'Waiting %.2fs (from Retry-After header)...',
                            attempt,
                            effective_max_attempts,
                            actual_delay,
                        )
                    else:
                        actual_delay = _calculate_delay(
                            delay, effective_jitter
                        )
                        logger.warning(
                            'Attempt %s/%s failed: %s. '
                            'Waiting %.2fs before retrying...',
                            attempt,
                            effective_max_attempts,
                            e,
                            actual_delay,
                        )

                    await asyncio.sleep(actual_delay)

                    if not (is_rate_limit and retry_after):
                        delay *= effective_backoff_factor

            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = effective_initial_delay
            last_exception = None

            for attempt in range(1, effective_max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == effective_max_attempts:
                        logger.error(
                            'Failure after %s attempts: %s',
                            effective_max_attempts,
                            e,
                        )
                        raise

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(
                                'Error in retry callback: %s', callback_error
                            )

                    is_rate_limit, retry_after = _is_rate_limit_error(e)

                    if (
                        is_rate_limit
                        and effective_respect_retry_after
                        and retry_after
                    ):
                        actual_delay = _calculate_delay(
                            delay,
                            jitter=False,
                            rate_limit_retry_after=retry_after,
                        )
                        logger.warning(
                            'Rate limit hit (attempt %s/%s). '
                            'Waiting %.2fs (from Retry-After header)...',
                            attempt,
                            effective_max_attempts,
                            actual_delay,
                        )
                    else:
                        actual_delay = _calculate_delay(
                            delay, effective_jitter
                        )
                        logger.warning(
                            'Attempt %s/%s failed: %s. '
                            'Waiting %.2fs before retrying...',
                            attempt,
                            effective_max_attempts,
                            e,
                            actual_delay,
                        )

                    time.sleep(actual_delay)

                    if not (is_rate_limit and retry_after):
                        delay *= effective_backoff_factor

            if last_exception:
                raise last_exception

        return async_wrapper if is_async else sync_wrapper

    return decorator

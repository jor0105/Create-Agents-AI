import asyncio
import inspect
import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from .logging_config import create_logger


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    A decorator for retrying with exponential backoff and jitter.
    Supports both synchronous and asynchronous functions.

    Args:
        max_attempts: The maximum number of attempts.
        initial_delay: The initial delay in seconds.
        backoff_factor: The multiplication factor for the delay at each attempt.
        exceptions: A tuple of exceptions that should trigger a retry.
        jitter: If True, adds random variation to the delay (±10%) to prevent
                the "thundering herd" problem in distributed systems.
        on_retry: An optional callback to be called on each retry, receiving
                  the attempt number and the exception.

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
    logger = create_logger(__name__)

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            'Failure after %s attempts: %s', max_attempts, e
                        )
                        raise

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(
                                'Error in retry callback: %s', callback_error
                            )

                    actual_delay = delay
                    if jitter:
                        jitter_factor = 1 + random.uniform(-0.1, 0.1)  # nosec
                        actual_delay = delay * jitter_factor

                    logger.warning(
                        'Attempt %s/%s failed: %s. Waiting %.2fs before retrying...',
                        attempt,
                        max_attempts,
                        e,
                        actual_delay,
                    )

                    await asyncio.sleep(actual_delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            'Failure after %s attempts: %s', max_attempts, e
                        )
                        raise

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(
                                'Error in retry callback: %s', callback_error
                            )

                    actual_delay = delay
                    if jitter:
                        jitter_factor = 1 + random.uniform(-0.1, 0.1)  # nosec
                        actual_delay = delay * jitter_factor

                    logger.warning(
                        'Attempt %s/%s failed: %s. Waiting %.2fs before retrying...',
                        attempt,
                        max_attempts,
                        e,
                        actual_delay,
                    )

                    time.sleep(actual_delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        return async_wrapper if is_async else sync_wrapper

    return decorator

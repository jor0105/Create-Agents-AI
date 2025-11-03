import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from src.infra.config.logging_config import LoggingConfig


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
        >>> @retry_with_backoff(max_attempts=3, initial_delay=1.0, jitter=True)
        ... def api_call():
        ...     return requests.get("https://api.example.com")
    """
    logger = LoggingConfig.get_logger(__name__)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(f"Failure after {max_attempts} attempts: {str(e)}")
                        raise

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.warning(f"Error in retry callback: {callback_error}")

                    actual_delay = delay
                    if jitter:
                        jitter_factor = 1 + random.uniform(-0.1, 0.1)
                        actual_delay = delay * jitter_factor

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {str(e)}. "
                        f"Waiting {actual_delay:.2f}s before retrying..."
                    )

                    time.sleep(actual_delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        return wrapper

    return decorator

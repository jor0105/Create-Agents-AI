import os
import threading
from typing import Dict, Optional

from dotenv import load_dotenv


class EnvironmentConfig:
    """
    A thread-safe singleton for managing environment configurations.
    It loads environment variables only once and uses a lock to ensure
    safety in multi-threaded environments.
    """

    _instance: Optional["EnvironmentConfig"] = None
    _initialized: bool = False
    _cache: Dict[str, str] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "EnvironmentConfig":
        """Implements the singleton pattern with thread-safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initializes and loads environment variables only once."""
        if not EnvironmentConfig._initialized:
            with EnvironmentConfig._lock:
                if not EnvironmentConfig._initialized:
                    load_dotenv()
                    EnvironmentConfig._initialized = True

    @classmethod
    def get_api_key(cls, key: str) -> str:
        """
        Retrieves an API key from environment variables.
        This method is thread-safe and uses a cache to avoid multiple reads.

        Args:
            key: The name of the environment variable.

        Returns:
            The value of the API key.

        Raises:
            EnvironmentError: If the variable is not found or is empty.
        """
        if not cls._initialized:
            cls()

        if key in cls._cache:
            return cls._cache[key]

        with cls._lock:
            if key in cls._cache:
                return cls._cache[key]

            api_key = os.getenv(key)

            if not api_key or not api_key.strip():
                raise EnvironmentError(
                    f"The environment variable '{key}' was not found or is empty. "
                    "Ensure it is defined in the .env file."
                )

            api_key = api_key.strip()
            cls._cache[key] = api_key
            return api_key

    @classmethod
    def get_env(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves an environment variable with an optional default value.
        This method is thread-safe, cached, and validates for empty values.

        Args:
            key: The name of the environment variable.
            default: The default value to return if the variable does not exist.

        Returns:
            The value of the variable or the default.
        """
        if not cls._initialized:
            cls()

        if key in cls._cache:
            return cls._cache[key]

        with cls._lock:
            if key in cls._cache:
                return cls._cache[key]

            value = os.getenv(key, default)

            if value is not None and value.strip():
                value = value.strip()
                cls._cache[key] = value
                return value
            elif default is not None:
                return default

            return value

    @classmethod
    def reload(cls) -> None:
        """
        Reloads environment variables from the .env file.
        This is useful for tests or runtime reconfigurations.
        This method is thread-safe.

        Example:
            >>> EnvironmentConfig.reload()
        """
        with cls._lock:
            load_dotenv(override=True)
            cls._cache.clear()

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the variable cache. This method is thread-safe."""
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def reset(cls) -> None:
        """Completely resets the singleton. This method is thread-safe."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            cls._cache.clear()

from typing import Optional

from openai import AsyncOpenAI


class ClientOpenAI:
    """Client for interacting with the OpenAI API."""

    API_OPENAI_NAME = 'OPENAI_API_KEY'

    @staticmethod
    def get_client(api_key: str, timeout: Optional[int] = None) -> AsyncOpenAI:
        """Create and return an OpenAI client instance.

        Args:
            api_key: The OpenAI API key.
            timeout: Optional timeout in seconds for API requests.

        Returns:
            AsyncOpenAI: The configured OpenAI client.
        """
        client = AsyncOpenAI(
            api_key=api_key,
            timeout=float(timeout) if timeout else 30.0,
        )
        return client

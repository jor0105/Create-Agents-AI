from openai import AsyncOpenAI


class ClientOpenAI:
    """Client for interacting with the OpenAI API."""

    API_OPENAI_NAME = 'OPENAI_API_KEY'

    @staticmethod
    def get_client(api_key: str) -> AsyncOpenAI:
        """Create and return an OpenAI client instance.

        Args:
            api_key: The OpenAI API key.

        Returns:
            AsyncOpenAI: The configured OpenAI client.
        """
        client = AsyncOpenAI(api_key=api_key)
        return client

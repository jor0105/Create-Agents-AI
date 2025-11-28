from openai import OpenAI


class ClientOpenAI:
    """Client for interacting with the OpenAI API."""

    API_OPENAI_NAME = 'OPENAI_API_KEY'

    @staticmethod
    def get_client(api_key: str) -> OpenAI:
        """Create and return an OpenAI client instance.

        Args:
            api_key: The OpenAI API key.

        Returns:
            OpenAI: The configured OpenAI client.
        """
        client = OpenAI(api_key=api_key)
        return client

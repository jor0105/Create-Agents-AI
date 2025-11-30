from typing import AsyncGenerator


class StreamingResponseDTO:
    """Data Transfer Object for streaming chat responses.

    Wraps an async generator to provide a clean interface for async iteration.
    """

    def __init__(self, generator: AsyncGenerator[str, None]):
        """Initialize with a token generator.

        Args:
            generator: AsyncGenerator that yields response tokens as strings.
        """
        self._generator = generator
        self._consumed = False
        self._full_response = ''

    def __aiter__(self):
        """Allow async iteration over tokens."""
        return self

    async def __anext__(self):
        """Get next token asynchronously."""
        if self._consumed:
            raise StopAsyncIteration

        try:
            token = await self._generator.__anext__()
            self._full_response += token
            return token
        except StopAsyncIteration:
            self._consumed = True
            raise

    def __repr__(self) -> str:
        """Return representation."""
        if self._consumed:
            return f'StreamingResponseDTO(consumed, length={len(self._full_response)})'
        return 'StreamingResponseDTO(active)'

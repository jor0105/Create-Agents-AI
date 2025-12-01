from typing import AsyncGenerator


class StreamingResponseDTO:
    """Data Transfer Object for streaming chat responses.

    Wraps an async generator to provide a clean interface for async iteration.
    Can be awaited to get the complete response string automatically.
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

    def __await__(self):
        """Allow awaiting to get complete response string.

        This method enables transparent usage:
            response = await agent.chat("message")  # Returns StreamingResponseDTO
            text = await response  # Auto-consumes and returns complete string

        The CLI can still use async for without awaiting again.
        """

        async def _consume():
            """Consume all tokens and return complete response."""
            if self._consumed:
                return self._full_response

            # Consume all tokens from the generator
            async for _ in self:
                pass  # Tokens are accumulated in _full_response by __anext__

            return self._full_response

        return _consume().__await__()

    def __str__(self) -> str:
        """Return string representation.

        Returns the full response if consumed, otherwise a placeholder.
        For unconsumed streams, await the response first to get the text.
        """
        if self._consumed:
            return self._full_response
        return 'StreamingResponseDTO(not consumed - use "await response")'

    def __repr__(self) -> str:
        """Return representation."""
        if self._consumed:
            return f'StreamingResponseDTO(consumed, length={len(self._full_response)})'
        return 'StreamingResponseDTO(active)'

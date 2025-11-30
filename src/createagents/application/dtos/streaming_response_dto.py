from typing import Generator


class StreamingResponseDTO:
    """Data Transfer Object for streaming chat responses.

    Wraps a generator to provide a clean interface that works seamlessly
    with both iteration and string conversion (via print).

    This is an internal implementation detail - users interact only with
    the result through normal Python operations (print, iteration, etc).
    """

    def __init__(self, generator: Generator[str, None, None]):
        """Initialize with a token generator.

        Args:
            generator: Generator that yields response tokens as strings.
        """
        self._generator = generator
        self._consumed = False
        self._full_response = ''

    def __iter__(self):
        """Allow iteration over tokens."""
        if self._consumed:
            yield self._full_response
        else:
            for token in self._generator:
                self._full_response += token
                yield token
            self._consumed = True

    def __str__(self) -> str:
        """Convert to string by consuming generator and printing tokens in real-time."""
        if self._consumed:
            return self._full_response

        for token in self._generator:
            print(token, end='', flush=True)
            self._full_response += token
        self._consumed = True

        return self._full_response

    def __repr__(self) -> str:
        """Return representation."""
        if self._consumed:
            return f'StreamingResponseDTO(consumed, length={len(self._full_response)})'
        return 'StreamingResponseDTO(active)'

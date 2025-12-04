"""Event loop manager for CLI application.

This module provides a centralized event loop management to prevent
the 'Event loop is closed' error that occurs when using asyncio.run()
multiple times with persistent HTTP connections (like the Ollama client).

The issue: When asyncio.run() completes, it closes the event loop.
However, HTTP clients like httpx maintain connection pools that need
the loop to be alive for cleanup. Multiple asyncio.run() calls create
and destroy loops, leaving dangling connections that fail on cleanup.

Solution: Use a single persistent event loop for the entire CLI session.
"""

import asyncio
import atexit
from typing import Any, Coroutine, Optional, TypeVar

T = TypeVar('T')


class EventLoopManager:
    """Manages a persistent event loop for the CLI application.

    This singleton ensures that:
    1. A single event loop is used throughout the CLI session
    2. Async HTTP clients can reuse connections without loop conflicts
    3. Proper cleanup happens only when the application exits
    """

    _instance: Optional['EventLoopManager'] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None

    def __new__(cls) -> 'EventLoopManager':
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the event loop."""
        # Create a new event loop if none exists or current is closed
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            # Register cleanup on exit
            atexit.register(self._cleanup)

    def _cleanup(self) -> None:
        """Clean up the event loop on application exit."""
        # Reset HTTP clients before closing the loop
        # This prevents "Event loop is closed" errors during connection cleanup
        try:
            from ....infra.adapters.Ollama.ollama_client import (  # pylint: disable=import-outside-toplevel
                OllamaClient,
            )

            OllamaClient.reset_client()
        except ImportError:
            pass  # Ollama adapter not available

        if self._loop and not self._loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()

            # Allow cancelled tasks to complete
            if pending:
                self._loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )

            # Close the loop
            self._loop.close()
            self._loop = None

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run a coroutine in the persistent event loop.

        This replaces asyncio.run() to avoid creating/destroying loops.

        Args:
            coro: The coroutine to execute.

        Returns:
            The result of the coroutine.
        """
        if self._loop is None or self._loop.is_closed():
            self._initialize()

        # Use run_until_complete instead of asyncio.run()
        # This doesn't close the loop after completion
        return self._loop.run_until_complete(coro)  # type: ignore[union-attr]

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the current event loop.

        Returns:
            The persistent event loop.
        """
        if self._loop is None or self._loop.is_closed():
            self._initialize()
        return self._loop  # type: ignore[return-value]

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        if cls._instance and cls._instance._loop:
            if not cls._instance._loop.is_closed():
                cls._instance._loop.close()
        cls._instance = None
        cls._loop = None

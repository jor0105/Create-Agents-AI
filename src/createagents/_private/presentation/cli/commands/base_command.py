from abc import ABC, abstractmethod
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ....application.facade import CreateAgent
    from ..ui import TerminalRenderer


class CommandHandler(ABC):
    """Abstract base class for CLI command handlers.

    This interface follows:
    - ISP: Minimal interface with only necessary methods
    - DIP: High-level modules depend on this abstraction
    - OCP: New commands can be added without modifying existing code
    """

    def __init__(self, renderer: 'TerminalRenderer'):
        """Initialize the command handler.

        Args:
            renderer: The terminal renderer for output.
        """
        self._renderer = renderer

    @abstractmethod
    def can_handle(self, user_input: str) -> bool:
        """Check if this handler can process the given input.

        Args:
            user_input: The user's input string.

        Returns:
            True if this handler can process the input, False otherwise.
        """

    @abstractmethod
    def execute(self, agent: 'CreateAgent', user_input: str) -> Any:
        """Execute the command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.

        Returns:
            Command execution result (can vary by command).
        """

    @abstractmethod
    def get_aliases(self) -> List[str]:
        """Get the list of command aliases.

        Returns:
            List of command aliases (e.g., ['/help', 'help']).
        """

    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for comparison.

        Args:
            user_input: The raw user input.

        Returns:
            Normalized input (stripped and lowercased).
        """
        return user_input.strip().lower()

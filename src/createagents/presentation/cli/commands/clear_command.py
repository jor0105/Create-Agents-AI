from typing import List, TYPE_CHECKING

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class ClearCommandHandler(CommandHandler):
    """Handles the /clear command.

    Responsibility: Clear chat history.
    This follows SRP by handling only clear-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a clear command."""
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the clear command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.
        """
        agent.clear_history()
        self._renderer.render_success_message('🧹 Chat history cleared.')

    def get_aliases(self) -> List[str]:
        """Get clear command aliases."""
        return ['/clear', 'clear_history']

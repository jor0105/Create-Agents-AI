from typing import List, TYPE_CHECKING

from ....utils.text_sanitizer import TextSanitizer
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class HelpCommandHandler(CommandHandler):
    """Handles the /help command.

    Responsibility: Display help information to the user.
    This follows SRP by handling only help-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a help command."""
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the help command.

        Args:
            agent: The CreateAgent instance (not used for help).
            user_input: The user's input string.
        """
        help_text = """
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /trace    → View and manage execution traces (debugging)
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Trace Commands:
• /trace list             → List recent traces
• /trace show <trace_id>  → View trace details
• /trace export           → Export traces to file
• /trace clear            → Clear stored traces

Type 'exit' or 'quit' to close the application.
        """
        formatted_help = TextSanitizer.format_markdown_for_terminal(help_text)
        self._renderer.render_system_message(formatted_help)

    def get_aliases(self) -> List[str]:
        """Get help command aliases."""
        return ['/help', 'help']

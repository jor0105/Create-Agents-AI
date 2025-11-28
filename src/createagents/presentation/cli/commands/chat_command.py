from typing import List, TYPE_CHECKING

from ....utils.text_sanitizer import TextSanitizer
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class ChatCommandHandler(CommandHandler):
    """Handles regular chat messages (default handler).

    Responsibility: Process regular chat messages.
    This follows SRP by handling only chat-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """This handler accepts all non-empty inputs.

        Should be registered last in the command registry as it's the default.
        """
        return bool(user_input.strip())

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the chat command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.
        """
        # 1. Show User Message (Right aligned, Blue)
        self._renderer.render_user_message(user_input)
        self._renderer.render_spacer()
        # 2. Show AI Thinking
        self._renderer.render_thinking_indicator()
        # Get Response
        try:
            response = agent.chat(user_input)
            response = TextSanitizer.format_markdown_for_terminal(response)
        except Exception as e:
            response = f'Error: {str(e)}'
        # Clear thinking line
        self._renderer.clear_thinking_indicator()
        # 3. Show AI Message (Left aligned, Purple)
        self._renderer.render_ai_message(response)
        self._renderer.render_spacer()

    def get_aliases(self) -> List[str]:
        """Get chat command aliases.

        Returns empty list as this is the default handler.
        """
        return []

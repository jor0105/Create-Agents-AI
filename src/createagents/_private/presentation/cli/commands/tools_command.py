from typing import List, TYPE_CHECKING

from ..ui import render_markdown
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class ToolsCommandHandler(CommandHandler):
    """Handles the /tools command.

    Responsibility: Display available tools.
    This follows SRP by handling only tools-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a tools command."""
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the tools command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.
        """
        tools = agent.get_all_available_tools()
        tools_str = '## Available Tools\n\n'
        if not tools:
            tools_str += '_No tools configured for this agent._'
        else:
            for name, desc in tools.items():
                tools_str += f'**{name}**\n{desc}\n\n'
        formatted_tools = render_markdown(tools_str)
        self._renderer.render_system_message(formatted_tools)

    def get_aliases(self) -> List[str]:
        """Get tools command aliases."""
        return ['/tools', 'get_tools']

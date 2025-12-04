from typing import List, TYPE_CHECKING

from ..ui import render_markdown
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class ConfigsCommandHandler(CommandHandler):
    """Handles the /configs command.

    Responsibility: Display agent configurations.
    This follows SRP by handling only config-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a configs command."""
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the configs command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.
        """
        configs = agent.get_configs()
        config_str = '## Agent Configuration\n\n'
        for k, v in configs.items():
            if k == 'history' and isinstance(v, list):
                config_str += f'**{k}:** {len(v)} messages in history\n\n'
                for msg in v:
                    role = msg.get('role', 'unknown')
                    content = str(msg.get('content', ''))
                    # Create a preview of the content
                    preview = (
                        (content[:50] + '...')
                        if len(content) > 50
                        else content
                    )
                    preview = preview.replace('\n', ' ')
                    # Use indented bullets for better visual hierarchy
                    config_str += f'  - **{role}**: {preview}\n'
                config_str += '\n'
            else:
                config_str += f'**{k}:** {v}\n'
        formatted_config = render_markdown(config_str)
        self._renderer.render_system_message(formatted_config)

    def get_aliases(self) -> List[str]:
        """Get configs command aliases."""
        return ['/configs', 'get_configs']

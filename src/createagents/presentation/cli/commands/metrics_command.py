from typing import List, TYPE_CHECKING

from ....utils.text_sanitizer import TextSanitizer
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent


class MetricsCommandHandler(CommandHandler):
    """Handles the /metrics command.

    Responsibility: Display agent performance metrics.
    This follows SRP by handling only metrics-related functionality.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a metrics command."""
        normalized = self._normalize_input(user_input)
        return normalized in self.get_aliases()

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the metrics command.

        Args:
            agent: The CreateAgent instance.
            user_input: The user's input string.
        """
        metrics = agent.get_metrics()
        if not metrics:
            self._renderer.render_system_message(
                'No metrics available yet. Start chatting to collect data!'
            )
            return
        # Format metrics nicely
        metrics_str = '## Performance Metrics\n\n'
        metrics_str += '| Model | Duration | Tokens (In/Out/Total) |\n'
        metrics_str += '|-------|----------|-----------------------|\n'
        for m in metrics:
            duration_s = m.latency_ms / 1000 if m.latency_ms else 0
            metrics_str += (
                f'| {m.model} | {duration_s:.2f}s | '
                f'{m.prompt_tokens} / {m.completion_tokens} / {m.tokens_used} |\n'
            )
        formatted_metrics = TextSanitizer.format_markdown_for_terminal(
            metrics_str
        )
        self._renderer.render_system_message(formatted_metrics)

    def get_aliases(self) -> List[str]:
        """Get metrics command aliases."""
        return ['/metrics', 'get_metrics']

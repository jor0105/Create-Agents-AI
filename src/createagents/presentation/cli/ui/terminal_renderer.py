import sys

from .color_scheme import ColorScheme
from .terminal_formatter import TerminalFormatter


class TerminalRenderer:
    """Handles rendering of visual components to the terminal.

    Responsibility: Render UI components to the terminal.
    This follows SRP by focusing solely on rendering operations.
    """

    def __init__(self):
        """Initialize the terminal renderer."""
        self._formatter = TerminalFormatter()

    def render_welcome_screen(self) -> None:
        """Render the welcome screen with system information."""
        self.clear_screen()
        print(f'{ColorScheme.GRAY}Initializing System...{ColorScheme.RESET}')
        print(
            f'\n{ColorScheme.BOLD}✨ AI Chat System Ready.{ColorScheme.RESET} '
            f"{ColorScheme.GRAY}Type 'exit' to quit.{ColorScheme.RESET}"
        )
        print(
            f'{ColorScheme.GRAY}Available commands: '
            f'/metrics, /configs, /tools, /clear, /help{ColorScheme.RESET}\n'
        )

    def render_message_box(
        self, message: str, color: str, align: str = 'left'
    ) -> None:
        """Render a message inside a rounded box.

        Args:
            message: The message to display.
            color: ANSI color code for the box.
            align: Alignment ('left' or 'right').
        """
        box = self._formatter.format_rounded_box(message, color, align)
        print(box)

    def render_user_message(self, message: str) -> None:
        """Render a user message (right-aligned, blue).

        Args:
            message: The user's message.
        """
        self.render_message_box(
            message, ColorScheme.get_user_color(), align='right'
        )

    def render_ai_message(self, message: str) -> None:
        """Render an AI message (left-aligned, purple).

        Args:
            message: The AI's message.
        """
        self.render_message_box(
            message, ColorScheme.get_ai_color(), align='left'
        )

    async def render_ai_message_streaming(self, token_generator) -> None:
        """Renders AI message tokens in real-time inside purple box.

        Args:
            token_generator: AsyncGenerator that yields tokens as strings.
        """
        from rich.live import Live  # pylint: disable=import-outside-toplevel
        from rich.text import Text  # pylint: disable=import-outside-toplevel
        from rich.panel import Panel  # pylint: disable=import-outside-toplevel
        from rich import box  # pylint: disable=import-outside-toplevel
        from rich.console import Console  # pylint: disable=import-outside-toplevel

        # Initialize console if not already done (assuming it's not part of __init__ yet)
        if not hasattr(self, '_console'):
            self._console = Console()

        # Wait for the first token before creating the panel
        # This keeps "AI thinking..." visible until AI actually starts responding
        full_response = ''
        first_token_received = False

        async for token in token_generator:
            # On first token: clear thinking indicator and start the Live display
            if not first_token_received:
                self.clear_thinking_indicator()
                first_token_received = True
                full_response = token

                # Create initial panel with first token
                text = Text(full_response)
                panel = Panel(
                    text,
                    style='bold purple',
                    box=box.ROUNDED,
                    padding=(0, 1),
                    expand=False,
                )

                # Start Live display and continue with remaining tokens
                with Live(
                    panel, console=self._console, refresh_per_second=20
                ) as live:
                    # Continue consuming remaining tokens
                    async for next_token in token_generator:
                        full_response += next_token
                        # Update the text and panel
                        text = Text(full_response)
                        panel = Panel(
                            text,
                            style='bold purple',
                            box=box.ROUNDED,
                            padding=(0, 1),
                            expand=False,
                        )
                        live.update(panel)
                break  # Exit outer loop after Live context completes

    def render_system_message(self, message: str) -> None:
        """Render a system message (left-aligned, yellow).

        Args:
            message: The system message.
        """
        self.render_message_box(
            message, ColorScheme.get_system_color(), align='left'
        )

    def render_success_message(self, message: str) -> None:
        """Render a success message (left-aligned, green).

        Args:
            message: The success message.
        """
        self.render_message_box(
            message, ColorScheme.get_success_color(), align='left'
        )

    def render_thinking_indicator(self) -> None:
        """Display 'AI is thinking...' indicator."""
        print(
            f'{ColorScheme.ITALIC}{ColorScheme.GRAY}'
            f'AI is thinking...{ColorScheme.RESET}',
            end='\r',
        )
        sys.stdout.flush()

    def clear_thinking_indicator(self) -> None:
        """Clear the thinking indicator line."""
        sys.stdout.write(ColorScheme.CLEAR_LINE)
        sys.stdout.flush()

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        print(ColorScheme.CLEAR_SCREEN, end='')
        sys.stdout.flush()

    def clear_input_lines(self, num_lines: int = 2) -> None:
        """Clear the specified number of lines above cursor.

        Args:
            num_lines: Number of lines to clear.
        """
        for _ in range(num_lines):
            sys.stdout.write(ColorScheme.MOVE_UP)
            sys.stdout.write(ColorScheme.CLEAR_LINE)
        sys.stdout.flush()

    def render_prompt(self, prompt: str = 'Type your message...') -> None:
        """Render the input prompt.

        Args:
            prompt: The prompt message to display.
        """
        print(f'{ColorScheme.GRAY}{prompt}{ColorScheme.RESET}')

    def render_input_indicator(self) -> None:
        """Render the input indicator (>)."""
        print(f'{ColorScheme.BOLD}> {ColorScheme.RESET}', end='')

    def render_spacer(self) -> None:
        """Render a blank line spacer."""
        print()

    def render_goodbye(self) -> None:
        """Render goodbye message."""
        print(f'\n{ColorScheme.GRAY}Goodbye!{ColorScheme.RESET}')

    def render_error(self, error_message: str) -> None:
        """Render an error message.

        Args:
            error_message: The error message to display.
        """
        print(f'\n{ColorScheme.BOLD}Error:{ColorScheme.RESET} {error_message}')

    def render_interrupt(self) -> None:
        """Render session interrupted message."""
        print(f'\n{ColorScheme.GRAY}Session interrupted.{ColorScheme.RESET}')

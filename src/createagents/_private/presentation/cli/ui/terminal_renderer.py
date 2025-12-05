import sys
from datetime import datetime

from .color_scheme import ColorScheme
from .terminal_formatter import TerminalFormatter


class TerminalRenderer:
    """Handles rendering of visual components to the terminal.

    Responsibility: Render UI components to the terminal.
    This follows SRP by focusing solely on rendering operations.
    """

    def __init__(self, show_timestamps: bool = False):
        """Initialize the terminal renderer.

        Args:
            show_timestamps: Whether to display timestamps in messages.
        """
        self._formatter = TerminalFormatter()
        self._show_timestamps = show_timestamps

    def _get_timestamp(self) -> str:
        """Get formatted timestamp for messages.

        Returns:
            Formatted timestamp string or empty if disabled.
        """
        if not self._show_timestamps:
            return ''
        now = datetime.now()
        return f'{ColorScheme.get_timestamp_color()}{now.strftime("%H:%M")}{ColorScheme.RESET} '

    def render_welcome_screen(self) -> None:
        """Render the welcome screen with modern ASCII banner."""
        self.clear_screen()

        # Modern, minimal ASCII banner
        banner = f"""{ColorScheme.PURPLE}{ColorScheme.BOLD}
    ╔═══════════════════════════════════════╗
    ║     🤖  AI CHAT SYSTEM  ✨            ║
    ║     Enterprise Agent Framework        ║
    ╚═══════════════════════════════════════╝{ColorScheme.RESET}
"""
        print(banner)

        # Welcome message with icons
        print(
            f'{ColorScheme.GREEN}●{ColorScheme.RESET} '
            f'{ColorScheme.BOLD}System Ready{ColorScheme.RESET} '
            f'{ColorScheme.GRAY}• Type your message to begin{ColorScheme.RESET}'
        )

        # Commands help with better formatting
        print(
            f'\n{ColorScheme.DARK_GRAY}┌─ Available Commands{ColorScheme.RESET}\n'
            f'{ColorScheme.DARK_GRAY}│{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/help{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/metrics{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/configs{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/tools{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/trace{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}/clear{ColorScheme.RESET} '
            f'{ColorScheme.CYAN}exit{ColorScheme.RESET}\n'
            f'{ColorScheme.DARK_GRAY}└{"─" * 45}{ColorScheme.RESET}\n'
        )

    def render_message_box(
        self, message: str, color: str, align: str = 'left', icon: str = ''
    ) -> None:
        """Render a message inside a rounded box.

        Args:
            message: The message to display.
            color: ANSI color code for the box.
            align: Alignment ('left' or 'right').
            icon: Optional icon to display before message.
        """
        timestamp = self._get_timestamp()
        box = self._formatter.format_rounded_box(
            message, color, align, icon, timestamp
        )
        print(box)

    def render_user_message(self, message: str) -> None:
        """Render a user message (right-aligned, blue).

        Args:
            message: The user's message.
        """
        self.render_message_box(
            message, ColorScheme.get_user_color(), align='right', icon='👤'
        )

    def render_ai_message(self, message: str) -> None:
        """Render an AI message (left-aligned, purple).

        Args:
            message: The AI's message.
        """
        self.render_message_box(
            message, ColorScheme.get_ai_color(), align='left', icon='🤖'
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
        """Render a system message (left-aligned, cyan).

        Args:
            message: The system message.
        """
        self.render_message_box(
            message, ColorScheme.get_system_color(), align='left', icon='ℹ️'
        )

    def render_success_message(self, message: str) -> None:
        """Render a success message (left-aligned, green).

        Args:
            message: The success message.
        """
        self.render_message_box(
            message, ColorScheme.get_success_color(), align='left', icon='✓'
        )

    def render_thinking_indicator(self) -> None:
        """Display 'AI is thinking...' indicator with animation effect."""
        print(
            f'{ColorScheme.DIM}{ColorScheme.PURPLE}'
            f'🤖 AI is thinking...{ColorScheme.RESET}',
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

    def render_prompt(self, prompt: str = '💬 Your message') -> None:
        """Render the input prompt.

        Args:
            prompt: The prompt message to display.
        """
        print(f'{ColorScheme.GRAY}{prompt}{ColorScheme.RESET}')

    def render_input_indicator(self) -> None:
        """Render the input indicator with modern arrow."""
        print(
            f'{ColorScheme.BLUE}{ColorScheme.BOLD}▶ {ColorScheme.RESET}',
            end='',
        )

    def render_spacer(self) -> None:
        """Render a subtle separator line."""
        print(f'{ColorScheme.DARK_GRAY}{"─" * 50}{ColorScheme.RESET}')

    def render_goodbye(self) -> None:
        """Render goodbye message with icon."""
        print(
            f'\n{ColorScheme.PURPLE}👋 Goodbye! Thanks for using AI Chat System.{ColorScheme.RESET}'
        )

    def render_error(self, error_message: str) -> None:
        """Render an error message with icon and formatting.

        Args:
            error_message: The error message to display.
        """
        print(
            f'\n{ColorScheme.get_error_color()}{ColorScheme.BOLD}✗ Error:{ColorScheme.RESET} '
            f'{ColorScheme.get_error_color()}{error_message}{ColorScheme.RESET}'
        )

    def render_interrupt(self) -> None:
        """Render session interrupted message."""
        print(
            f'\n{ColorScheme.YELLOW}⚠ Session interrupted.{ColorScheme.RESET}'
        )

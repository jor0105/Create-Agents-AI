import re
import shutil
import textwrap
import unicodedata
from typing import List

from .color_scheme import ColorScheme


class TerminalFormatter:
    """Handles terminal text formatting and display width calculations.

    Responsibility: Format text for terminal display with proper width handling.
    This follows SRP by focusing solely on text formatting operations.
    """

    @staticmethod
    def get_display_width(text: str) -> int:
        """Calculate the visual display width of a string in the terminal.

        East Asian Wide (W) and Fullwidth (F) characters count as 2.
        Ignores ANSI escape codes.

        Args:
            text: The text to measure.

        Returns:
            The visual width of the text in terminal columns.
        """
        # Strip ANSI codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text_without_ansi = ansi_escape.sub('', text)
        width = 0
        for char in text_without_ansi:
            if unicodedata.east_asian_width(char) in ('W', 'F'):
                width += 2
            else:
                width += 1
        return width

    @staticmethod
    def get_terminal_width() -> int:
        """Get the current terminal width.

        Returns:
            Terminal width in columns, defaults to 100 if unable to determine.
        """
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 100

    @staticmethod
    def wrap_text(
        text: str, max_width: int, subsequent_indent: str = ''
    ) -> List[str]:
        """Wrap text to fit within specified width.

        Args:
            text: The text to wrap.
            max_width: Maximum width for each line.
            subsequent_indent: Indent for wrapped lines.

        Returns:
            List of wrapped text lines.
        """
        if not text.strip():
            return ['']
        # Ensure minimum width to prevent excessive wrapping
        effective_width = max(max_width, 40)
        return textwrap.wrap(
            text,
            width=effective_width,
            subsequent_indent=subsequent_indent,
            break_long_words=True,  # Allow breaking very long words
            break_on_hyphens=False,  # But don't break on hyphens
        )

    @staticmethod
    def format_rounded_box(text: str, color: str, align: str = 'left') -> str:
        """Format text inside a rounded box with specified color and alignment.

        Simulates a modern chat bubble.

        Args:
            text: The text to display in the box.
            color: ANSI color code for the box.
            align: Alignment ('left' or 'right').

        Returns:
            Formatted text with rounded box borders.
        """
        terminal_width = TerminalFormatter.get_terminal_width()
        max_content_width = min(100, terminal_width - 10)
        wrapped_lines = []
        for line in text.split('\n'):
            # Handle empty lines
            if not line.strip():
                wrapped_lines.append('')
                continue
            # Detect list indentation for nicer wrapping
            subsequent_indent = ''
            # Check for bullet points (TextSanitizer uses "  • ", "  → ", "  ▪ ")
            match = re.match(r'^(\s*[•→▪]\s+)', line)
            if match:
                prefix_len = len(match.group(1))
                subsequent_indent = ' ' * prefix_len
            wrapped_lines.extend(
                TerminalFormatter.wrap_text(
                    line,
                    max_width=max_content_width,
                    subsequent_indent=subsequent_indent,
                )
            )
        if not wrapped_lines:
            wrapped_lines = ['...']
        # Calculate box dimensions using display width
        content_width = max(
            TerminalFormatter.get_display_width(line) for line in wrapped_lines
        )
        box_width = content_width + 2  # +2 for padding
        # Box drawing characters (Rounded)
        TL, TR = '╭', '╮'
        BL, BR = '╰', '╯'
        H, V = '─', '│'
        # Calculate indentation for alignment
        if align == 'right':
            indent = ' ' * (terminal_width - box_width - 2)
        else:
            indent = ''
        # Build the box
        lines = []
        # Draw Top
        lines.append(
            f'{indent}{color}{TL}{H * box_width}{TR}{ColorScheme.RESET}'
        )
        # Draw Content
        for line in wrapped_lines:
            # Pad the line to fill the box using display width
            padding = ' ' * (
                content_width - TerminalFormatter.get_display_width(line)
            )
            # Re-apply color for the right border in case line reset it
            lines.append(
                f'{indent}{color}{V} {line}{padding} {color}{V}{ColorScheme.RESET}'
            )
        # Draw Bottom
        lines.append(
            f'{indent}{color}{BL}{H * box_width}{BR}{ColorScheme.RESET}'
        )
        return '\n'.join(lines)

    @staticmethod
    def create_list_indent(line: str) -> str:
        """Create appropriate indent for list items.

        Args:
            line: The line to analyze.

        Returns:
            Indent string for subsequent lines.
        """
        match = re.match(r'^(\s*[•→▪]\s+)', line)
        if match:
            return ' ' * len(match.group(1))
        return ''

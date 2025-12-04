import re
from typing import List

from .color_scheme import ColorScheme


class MarkdownRenderer:
    """Renders Markdown text for terminal display with ANSI styling.

    Responsibility: Convert Markdown elements into styled terminal text.
    This follows SRP by focusing solely on terminal Markdown rendering.
    """

    def __init__(self, max_line_width: int = 70) -> None:
        self._max_line_width = max_line_width

    def render(self, text: str) -> str:
        """Render Markdown text for terminal display.

        Converts Markdown elements into styled terminal text with ANSI codes.

        Args:
            text: The Markdown text to render.

        Returns:
            Terminal-formatted text with ANSI styling.
        """
        if not isinstance(text, str):
            return text

        text = self._remove_html_tags(text)
        text = self._render_headers(text)
        text = self._render_text_styles(text)
        text = self._render_lists(text)
        text = self._render_horizontal_rules(text)
        text = self._render_tables(text)
        text = self._normalize_whitespace(text)

        return text

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        text = re.sub(r'<br\s*/?>\s*', '\n', text, flags=re.IGNORECASE)
        return re.sub(r'<[^>]+>', '', text)

    def _render_headers(self, text: str) -> str:
        """Convert Markdown headers to styled terminal text."""
        patterns = [
            (r'^######\s+(.+)$', rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}'),
            (r'^#####\s+(.+)$', rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}'),
            (r'^####\s+(.+)$', rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}'),
            (r'^###\s+(.+)$', rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}'),
            (r'^##\s+(.+)$', rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}'),
            (
                r'^#\s+(.+)$',
                rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}\n'
                rf'{ColorScheme.DARK_GRAY}{"─" * 50}{ColorScheme.RESET}',
            ),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)

        return text

    def _render_text_styles(self, text: str) -> str:
        """Convert bold and italic Markdown to ANSI styles."""
        # Bold: **text** or __text__
        text = re.sub(
            r'\*\*(.+?)\*\*',
            rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
        )
        text = re.sub(
            r'__(.+?)__',
            rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
        )

        # Italic: *text* or _text_ (not preceded/followed by same char)
        text = re.sub(
            r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)',
            rf'{ColorScheme.ITALIC}\1{ColorScheme.RESET}',
            text,
        )
        text = re.sub(
            r'(?<!_)_(?!_)(.+?)_(?!_)',
            rf'{ColorScheme.ITALIC}\1{ColorScheme.RESET}',
            text,
        )

        return text

    def _render_lists(self, text: str) -> str:
        """Convert Markdown lists to styled bullets."""
        # Unordered lists
        text = re.sub(
            r'^(\s*)[-*+]\s+',
            rf'\1{ColorScheme.GREEN}•{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        # Ordered lists
        text = re.sub(
            r'^(\s*)\d+\.\s+',
            rf'\1{ColorScheme.BLUE}→{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        return text

    def _render_horizontal_rules(self, text: str) -> str:
        """Convert Markdown horizontal rules to styled separators."""
        return re.sub(
            r'^[\-\*_]{3,}\s*$',
            rf'{ColorScheme.DARK_GRAY}{"─" * 60}{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )

    def _render_tables(self, text: str) -> str:
        """Convert Markdown tables to formatted terminal output."""
        lines = text.split('\n')
        formatted_lines: List[str] = []
        in_table = False

        for line in lines:
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    formatted_lines.append(
                        f'\n{ColorScheme.DARK_GRAY}{"─" * self._max_line_width}{ColorScheme.RESET}'
                    )

                cells = [cell.strip() for cell in line.split('|') if cell.strip()]

                # Skip separator lines (|---|---|)
                if all(re.match(r'^[\-:]+$', cell) for cell in cells):
                    continue

                formatted_lines.extend(self._format_table_row(cells))
            else:
                if in_table:
                    formatted_lines.append(
                        f'{ColorScheme.DARK_GRAY}{"─" * self._max_line_width}{ColorScheme.RESET}\n'
                    )
                    in_table = False
                formatted_lines.append(line)

        if in_table:
            formatted_lines.append(
                f'{ColorScheme.DARK_GRAY}{"─" * self._max_line_width}{ColorScheme.RESET}'
            )

        return '\n'.join(formatted_lines)

    def _format_table_row(self, cells: List[str]) -> List[str]:
        """Format a table row based on column count."""
        result: List[str] = []

        if len(cells) == 2:
            # Two-column: format as label-value pairs
            label, value = cells[0], cells[1]
            result.append(
                f'  {ColorScheme.CYAN}▪{ColorScheme.RESET} '
                f'{ColorScheme.BOLD}{label}{ColorScheme.RESET}'
            )

            if len(value) > self._max_line_width - 6:
                for wrapped_line in self._wrap_text(value, self._max_line_width - 6):
                    result.append(f'    {wrapped_line}')
            else:
                result.append(f'    {value}')
            result.append('')
        else:
            # Multi-column: join with separators
            formatted_line = f' {ColorScheme.DARK_GRAY}│{ColorScheme.RESET} '.join(
                str(cell) for cell in cells
            )
            result.append(f'  {formatted_line}')

        return result

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines: List[str] = []
        current_line: List[str] = []
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) > width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _normalize_whitespace(self, text: str) -> str:
        """Remove excessive blank lines and trailing spaces."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        return re.sub(r' +$', '', text, flags=re.MULTILINE)


# Module-level instance for convenience
_default_renderer = MarkdownRenderer()


def render_markdown(text: str) -> str:
    """Render Markdown text for terminal display.

    Convenience function using the default renderer instance.

    Args:
        text: The Markdown text to render.

    Returns:
        Terminal-formatted text with ANSI styling.
    """
    return _default_renderer.render(text)

import re
import unicodedata
from typing import List


class TextSanitizer:
    """
    A utility class for sanitizing and formatting text.

    This class provides methods to clean text by removing problematic unicode
    characters and to format markdown text for better readability in a
    terminal environment.
    """

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Sanitizes the input text by removing problematic unicode characters
        and normalizing it.

        Args:
            text (str): The input text to be sanitized.

        Returns:
            str: The sanitized text with problematic characters removed or
                 replaced, and unicode normalized to NFKC form.
        """
        if not isinstance(text, str):
            return text

        # Remove specific problematic unicode characters
        problematic_chars = {
            '\u202f': ' ',  # Narrow no-break space → regular space
            '\u00a0': ' ',  # Non-breaking space → regular space
            '\u2011': '-',  # Non-breaking hyphen → regular hyphen '-'
            '\u2009': ' ',  # Thin space → regular space
            '\u200b': '',  # Zero-width space → remove
            '\u200c': '',  # Zero-width non-joiner → remove
            '\u200d': '',  # Zero-width joiner → remove
        }

        for char, replacement in problematic_chars.items():
            text = text.replace(char, replacement)

        # Normalize unicode to decomposed form (NFKC) for consistency
        text = unicodedata.normalize('NFKC', text)

        # Remove any control characters (category Cc)
        # This includes various invisible formatting characters
        # text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

        return text

    @staticmethod
    def format_markdown_for_terminal(text: str) -> str:
        """
        Format Markdown text for better readability in the terminal.
        Convert Markdown elements into styled terminal text with ANSI codes.
        """
        if not isinstance(text, str):
            return text

        # First, sanitize problematic unicode characters
        text = TextSanitizer.sanitize(text)

        # Remove HTML <br> tags and replace with newlines
        text = re.sub(r'<br\s*/?>\s*', '\n', text, flags=re.IGNORECASE)

        # Remove other common HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Import ColorScheme for styling
        from ..presentation.cli.ui.color_scheme import ColorScheme  # pylint: disable=import-outside-toplevel

        # Convert headers with colors and better formatting
        text = re.sub(
            r'^######\s+(.+)$',
            rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^#####\s+(.+)$',
            rf'{ColorScheme.CYAN}{ColorScheme.BOLD}\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^####\s+(.+)$',
            rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^###\s+(.+)$',
            rf'{ColorScheme.PURPLE}{ColorScheme.BOLD}▌\1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^##\s+(.+)$',
            rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r'^#\s+(.+)$',
            rf'\n{ColorScheme.BLUE}{ColorScheme.BOLD}▐ \1{ColorScheme.RESET}\n{ColorScheme.DARK_GRAY}{"─" * 50}{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )

        # Convert bold formatting (**text** or __text__) to ANSI bold
        text = re.sub(
            r'\*\*(.+?)\*\*', rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}', text
        )
        text = re.sub(
            r'__(.+?)__', rf'{ColorScheme.BOLD}\1{ColorScheme.RESET}', text
        )

        # Convert italic formatting (*text* or _text_) to ANSI italic
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

        # Convert unordered lists with colored bullets
        text = re.sub(
            r'^(\s*)[-*+]\s+',
            rf'\1{ColorScheme.GREEN}•{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        # Convert ordered lists with colored arrows
        text = re.sub(
            r'^(\s*)\d+\.\s+',
            rf'\1{ColorScheme.BLUE}→{ColorScheme.RESET} ',
            text,
            flags=re.MULTILINE,
        )

        # Convert markdown horizontal rules to styled separators
        text = re.sub(
            r'^[\-\*_]{3,}\s*$',
            rf'{ColorScheme.DARK_GRAY}{"─" * 60}{ColorScheme.RESET}',
            text,
            flags=re.MULTILINE,
        )

        # Convert simple tables (just remove pipes and adjust)
        # Detect table lines (|...|...|)
        lines = text.split('\n')
        formatted_lines = []
        in_table = False
        max_line_width = 70

        for _, line in enumerate(lines):
            # Detect if this is a table line
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    formatted_lines.append(
                        f'\n{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}'
                    )

                # Remove pipes and format cells
                cells = [cell.strip() for cell in line.split('|')]
                cells = [cell for cell in cells if cell]  # Remove empty cells

                # Check if it's a separator line (|---|---|)
                if all(re.match(r'^[\-:]+$', cell) for cell in cells):
                    continue  # Skip separator lines

                # Format table row with better readability
                if len(cells) == 2:
                    # Two-column table: format as label-value pairs
                    label, value = cells[0], cells[1]
                    formatted_lines.append(
                        f'  {ColorScheme.CYAN}▪{ColorScheme.RESET} '
                        f'{ColorScheme.BOLD}{label}{ColorScheme.RESET}'
                    )

                    # Wrap long values to fit terminal width
                    if len(value) > max_line_width - 6:
                        wrapped_lines = TextSanitizer._wrap_text(
                            value, max_line_width - 6
                        )
                        for wrapped_line in wrapped_lines:
                            formatted_lines.append(f'    {wrapped_line}')
                    else:
                        formatted_lines.append(f'    {value}')
                    formatted_lines.append('')  # Add blank line between rows
                else:
                    # Multi-column table: join with separators
                    formatted_line = (
                        f' {ColorScheme.DARK_GRAY}│{ColorScheme.RESET} '.join(
                            str(cell) for cell in cells
                        )
                    )
                    formatted_lines.append(f'  {formatted_line}')
            else:
                if in_table:
                    formatted_lines.append(
                        f'{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}\n'
                    )
                    in_table = False
                formatted_lines.append(line)

        if in_table:
            formatted_lines.append(
                f'{ColorScheme.DARK_GRAY}{"─" * max_line_width}{ColorScheme.RESET}'
            )

        text = '\n'.join(formatted_lines)

        # Remove consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing spaces on lines
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)

        return text

    @staticmethod
    def _wrap_text(text: str, width: int) -> List[str]:
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

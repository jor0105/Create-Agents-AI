import re
import unicodedata
from typing import List


class TextSanitizer:
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

    @staticmethod
    def sanitize(text: str) -> str:
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
        Remove or convert Markdown elements into more readable plain text.
        """
        if not isinstance(text, str):
            return text

        # First, sanitize problematic unicode characters
        text = TextSanitizer.sanitize(text)

        # Remove HTML <br> tags and replace with newlines
        text = re.sub(r'<br\s*/?>\s*', '\n', text, flags=re.IGNORECASE)

        # Remove other common HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Convert headers (#, ##, ###) into visually highlighted text
        text = re.sub(
            r'^######\s+(.+)$', r'━━ \1 ━━', text, flags=re.MULTILINE
        )
        text = re.sub(r'^#####\s+(.+)$', r'━━ \1 ━━', text, flags=re.MULTILINE)
        text = re.sub(
            r'^####\s+(.+)$', r'━━━ \1 ━━━', text, flags=re.MULTILINE
        )
        text = re.sub(r'^###\s+(.+)$', r'━━━ \1 ━━━', text, flags=re.MULTILINE)
        text = re.sub(
            r'^##\s+(.+)$', r'\n═══ \1 ═══', text, flags=re.MULTILINE
        )
        text = re.sub(
            r'^#\s+(.+)$', r'\n═══════ \1 ═══════', text, flags=re.MULTILINE
        )

        # Remove bold formatting (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)

        # Remove italic formatting (*text* or _text_)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_(?!_)(.+?)_(?!_)', r'\1', text)

        # Convert unordered lists
        text = re.sub(r'^\s*[-*+]\s+', r'  • ', text, flags=re.MULTILINE)

        # Convert ordered lists
        text = re.sub(r'^\s*\d+\.\s+', r'  → ', text, flags=re.MULTILINE)

        # Remove markdown horizontal rules (---, ***, ___)
        text = re.sub(r'^[\-\*_]{3,}\s*$', r'─' * 80, text, flags=re.MULTILINE)

        # Convert simple tables (just remove pipes and adjust)
        # Detect table lines (|...|...|)
        lines = text.split('\n')
        formatted_lines = []
        in_table = False
        max_line_width = 80

        for i, line in enumerate(lines):
            # Detect if this is a table line
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    formatted_lines.append('\n' + '─' * max_line_width)

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
                    formatted_lines.append(f'  ▪ {label}')

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
                    formatted_line = ' │ '.join(str(cell) for cell in cells)
                    formatted_lines.append(f'  {formatted_line}')
            else:
                if in_table:
                    formatted_lines.append('─' * max_line_width + '\n')
                    in_table = False
                formatted_lines.append(line)

        if in_table:
            formatted_lines.append('─' * max_line_width)

        text = '\n'.join(formatted_lines)

        # Remove consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing spaces on lines
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)

        return text

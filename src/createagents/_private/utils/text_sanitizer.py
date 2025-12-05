import unicodedata
from typing import Dict

# Mapping of problematic unicode characters to their safe replacements
_PROBLEMATIC_CHARS: Dict[str, str] = {
    '\u202f': ' ',  # Narrow no-break space → regular space
    '\u00a0': ' ',  # Non-breaking space → regular space
    '\u2011': '-',  # Non-breaking hyphen → regular hyphen
    '\u2009': ' ',  # Thin space → regular space
    '\u200b': '',  # Zero-width space → remove
    '\u200c': '',  # Zero-width non-joiner → remove
    '\u200d': '',  # Zero-width joiner → remove
    '\ufeff': '',  # Byte order mark → remove
    '\u2028': '\n',  # Line separator → newline
    '\u2029': '\n',  # Paragraph separator → newline
}


class TextSanitizer:
    """Utility for sanitizing text by removing problematic unicode characters.

    Responsibility: Clean and normalize text for safe processing.
    This follows SRP by focusing solely on text sanitization operations.
    """

    @staticmethod
    def sanitize(text: str) -> str:
        """Sanitize text by removing problematic unicode characters.

        Removes or replaces problematic unicode characters and normalizes
        the text to NFKC form for consistency.

        Args:
            text: The input text to sanitize.

        Returns:
            Sanitized text with problematic characters handled.
        """
        if not isinstance(text, str):
            return text

        for char, replacement in _PROBLEMATIC_CHARS.items():
            text = text.replace(char, replacement)

        return unicodedata.normalize('NFKC', text)

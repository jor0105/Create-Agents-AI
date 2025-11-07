import unicodedata


class TextSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        if not isinstance(text, str):
            return text

        # Remove specific problematic unicode characters
        # U+202F: Narrow no-break space
        # U+00A0: Non-breaking space
        # U+2011: Non-breaking hyphen
        # U+2009: Thin space
        # U+200B: Zero-width space
        # U+200C: Zero-width non-joiner
        # U+200D: Zero-width joiner
        problematic_chars = {
            "\u202f": " ",  # Narrow no-break space → regular space
            "\u00a0": " ",  # Non-breaking space → regular space
            "\u2011": "",  # Non-breaking hyphen → remove (will be replaced by normal hyphen below)
            "\u2009": " ",  # Thin space → regular space
            "\u200b": "",  # Zero-width space → remove
            "\u200c": "",  # Zero-width non-joiner → remove
            "\u200d": "",  # Zero-width joiner → remove
        }

        for char, replacement in problematic_chars.items():
            text = text.replace(char, replacement)

        # Normalize unicode to decomposed form (NFKC) for consistency
        text = unicodedata.normalize("NFKC", text)

        # Remove any control characters (category Cc)
        # This includes various invisible formatting characters
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

        # Clean up extra spaces created during replacement
        # Replace multiple consecutive spaces with a single space
        while "  " in text:
            text = text.replace("  ", " ")

        return text.strip()

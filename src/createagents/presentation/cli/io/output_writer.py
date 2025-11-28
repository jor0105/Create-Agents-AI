import sys


class OutputWriter:
    """Handles terminal output writing.

    Responsibility: Write output to terminal.
    This follows SRP by focusing solely on output operations.
    """

    def write(self, text: str) -> None:
        """Write text to terminal.

        Args:
            text: The text to write.
        """
        print(text)

    def write_line(self, text: str = '') -> None:
        """Write a line of text to terminal.

        Args:
            text: The text to write (optional).
        """
        print(text)

    def write_inline(self, text: str) -> None:
        """Write text without newline.

        Args:
            text: The text to write.
        """
        print(text, end='')
        sys.stdout.flush()

    def flush(self) -> None:
        """Flush the output buffer."""
        sys.stdout.flush()

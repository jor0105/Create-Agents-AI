class InputReader:
    """Handles user input reading from the terminal.

    Responsibility: Read and sanitize user input.
    This follows SRP by focusing solely on input operations.
    """

    def read_user_input(self, prompt: str = '> ') -> str:
        """Read and return user input.

        Args:
            prompt: The prompt to display before reading input.

        Returns:
            The user's input as a string.
        """
        return input(prompt)

    def read_line(self) -> str:
        """Read a single line of input.

        Returns:
            The input line as a string.
        """
        return input()

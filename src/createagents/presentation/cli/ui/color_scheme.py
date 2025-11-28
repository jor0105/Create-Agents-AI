class ColorScheme:
    """Manages ANSI color codes for terminal output.

    Responsibility: Centralize all color definitions in one place.
    This follows SRP by having a single reason to change: updating color scheme.
    """

    # Colors
    BLUE: str = '\033[38;5;39m'  # Bright Blue
    PURPLE: str = '\033[38;5;135m'  # Lavender/Purple
    GREEN: str = '\033[38;5;82m'  # Bright Green
    YELLOW: str = '\033[38;5;226m'  # Bright Yellow
    GRAY: str = '\033[90m'

    # Styles
    RESET: str = '\033[0m'
    BOLD: str = '\033[1m'
    ITALIC: str = '\033[3m'

    # Control sequences
    CLEAR_SCREEN: str = '\033[2J\033[H'
    CLEAR_LINE: str = '\033[K'
    MOVE_UP: str = '\033[F'

    @classmethod
    def get_user_color(cls) -> str:
        """Get color for user messages."""
        return cls.BLUE

    @classmethod
    def get_ai_color(cls) -> str:
        """Get color for AI messages."""
        return cls.PURPLE

    @classmethod
    def get_system_color(cls) -> str:
        """Get color for system messages."""
        return cls.YELLOW

    @classmethod
    def get_success_color(cls) -> str:
        """Get color for success messages."""
        return cls.GREEN

    @classmethod
    def get_info_color(cls) -> str:
        """Get color for info messages."""
        return cls.GRAY

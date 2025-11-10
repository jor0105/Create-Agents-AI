from typing import TYPE_CHECKING

from .Ollama import OllamaChatAdapter
from .OpenAI import ClientOpenAI, OpenAIChatAdapter
from .Tools import CurrentDateTool

if TYPE_CHECKING:
    from .Tools import ReadLocalFileTool

__all__ = [
    "OllamaChatAdapter",
    "OpenAIChatAdapter",
    "ClientOpenAI",
    # tools
    "ReadLocalFileTool",
    "CurrentDateTool",
]


def __getattr__(name: str):
    """Lazy load heavy tools only when accessed.

    Args:
        name: The name being imported.

    Returns:
        The requested module/class.

    Raises:
        AttributeError: If the name doesn't exist.
        ImportError: If optional dependencies are not installed.
    """
    if name == "ReadLocalFileTool":
        from .Tools import ReadLocalFileTool

        return ReadLocalFileTool

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

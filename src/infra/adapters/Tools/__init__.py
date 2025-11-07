"""Tools module with lazy loading for heavy dependencies.

This module implements lazy loading to avoid importing heavy dependencies
(like pandas, tiktoken, pymupdf) unless they are actually needed.
"""

from typing import TYPE_CHECKING

# Always import lightweight tools
from .Current_Data_Tool import CurrentDateTool

# Type hints only - not imported at runtime
if TYPE_CHECKING:
    from .Read_Local_File_Tool import ReadLocalFileTool

__all__ = [
    "ReadLocalFileTool",
    "CurrentDateTool",
]


def __getattr__(name: str):
    """Lazy load heavy tools only when accessed.

    This function is called when trying to import a name that doesn't exist
    in the module's namespace. We use it to delay importing ReadLocalFileTool
    until it's actually needed.

    Args:
        name: The name being imported.

    Returns:
        The requested module/class.

    Raises:
        AttributeError: If the name doesn't exist.
        ImportError: If optional dependencies are not installed.
    """
    if name == "ReadLocalFileTool":
        try:
            from .Read_Local_File_Tool import ReadLocalFileTool

            return ReadLocalFileTool
        except ImportError as e:
            raise ImportError(
                f"ReadLocalFileTool requires optional dependencies. "
                f"Install with: pip install ai-agent[file-tools]\n"
                f"Original error: {e}"
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

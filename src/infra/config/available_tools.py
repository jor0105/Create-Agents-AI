"""Registry of available tools with lazy loading for heavy dependencies."""

from typing import Dict, Optional

from src.domain import BaseTool
from src.infra.adapters.Tools import CurrentDateTool


class AvailableTools:
    """Registry of available tools for the AI Agent.

    This class maintains a catalog of tool instances that can be used
    by agents. Tools are registered with string keys for easy lookup.

    Heavy tools (like ReadLocalFileTool) are loaded lazily to improve
    import performance and avoid loading unnecessary dependencies.
    """

    __AVAILABLE_TOOLS: Dict[str, BaseTool] = {
        "currentdate": CurrentDateTool(),
    }

    # Cache for lazily loaded tools
    __LAZY_TOOLS: Dict[str, Optional[BaseTool]] = {}

    @classmethod
    def get_available_tools(cls) -> Dict[str, BaseTool]:
        """Return a dict of available tool instances.

        This method will attempt to load lazy tools (like ReadLocalFileTool)
        if they haven't been loaded yet. If optional dependencies are missing,
        those tools will be silently skipped.

        Returns:
            A dict of supported tool instances.
        """
        # Try to load lazy tools on first access
        if "readlocalfile" not in cls.__LAZY_TOOLS:
            cls.__try_load_read_local_file_tool()

        # Combine eager and lazy tools
        all_tools = cls.__AVAILABLE_TOOLS.copy()
        all_tools.update({k: v for k, v in cls.__LAZY_TOOLS.items() if v is not None})

        return all_tools

    @classmethod
    def __try_load_read_local_file_tool(cls) -> None:
        """Attempt to load ReadLocalFileTool with its heavy dependencies.

        If the optional dependencies are not installed, logs a warning
        and marks the tool as unavailable.
        """
        try:
            from src.infra.adapters.Tools import ReadLocalFileTool
            from src.infra.config.logging_config import LoggingConfig

            logger = LoggingConfig.get_logger(__name__)
            cls.__LAZY_TOOLS["readlocalfile"] = ReadLocalFileTool()
            logger.debug("ReadLocalFileTool loaded successfully")
        except ImportError as e:
            from src.infra.config.logging_config import LoggingConfig

            logger = LoggingConfig.get_logger(__name__)
            logger.warning(
                f"ReadLocalFileTool not available - optional dependencies missing. "
                f"Install with: pip install ai-agent[file-tools]\n"
                f"Error: {e}"
            )
            cls.__LAZY_TOOLS["readlocalfile"] = None
        except Exception as e:
            from src.infra.config.logging_config import LoggingConfig

            logger = LoggingConfig.get_logger(__name__)
            logger.error(f"Failed to load ReadLocalFileTool: {e}")
            cls.__LAZY_TOOLS["readlocalfile"] = None

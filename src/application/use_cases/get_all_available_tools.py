from typing import Dict

from src.infra.config.available_tools import AvailableTools
from src.infra.config.logging_config import LoggingConfig


class GetAllAvailableToolsUseCase:
    """Use case for retrieving all available tools (system + agent tools).

    This use case returns both system tools and agent-specific tools.
    """

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self) -> Dict[str, str]:
        """
        Returns a dictionary of all available tool instances (system + agent).

        Returns:
            Dict[str, str]: Dictionary mapping all tool names to descriptions.
        """
        self.__logger.debug("Retrieving all available tools (system + agent).")
        all_tools = AvailableTools.get_all_available_tools()
        self.__logger.info(f"Retrieved {len(all_tools)} total tool(s).")
        return all_tools

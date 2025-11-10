from typing import Dict

from src.domain import BaseTool
from src.infra.config.available_tools import AvailableTools
from src.infra.config.logging_config import LoggingConfig


class GetAgentAvailableToolsUseCase:
    """Use case for retrieving available tools for the agent."""

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self) -> Dict[str, BaseTool]:
        """
        Returns a dictionary of available tool instances.

        Returns:
            Dict[str, BaseTool]: Dictionary mapping tool names to tool instances.
        """
        self.__logger.debug("Retrieving available tools for agent.")
        all_tools = AvailableTools.get_available_tools()
        return all_tools

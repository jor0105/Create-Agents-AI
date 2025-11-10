from typing import Dict

from src.infra.config.available_tools import AvailableTools
from src.infra.config.logging_config import LoggingConfig


class GetSystemAvailableToolsUseCase:
    """Use case for retrieving system tools available in the AI Agent framework.

    System tools are built-in tools provided by the framework that are always
    available and can be added to any agent.
    """

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self) -> Dict[str, str]:
        """
        Returns a dictionary of available system tools.

        System tools are built-in tools provided by the AI Agent framework.

        Returns:
            Dict[str, str]: Dictionary mapping system tool names to descriptions.
        """
        self.__logger.debug("Retrieving available system tools.")
        system_tools = AvailableTools.get_system_tools()
        self.__logger.info(f"Retrieved {len(system_tools)} system tool(s).")
        return system_tools

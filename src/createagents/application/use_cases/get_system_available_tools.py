from typing import Dict

from ...infra import AvailableTools


class GetSystemAvailableToolsUseCase:
    """Use case for retrieving system tools available in the AI Agent framework.

    System tools are built-in tools provided by the framework that are always
    available and can be added to any agent.
    """

    def execute(self) -> Dict[str, str]:
        """
        Returns a dictionary of available system tools.

        System tools are built-in tools provided by the AI Agent framework.

        Returns:
            Dict[str, str]: Dictionary mapping system tool names to descriptions.
        """
        system_tools: Dict[str, str] = AvailableTools.get_system_tools()
        return system_tools

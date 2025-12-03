from typing import Dict

from ...infra import AvailableTools


class GetAllAvailableToolsUseCase:
    """Use case for retrieving all available tools (system + agent tools).

    This use case returns both system tools and agent-specific tools.
    """

    def execute(self) -> Dict[str, str]:
        """
        Returns a dictionary of all available tool instances (system + agent).

        Returns:
            Dict[str, str]: Dictionary mapping all tool names to descriptions.
        """
        all_tools: Dict[str, str] = AvailableTools.get_all_available_tools()
        return all_tools

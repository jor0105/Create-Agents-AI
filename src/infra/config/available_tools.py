from typing import Dict

from src.domain import BaseTool
from src.infra.adapters.Tools import StockPriceTool, WebSearchTool


class AvailableTools:
    """Registry of available tools for the AI Agent.

    This class maintains a catalog of tool instances that can be used
    by agents. Tools are registered with string keys for easy lookup.
    """

    __AVAILABLE_TOOLS: Dict[str, BaseTool] = {
        "web_search": WebSearchTool(),
        "stock_price": StockPriceTool(),
    }

    @classmethod
    def get_available_tools(cls) -> Dict[str, BaseTool]:
        """
        Return a dict of available tool instances.

        Returns:
            A dict of supported tool instances.
        """
        return cls.__AVAILABLE_TOOLS.copy()

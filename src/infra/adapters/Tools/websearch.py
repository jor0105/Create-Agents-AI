from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig


class WebSearchTool(BaseTool):
    """Fictitious web search tool for testing purposes.

    Simulates searching the web for information. In a real implementation,
    this would integrate with a search API like Google, Bing, or DuckDuckGo.
    """

    name = "web_search"
    description = (
        "Use this tool to obtain current information or answer questions about "
        "recent events. The input should be a clear search query."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the web",
            }
        },
        "required": ["query"],
    }

    def __init__(self):
        """Initialize the WebSearchTool with logging."""
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self, query: str) -> str:
        """Execute a simulated web search.

        Args:
            query: The search query string.

        Returns:
            A string with simulated search results.
        """
        self.__logger.info(f"Executing web search for query: '{query}'")
        self.__logger.debug(f"Web search query details - Length: {len(query)} chars")

        # Simulated responses based on query content
        if "weather" in query.lower() or "clima" in query.lower():
            result = "Observation: The weather in São Paulo is 22°C, cloudy with a chance of rain."
            self.__logger.debug("Web search returned weather information")
            return result
        elif (
            "exchange" in query.lower()
            or "dólar" in query.lower()
            or "usd" in query.lower()
        ):
            result = "Observation: The current USD/BRL exchange rate is R$ 5.15."
            self.__logger.debug("Web search returned exchange rate information")
            return result
        else:
            result = f"Observation: Search results for '{query}': No specific information available in the mock database."
            self.__logger.debug("Web search returned generic response")
            return result

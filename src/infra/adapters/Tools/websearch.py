from src.domain import BaseTool


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

    def execute(self, query: str) -> str:
        """Execute a simulated web search.

        Args:
            query: The search query string.

        Returns:
            A string with simulated search results.
        """
        print(f"[WebSearchTool] Searching for: {query}")

        # Simulated responses based on query content
        if "weather" in query.lower() or "clima" in query.lower():
            return "Observation: The weather in São Paulo is 22°C, cloudy with a chance of rain."
        elif (
            "exchange" in query.lower()
            or "dólar" in query.lower()
            or "usd" in query.lower()
        ):
            return "Observation: The current USD/BRL exchange rate is R$ 5.15."
        else:
            return f"Observation: Search results for '{query}': No specific information available in the mock database."

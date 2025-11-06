import json
import os

import httpx
from dotenv import load_dotenv

from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig


class WebSearchTool(BaseTool):
    """Web search tool using Serper.dev API for real-time information lookup.

    Performs live web searches to find recent facts, news, and up-to-date
    information. Requires SERPER_API_KEY environment variable to be set.
    """

    name = "web_search"
    description = (
        "Use this tool to search the web for recent facts, news, or up-to-date "
        "information. The input should be a search query string (e.g., 'latest "
        "news on AI' or 'who won the 2024 election')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to look up on the web.",
            },
            "k": {
                "type": "integer",
                "description": "Number of results to return (summary snippets).",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        """Initialize the WebSearchTool with logging and API configuration.

        Raises:
            ValueError: If SERPER_API_KEY environment variable is not set.
        """
        load_dotenv()
        self.__logger = LoggingConfig.get_logger(__name__)

        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            error_msg = "SERPER_API_KEY environment variable not set. WebSearchTool requires a valid Serper.dev API key."
            self.__logger.error(error_msg)
            raise ValueError(error_msg)

        self.search_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def _format_results(self, results_json: dict, k: int) -> str:
        """Format search results into a concise English summary.

        Returns a human-readable string with top-k snippets and sources.
        """
        snippets: list[str] = []

        answer_box = results_json.get("answerBox") or {}
        snippet = answer_box.get("snippet") or answer_box.get("answer")
        if snippet:
            snippets.append(f"Direct answer: {snippet}")

        organic = results_json.get("organic", [])
        for i, item in enumerate(organic[:k]):
            title = item.get("title", "N/A")
            link = item.get("link", "N/A")
            item_snippet = item.get("snippet", "N/A")
            snippets.append(
                f"Result {i+1} (Source: {link})\nTitle: {title}\nSnippet: {item_snippet}"
            )

        if not snippets:
            return "Observation: No relevant search results found."

        return "\n\n".join(snippets)

    def execute(self, query: str, k: int = 3) -> str:
        """Execute a web search query and return formatted results.

        Args:
            query: The search query string (e.g., 'latest AI news').
            k: Number of results to return (default 3).

        Returns:
            A formatted string with search results or an error message.
        """
        self.__logger.info(f"Executing web search for query: '{query}' (k={k})")

        payload = {"q": query, "num": k}

        try:
            with httpx.Client(headers=self.headers, timeout=10.0) as client:
                response = client.post(self.search_url, json=payload)
                response.raise_for_status()
                results_json = response.json()
                self.__logger.debug(f"Received search results for query: '{query}'")
                return self._format_results(results_json, k)

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text
            self.__logger.error(f"HTTP error during web search: {status} - {text}")
            return f"[WebSearchTool Error] HTTP {status}: {text}"
        except httpx.TimeoutException:
            self.__logger.error(f"Timeout while performing web search for '{query}'")
            return "[WebSearchTool Error] Timeout while performing web search."
        except httpx.RequestError as e:
            self.__logger.error(f"Request error during web search: {e}")
            return f"[WebSearchTool Error] Request failed: {e}"
        except json.JSONDecodeError:
            self.__logger.error("Failed to decode JSON response from search API")
            return (
                "[WebSearchTool Error] Failed to decode JSON response from search API."
            )


if __name__ == "__main__":
    tool = WebSearchTool()
    print(tool.execute("Who was the president of Brazil in 2024?", k=3))

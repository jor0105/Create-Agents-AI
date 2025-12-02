from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IProviderClient(ABC):
    """Abstract interface for provider API clients.

    This interface allows handlers to communicate with providers
    without coupling to specific SDK implementations.
    """

    @abstractmethod
    async def call_api(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Call the provider API.

        Args:
            model: The model name to use.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tool schemas.
            tool_choice: Optional tool choice configuration.
            **kwargs: Additional provider-specific arguments.

        Returns:
            The response from the provider API.

        Raises:
            ChatException: If the API call fails.
        """
        pass


__all__ = ['IProviderClient']

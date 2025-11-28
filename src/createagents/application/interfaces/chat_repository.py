from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain import BaseTool


class ChatRepository(ABC):
    """Interface for chat repositories."""

    @abstractmethod
    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """Send a message to the chat model and get a response.

        Args:
            model: The name of the model to use.
            instructions: System instructions for the agent.
            config: Configuration parameters for the model.
            tools: List of tools available to the agent.
            history: Chat history.
            user_ask: The user's message.

        Returns:
            str: The model's response.
        """

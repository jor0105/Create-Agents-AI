from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncGenerator, List, Optional, Union

from ...domain import BaseTool


class ChatRepository(ABC):
    """Interface for chat repositories."""

    @abstractmethod
    async def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Send a message to the chat model and get a response.

        Args:
            model: The name of the model to use.
            instructions: System instructions for the agent.
            config: Configuration parameters for the model.
            tools: List of tools available to the agent.
            history: Chat history.
            user_ask: The user's message.

        Returns:
            Union[str, AsyncGenerator[str, None]]: The model's response.
                - str: Complete response (if stream=False)
                - AsyncGenerator: Token stream (if stream=True)
        """

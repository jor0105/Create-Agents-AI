from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..domain import BaseTool


class ChatRepository(ABC):
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
        pass

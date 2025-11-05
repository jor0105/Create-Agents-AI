from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.value_objects import BaseTool


class ChatRepository(ABC):
    @abstractmethod
    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Dict[str, Any],
        history: List[Dict[str, str]],
        user_ask: str,
        tools: Optional[List[BaseTool]] = None,
    ) -> str:
        pass

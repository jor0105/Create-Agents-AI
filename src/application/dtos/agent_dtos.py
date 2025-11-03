from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CreateAgentInputDTO:
    """DTO for creating a new agent."""

    provider: str
    model: str
    name: Optional[str] = None
    instructions: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    history_max_size: int = 10

    def validate(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError(
                "The 'provider' field is required, must be a string, and cannot be empty."
            )

        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError(
                "The 'model' field is required, must be a string, and cannot be empty."
            )

        if self.name is not None and (
            not isinstance(self.name, str) or not self.name.strip()
        ):
            raise ValueError(
                "The 'name' field must be a valid string and cannot be empty."
            )

        if self.instructions is not None and (
            not isinstance(self.instructions, str) or not self.instructions.strip()
        ):
            raise ValueError(
                "The 'instructions' field must be a valid string and cannot be empty."
            )

        if not isinstance(self.config, dict):
            raise ValueError("The 'config' field must be a dictionary (dict).")

        if not isinstance(self.history_max_size, int) or self.history_max_size <= 0:
            raise ValueError("The 'history_max_size' field must be a positive integer.")


@dataclass
class AgentConfigOutputDTO:
    """DTO for returning agent configurations."""

    provider: str
    model: str
    name: Optional[str]
    instructions: Optional[str]
    config: Dict[str, Any]
    history: List[Dict[str, str]]
    history_max_size: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "name": self.name,
            "instructions": self.instructions,
            "config": self.config,
            "history": self.history,
            "history_max_size": self.history_max_size,
        }


@dataclass
class ChatInputDTO:
    """DTO for chat message input."""

    message: str

    def validate(self) -> None:
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "The 'message' field is required, must be a string, and cannot be empty."
            )


@dataclass
class ChatOutputDTO:
    """DTO for chat response."""

    response: str

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
        }

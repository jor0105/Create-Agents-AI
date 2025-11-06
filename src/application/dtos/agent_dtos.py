from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from src.domain import BaseTool, InvalidBaseToolException


@dataclass
class CreateAgentInputDTO:
    """DTO for creating a new agent."""

    provider: str
    model: str
    name: Optional[str] = None
    instructions: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    tools: Optional[Sequence[Union[str, BaseTool]]] = None
    history_max_size: int = 10

    def validate(self) -> None:
        """Validate and transform the DTO data.

        This method validates all fields and converts string tool names
        to BaseTool instances. After calling this method, the 'tools'
        attribute will only contain BaseTool instances (or None).

        Raises:
            ValueError: If any field validation fails.
            InvalidBaseToolException: If a tool is invalid or not found.
        """
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

        if self.tools:
            # Import here to avoid circular dependency
            from src.infra import AvailableTools

            validated_tools: List[BaseTool] = []
            for tool in self.tools:
                if isinstance(tool, str):
                    available_tools = AvailableTools.get_available_tools()
                    if tool.lower() in available_tools:
                        validated_tools.append(available_tools[tool.lower()])
                    else:
                        raise InvalidBaseToolException(tool)
                elif isinstance(tool, BaseTool):
                    required_method = "execute"
                    if not hasattr(tool, required_method) or not callable(
                        getattr(tool, required_method)
                    ):
                        raise InvalidBaseToolException(tool)
                    if not isinstance(tool.name, str) or not tool.name.strip():
                        raise InvalidBaseToolException(tool)
                    if (
                        not isinstance(tool.description, str)
                        or not tool.description.strip()
                    ):
                        raise InvalidBaseToolException(tool)
                    validated_tools.append(tool)
                else:
                    raise InvalidBaseToolException(tool)

            object.__setattr__(self, "tools", validated_tools)

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
    tools: Optional[List[BaseTool]]
    history: List[Dict[str, str]]
    history_max_size: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "name": self.name,
            "instructions": self.instructions,
            "config": self.config,
            "tools": self.tools,
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

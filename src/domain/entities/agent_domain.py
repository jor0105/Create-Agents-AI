from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.domain.exceptions import (
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)
from src.domain.value_objects import History, SupportedConfigs, SupportedProviders


@dataclass
class Agent:
    """Represents an AI agent in the domain.

    Responsibilities:
    - Maintain the agent's identity and configuration.
    - Manage the conversation history through the History Value Object.
    - Ensure the integrity of the agent's data.

    Business rule validations are performed in `__post_init__`.
    The logic for history management is delegated to the History Value Object.
    """

    provider: str
    model: str
    name: Optional[str] = None
    instructions: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    history: History = field(default_factory=History)

    def __post_init__(self):
        """Initializes history if necessary and validates agent configurations.

        Raises:
            InvalidProviderException: If the provider is not supported.
            UnsupportedConfigException: If a configuration is not supported.
            InvalidConfigTypeException: If a configuration type is invalid.
            InvalidAgentConfigException: If a configuration value is invalid.
        """
        if not isinstance(self.history, History):
            object.__setattr__(self, "history", History())

        if self.provider.lower() not in SupportedProviders.get_available_providers():
            raise InvalidProviderException(
                self.provider, SupportedProviders.get_available_providers()
            )

        for key, value in self.config.items():
            if key not in SupportedConfigs.get_available_configs():
                raise UnsupportedConfigException(
                    key, SupportedConfigs.get_available_configs()
                )

            if not isinstance(value, (int, float, str, bool, list, dict, type(None))):
                raise InvalidConfigTypeException(key, type(value))

            SupportedConfigs.validate_config(key, value)

    def add_user_message(self, content: str) -> None:
        """Adds a user message to the history.

        Args:
            content: The content of the message.
        """
        self.history.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Adds an assistant message to the history.

        Args:
            content: The content of the message.
        """
        self.history.add_assistant_message(content)

    def clear_history(self) -> None:
        """Clears the message history."""
        self.history.clear()

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from ..exceptions import (
    InvalidConfigTypeException,
    InvalidProviderException,
    UnsupportedConfigException,
)
from ..value_objects import (
    BaseTool,
    History,
    SupportedConfigs,
    SupportedProviders,
)


@dataclass
class Agent:
    """Represents an AI agent in the domain.

    Responsibilities:
    - Maintain the agent's identity and configuration.
    - Manage conversation history via the `History` value object.
    - Ensure the integrity of the agent's data via domain validations.

    Business validations are executed in `__post_init__`.
    History management logic is delegated to the `History` value object.
    """

    provider: str
    model: str
    name: Optional[str] = None
    instructions: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[BaseTool]] = None
    history: History = field(default_factory=History)
    _logger: Optional[Any] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Initialize history (if needed) and validate agent configuration.

        Raises:
            InvalidProviderException: if the provider is not supported.
            UnsupportedConfigException: if a configuration key is unsupported.
            InvalidConfigTypeException: if a configuration value has an invalid type.
        """
        # Initialize logger
        object.__setattr__(self, '_logger', logging.getLogger(__name__))

        self._logger.debug(
            'Initializing Agent - Provider: %s, Model: %s, Name: %s',
            self.provider,
            self.model,
            self.name,
        )

        if not isinstance(self.history, History):
            object.__setattr__(self, 'history', History())

        available_providers = SupportedProviders.get_available_providers()
        if self.provider.lower() not in available_providers:
            self._logger.error(
                f'Invalid provider: {self.provider}. '
                f'Available: {available_providers}'
            )
            raise InvalidProviderException(
                self.provider, set(available_providers)
            )

        self._logger.debug(
            f"Provider '{self.provider}' validated successfully"
        )

        if self.config:
            for key, value in self.config.items():
                available_configs = SupportedConfigs.get_available_configs()
                if key not in available_configs:
                    self._logger.error(
                        f'Unsupported config key: {key}. '
                        f'Available: {available_configs}'
                    )
                    raise UnsupportedConfigException(
                        key, set(available_configs)
                    )

                if not isinstance(
                    value, (int, float, str, bool, list, dict, type(None))
                ):
                    self._logger.error(
                        f"Invalid config type for '{key}': {type(value)}"
                    )
                    raise InvalidConfigTypeException(key, type(value))

                SupportedConfigs.validate_config(key, value)

        self._logger.info(
            f'Agent initialized - Name: {self.name}, Provider: {self.provider}, '
            f'Model: {self.model}, Tools: {len(self.tools) if self.tools else 0}'
        )

    def add_user_message(self, content: str) -> None:
        """Add a user message to history."""
        if self._logger:
            self._logger.debug(
                f'Adding user message - Length: {len(content)} chars'
            )
        self.history.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to history."""
        if self._logger:
            self._logger.debug(
                f'Adding assistant message - Length: {len(content)} chars'
            )
        self.history.add_assistant_message(content)

    def add_tool_message(self, content: str) -> None:
        """Add a tool message to history."""
        if self._logger:
            self._logger.debug(
                f'Adding tool message - Length: {len(content)} chars'
            )
        self.history.add_tool_message(content)

    def clear_history(self) -> None:
        """Clear all messages from history."""
        if self._logger:
            history_size = len(self.history)
            self._logger.debug(
                f'Clearing history - Removing {history_size} message(s)'
            )
        self.history.clear()

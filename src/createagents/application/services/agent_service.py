from typing import Any, Dict, List, Optional

from ...domain import (
    Agent,
    BaseTool,
    History,
)

from ...domain.interfaces import LoggerInterface


class AgentService:
    """Application service that wraps Agent entity and manages logging.

    This service follows Clean Architecture by keeping logging concerns
    in the application layer while the Agent entity remains pure domain logic.

    Responsibilities:
    - Wrap Agent entity operations with logging
    - Provide high-level agent operations for use cases
    - Coordinate between domain entities and infrastructure
    """

    def __init__(self, agent: Agent, logger: LoggerInterface):
        """Initialize the service with an agent and logger.

        Args:
            agent: The domain Agent entity to wrap.
            logger: Logger instance for logging agent operations.
        """
        self._agent = agent
        self._logger = logger

        self._logger.info(
            'AgentService initialized - Name: %s, Provider: %s, Model: %s, Tools: %s',
            agent.name,
            agent.provider,
            agent.model,
            len(agent.tools) if agent.tools else 0,
        )

    @property
    def agent(self) -> Agent:
        """Get the underlying domain agent.

        Returns:
            The wrapped Agent entity.
        """
        return self._agent

    @property
    def name(self) -> Optional[str]:
        """Get agent name."""
        return self._agent.name

    @property
    def provider(self) -> str:
        """Get agent provider."""
        return self._agent.provider

    @property
    def model(self) -> str:
        """Get agent model."""
        return self._agent.model

    @property
    def instructions(self) -> Optional[str]:
        """Get agent instructions."""
        return self._agent.instructions

    @property
    def config(self) -> Optional[Dict[str, Any]]:
        """Get agent configuration."""
        return self._agent.config

    @property
    def tools(self) -> Optional[List[BaseTool]]:
        """Get agent tools."""
        return self._agent.tools

    @property
    def history(self) -> History:
        """Get agent conversation history."""
        return self._agent.history

    def add_user_message(self, content: str) -> None:
        """Add a user message to history with logging.

        Args:
            content: The message content to add.
        """
        self._logger.debug(
            'Adding user message - Agent: %s, Length: %s chars',
            self._agent.name,
            len(content),
        )
        self._agent.add_user_message(content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to history with logging.

        Args:
            content: The message content to add.
        """
        self._logger.debug(
            'Adding assistant message - Agent: %s, Length: %s chars',
            self._agent.name,
            len(content),
        )
        self._agent.add_assistant_message(content)

    def add_tool_message(self, content: str) -> None:
        """Add a tool message to history with logging.

        Args:
            content: The message content to add.
        """
        self._logger.debug(
            'Adding tool message - Agent: %s, Length: %s chars',
            self._agent.name,
            len(content),
        )
        self._agent.add_tool_message(content)

    def clear_history(self) -> None:
        """Clear conversation history with logging."""
        history_size = len(self._agent.history)
        self._logger.debug(
            'Clearing history - Agent: %s, Removing %s message(s)',
            self._agent.name,
            history_size,
        )
        self._agent.clear_history()

from typing import Any, Dict, Optional, Sequence, Union

from src.application import (
    ChatWithAgentUseCase,
    CreateAgentInputDTO,
    CreateAgentUseCase,
    GetAgentConfigUseCase,
)
from src.domain import Agent, BaseTool
from src.infra import ChatAdapterFactory


class AgentComposer:
    """
    A composer responsible for creating and composing the necessary
    dependencies for agent-related use cases.
    """

    @staticmethod
    def create_agent(
        provider: str,
        model: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[Sequence[Union[str, BaseTool]]] = None,
        history_max_size: int = 10,
    ) -> Agent:
        """
        Creates a new agent using the CreateAgentUseCase.

        Args:
            provider: The specific provider ("openai" or "ollama").
            model: The name of the AI model.
            name: The name of the agent (optional).
            instructions: The agent's instructions (optional).
            config: Extra agent configurations, such as `max_tokens` and `temperature` (optional).
            history_max_size: The maximum history size (default: 10).

        Returns:
            A new agent instance.
        """
        if config is None:
            config = {}

        input_dto = CreateAgentInputDTO(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            tools=tools,
            history_max_size=history_max_size,
        )

        use_case = CreateAgentUseCase()

        return use_case.execute(input_dto)

    @staticmethod
    def create_chat_use_case(
        provider: str,
        model: str,
    ) -> ChatWithAgentUseCase:
        """
        Creates the ChatWithAgentUseCase with its dependencies injected.

        Args:
            provider: The specific provider ("openai" or "ollama").
            model: The name of the AI model.

        Returns:
            A configured ChatWithAgentUseCase.
        """
        chat_adapter = ChatAdapterFactory.create(provider, model)
        return ChatWithAgentUseCase(chat_repository=chat_adapter)

    @staticmethod
    def create_get_config_use_case() -> GetAgentConfigUseCase:
        """
        Creates the GetAgentConfigUseCase.

        Returns:
            A configured GetAgentConfigUseCase.
        """
        return GetAgentConfigUseCase()

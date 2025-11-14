from typing import Any, Dict, Optional, Sequence, Union

from ...application import (
    ChatWithAgentUseCase,
    CreateAgentInputDTO,
    CreateAgentUseCase,
    GetAgentConfigUseCase,
    GetAllAvailableToolsUseCase,
    GetSystemAvailableToolsUseCase,
)
from ...domain import Agent, BaseTool
from ...infra import ChatAdapterFactory, LoggingConfig


class AgentComposer:
    """
    A composer responsible for creating and composing the necessary
    dependencies for agent-related use cases.
    """

    __logger = LoggingConfig.get_logger(__name__)

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
        AgentComposer.__logger.info(
            f"Composing agent creation - Provider: {provider}, Model: {model}, Name: {name}"
        )

        if config is None:
            config = {}

        AgentComposer.__logger.debug(
            f"Agent parameters - Tools: {len(tools) if tools else 0}, "
            f"History max size: {history_max_size}, "
            f"Config keys: {list(config.keys()) if isinstance(config, dict) else 'invalid'}"
        )

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
        agent = use_case.execute(input_dto)

        AgentComposer.__logger.info(f"Agent composed successfully - Name: {agent.name}")
        return agent

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
        AgentComposer.__logger.debug(
            f"Composing chat use case - Provider: {provider}, Model: {model}"
        )

        chat_adapter = ChatAdapterFactory.create(provider, model)
        use_case = ChatWithAgentUseCase(chat_repository=chat_adapter)

        AgentComposer.__logger.debug("Chat use case composed successfully")
        return use_case

    @staticmethod
    def create_get_config_use_case() -> GetAgentConfigUseCase:
        """
        Creates the GetAgentConfigUseCase.

        Returns:
            A configured GetAgentConfigUseCase.
        """
        AgentComposer.__logger.debug("Composing get config use case")
        return GetAgentConfigUseCase()

    @staticmethod
    def create_get_all_available_tools_use_case() -> GetAllAvailableToolsUseCase:
        """
        Creates the GetAllAvailableToolsUseCase.

        This use case returns both system tools and agent tools.

        Returns:
            A configured GetAllAvailableToolsUseCase.
        """
        AgentComposer.__logger.debug("Composing get all available tools use case")
        return GetAllAvailableToolsUseCase()

    @staticmethod
    def create_get_system_available_tools_use_case() -> GetSystemAvailableToolsUseCase:
        """
        Creates the GetSystemAvailableToolsUseCase.

        This use case returns only system tools provided by the framework.

        Returns:
            A configured GetSystemAvailableToolsUseCase.
        """
        AgentComposer.__logger.debug("Composing get system available tools use case")
        return GetSystemAvailableToolsUseCase()

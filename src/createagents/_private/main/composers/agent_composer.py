from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union

from ...application import CreateAgentInputDTO
from ...domain import Agent, BaseTool
from ...domain.interfaces import LoggerInterface, ITraceStore
from ...infra import ChatAdapterFactory
from ...infra.config import create_logger, create_trace_logger

if TYPE_CHECKING:
    from ...application import (
        ChatWithAgentUseCase,
        GetAgentConfigUseCase,
        GetSystemAvailableToolsUseCase,
    )


class AgentComposer:
    """
    A composer responsible for creating and composing the necessary
    dependencies for agent-related use cases.
    """

    __logger: LoggerInterface = create_logger(__name__)

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
            tools: A list of tool names or BaseTool instances to be used by the agent (optional).
            history_max_size: The maximum history size (default: 10).

        Returns:
            A new agent instance.
        """
        AgentComposer.__logger.info(
            'Composing agent creation - Provider: %s, Model: %s, Name: %s',
            provider,
            model,
            name,
        )

        if config is None:
            # stream will be set to True by default
            config = {'stream': True}

        AgentComposer.__logger.debug(
            'Agent parameters - Tools: %s, History max size: %s, Config keys: %s',
            len(tools) if tools else 0,
            history_max_size,
            list(config.keys()) if isinstance(config, dict) else 'invalid',
        )

        from ...application import CreateAgentUseCase  # pylint: disable=import-outside-toplevel

        input_dto = CreateAgentInputDTO(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            tools=tools,
            history_max_size=history_max_size,
        )

        logger = create_logger(
            'createagents.application.use_cases.create_agent'
        )
        use_case = CreateAgentUseCase(logger=logger)
        agent = use_case.execute(input_dto)

        AgentComposer.__logger.info(
            'Agent composed successfully - Name: %s', agent.name
        )
        return agent

    @staticmethod
    def create_chat_use_case(
        provider: str,
        model: str,
        trace_store: Optional['ITraceStore'] = None,
    ) -> ChatWithAgentUseCase:
        """
        Creates the ChatWithAgentUseCase with its dependencies injected.

        Args:
            provider: The specific provider.
            model: The name of the AI model.
            trace_store: Optional trace store for persisting traces.
                        If provided, trace logging is enabled.

        Returns:
            A configured ChatWithAgentUseCase.
        """
        from ...application import ChatWithAgentUseCase  # pylint: disable=import-outside-toplevel

        AgentComposer.__logger.debug(
            'Composing chat use case - Provider: %s, Model: %s, Tracing: %s',
            provider,
            model,
            trace_store,
        )

        # Create trace logger only if trace_store is provided
        trace_logger = None
        if trace_store is not None:
            trace_logger = create_trace_logger(
                'createagents.tracing.chat',
                json_output=False,
                trace_store=trace_store,
            )

        # Pass trace_logger to the factory so handlers can use it
        chat_adapter = ChatAdapterFactory.create(
            provider, model, trace_logger=trace_logger
        )
        logger = create_logger(
            'createagents.application.use_cases.chat_with_agent'
        )

        use_case = ChatWithAgentUseCase(
            chat_repository=chat_adapter,
            logger=logger,
            trace_logger=trace_logger,
        )

        AgentComposer.__logger.debug('Chat use case composed successfully')
        return use_case

    @staticmethod
    def create_get_config_use_case() -> GetAgentConfigUseCase:
        """
        Creates the GetAgentConfigUseCase.

        Returns:
            A configured GetAgentConfigUseCase.
        """
        from ...application import GetAgentConfigUseCase  # pylint: disable=import-outside-toplevel

        AgentComposer.__logger.debug('Composing get config use case')
        return GetAgentConfigUseCase()

    @staticmethod
    def create_get_system_available_tools_use_case() -> (
        GetSystemAvailableToolsUseCase
    ):
        """
        Creates the GetSystemAvailableToolsUseCase.

        This use case returns only system tools provided by the framework.

        Returns:
            A configured GetSystemAvailableToolsUseCase.
        """
        from ...application import GetSystemAvailableToolsUseCase  # pylint: disable=import-outside-toplevel

        AgentComposer.__logger.debug(
            'Composing get system available tools use case'
        )
        return GetSystemAvailableToolsUseCase()

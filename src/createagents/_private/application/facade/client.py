from typing import Any, Dict, List, Optional, Sequence, Union

from ...domain import Agent, BaseTool, ToolChoiceType
from ...domain.interfaces import LoggerInterface, ITraceStore
from ...infra import ChatMetrics
from ...main import AgentComposer
from ..dtos import ChatInputDTO, StreamingResponseDTO
from ..use_cases import (
    ChatWithAgentUseCase,
    GetAgentConfigUseCase,
    GetSystemAvailableToolsUseCase,
)


class CreateAgent:
    """
    The application layer controller for interacting with AI agents.
    It is responsibility for coordinating requests and responses.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[Sequence[Union[str, BaseTool]]] = None,
        history_max_size: int = 10,
        logger: Optional[LoggerInterface] = None,
        trace_store: Optional['ITraceStore'] = None,
    ) -> None:
        """
        Initializes the controller by creating an agent and its dependencies.

        Args:
            provider: The specific provider ("openai" or "ollama"), which defines which API to use.
            model: The name of the AI model.
            name: The name of the agent (optional).
            instructions: The agent's instructions or prompt (optional).
            config: Extra agent configurations, such as `max_tokens` and `temperature` (optional).
            tools: A list of tool names or BaseTool instances to be used by the agent (optional).
            history_max_size: The maximum history size (default: 10).
            logger: Optional logger interface. If not provided, a default logger will be created.
            trace_store: Optional trace store for persisting trace data. If provided, tracing
                        is automatically enabled. Pass any ITraceStore implementation:
                        - FileTraceStore() for disk persistence (~/.createagents/traces/)
                        - InMemoryTraceStore() for in-memory storage (dev/testing)
                        - Custom ITraceStore implementation for OpenTelemetry, databases, etc.
        """
        # If no logger provided, create one from infrastructure
        if logger is None:
            from ...infra.config import create_logger  # pylint: disable=import-outside-toplevel

            self.__logger: LoggerInterface = create_logger(__name__)
        else:
            self.__logger = logger

        self.__logger.info(
            'Initializing CreateAgent controller - Provider: %s, Model: %s, Name: %s',
            provider,
            model,
            name,
        )

        self.__agent: Agent = AgentComposer.create_agent(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            tools=tools,
            history_max_size=history_max_size,
        )

        self.__chat_use_case: ChatWithAgentUseCase = (
            AgentComposer.create_chat_use_case(
                provider=provider,
                model=model,
                trace_store=trace_store,
            )
        )
        self.__get_config_use_case: GetAgentConfigUseCase = (
            AgentComposer.create_get_config_use_case()
        )

        self.__get_system_available_tools_use_case: GetSystemAvailableToolsUseCase = AgentComposer.create_get_system_available_tools_use_case()

        self.__logger.info(
            'Agent controller initialized',
            extra={
                'event': 'controller.initialized',
                'agent_name': self.__agent.name,
                'provider': provider,
                'model': model,
            },
        )

    async def chat(
        self,
        message: str,
        tool_choice: Optional[ToolChoiceType] = None,
    ) -> Union[str, StreamingResponseDTO]:
        """
        Sends a message to the agent and returns the response.

        The response appears token-by-token in real-time when stream=True is configured,
        or as a complete response when stream=False (default).

        Args:
            message: The user's message.
            tool_choice: Optional tool choice configuration. Can be:
                - "auto": Let the model decide (default)
                - "none": Don't call any tool
                - "required": Force at least one tool call
                - "<tool_name>": Force a specific tool
                - {"type": "function", "function": {"name": "tool_name"}}
                - ToolChoice value object

        Returns:
            Union[str, StreamingResponseDTO]: The agent's response.
                Returns str for normal responses, or StreamingResponseDTO for streaming
                (which behaves like str when printed).

        Example:
            >>> agent = CreateAgent(provider="openai", model="gpt-5-nano")
            >>> print(await agent.chat("Hello!"))  # Works seamlessly with or without streaming
            >>> # Force use of a specific tool
            >>> print(await agent.chat("Calculate 2+2", tool_choice="calculator"))
        """
        from typing import AsyncGenerator  # pylint: disable=import-outside-toplevel

        input_dto = ChatInputDTO(
            message=message,
            # ToolChoiceType validation happens in DTO.validate()
            tool_choice=tool_choice,  # type: ignore[arg-type]
        )
        result = await self.__chat_use_case.execute(self.__agent, input_dto)

        # If result is an AsyncGenerator (streaming mode), wrap in StreamingResponseDTO
        if isinstance(result, AsyncGenerator):
            return StreamingResponseDTO(result)

        # Otherwise it's a ChatOutputDTO, extract the response
        response: str = result.response

        return response

    def get_configs(self) -> Dict[str, Any]:
        """
        Returns the agent's configurations.

        Returns:
            A dictionary containing the agent's configurations.
        """
        output_dto = self.__get_config_use_case.execute(self.__agent)

        output_dict: Dict[str, Any] = output_dto.to_dict()

        return output_dict

    def get_all_available_tools(self) -> Dict[str, str]:
        """Return a dict of all available tools for THIS agent (system + agent-specific).

        This method returns:
        1. System tools (built-in tools like CurrentDateTool, ReadLocalFileTool)
        2. Agent-specific tools (custom tools added when this agent was created)

        Note: System tools are not duplicated. If an agent has a system tool
        in its tools list, it won't be added twice.

        Returns:
            A dict of all tool names and descriptions available for this agent.
        """
        from ...infra import AvailableTools  # pylint: disable=import-outside-toplevel

        # Get system tools
        all_tools: Dict[str, str] = (
            self.__get_system_available_tools_use_case.execute()
        )

        # Get system tool names (registry keys) and tool instance names
        system_tool_registry_names = AvailableTools.get_system_tool_names()

        # Also get the internal names of system tools (tool.name attribute)
        system_tool_instances = AvailableTools.get_all_tool_instances()
        system_tool_internal_names = {
            tool.name.lower()
            for key, tool in system_tool_instances.items()
            if key in system_tool_registry_names
        }

        # Combine both sets to catch all variations
        all_system_tool_names = (
            system_tool_registry_names | system_tool_internal_names
        )

        # Add agent-specific tools (excluding system tools to avoid duplication)
        if self.__agent.tools:
            for tool in self.__agent.tools:
                tool_name_lower = tool.name.lower()
                # Only add if it's not already a system tool
                # (by either registry name or internal name)
                if tool_name_lower not in all_system_tool_names:
                    all_tools[tool_name_lower] = tool.description

        return all_tools

    def get_system_available_tools(self) -> Dict[str, str]:
        """Return a dict of system tools only.

        System tools are built-in tools provided by the AI Agent framework
        that are always available and can be added to any agent.

        Returns:
            A dict of system tool names and descriptions.
        """
        output_dto: Dict[str, str] = (
            self.__get_system_available_tools_use_case.execute()
        )
        return output_dto

    def clear_history(self) -> None:
        """Clears the agent's history."""
        history_size = len(self.__agent.history)
        self.__agent.clear_history()
        self.__logger.info(
            'History cleared',
            extra={
                'event': 'history.cleared',
                'agent_name': self.__agent.name,
                'messages_removed': history_size,
            },
        )

    def get_metrics(self) -> List[ChatMetrics]:
        """
        Returns the performance metrics of the chat adapter.

        Returns:
            A list of metrics collected during interactions.
        """
        metrics: List[ChatMetrics] = self.__chat_use_case.get_metrics()
        return metrics

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in JSON format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A JSON string with the metrics.
        """
        from ...infra import MetricsCollector  # pylint: disable=import-outside-toplevel

        self.__logger.debug(
            'Exporting metrics to JSON - Filepath: %s',
            filepath or 'None (return string)',
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        json_result: str = collector.export_json(filepath)

        if filepath:
            self.__logger.info('Metrics exported to JSON file: %s', filepath)
        else:
            self.__logger.debug('Metrics exported as JSON string')

        return json_result

    def export_metrics_prometheus(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in Prometheus format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A string in Prometheus format with the metrics.
        """
        from ...infra import MetricsCollector  # pylint: disable=import-outside-toplevel

        self.__logger.debug(
            'Exporting metrics to Prometheus - Filepath: %s',
            filepath or 'None (return string)',
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        prometheus_text: str = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)
            self.__logger.info(
                'Metrics exported to Prometheus file: %s', filepath
            )
        else:
            self.__logger.debug('Metrics exported as Prometheus string')

        return prometheus_text

    def start_cli(self) -> None:
        """Start interactive CLI chat session.

        This method launches a terminal-based interactive chat interface
        using the presentation layer's CLI application.

        Example:
            >>> agent = CreateAgent(provider="openai", model="gpt-4")
            >>> agent.start_cli()  # Starts interactive chat
        """
        from ...presentation.cli import ChatCLIApplication  # pylint: disable=import-outside-toplevel

        self.__logger.info(
            'Starting CLI application for agent: %s', self.__agent.name
        )

        cli_app = ChatCLIApplication(agent=self)
        cli_app.run()

        self.__logger.info('CLI application ended')

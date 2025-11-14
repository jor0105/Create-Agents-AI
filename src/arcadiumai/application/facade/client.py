from typing import Any, Dict, List, Optional, Sequence, Union

from ..application import (
    ChatInputDTO,
    ChatWithAgentUseCase,
    GetAgentConfigUseCase,
    GetAllAvailableToolsUseCase,
    GetSystemAvailableToolsUseCase,
)
from ..domain import Agent, BaseTool
from ..infra import ChatMetrics, LoggingConfig
from ..main import AgentComposer


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
    ) -> None:
        """
        Initializes the controller by creating an agent and its dependencies.

        Args:
            provider: The specific provider ("openai" or "ollama"), which defines which API to use.
            model: The name of the AI model.
            name: The name of the agent (optional).
            instructions: The agent's instructions or prompt (optional).
            config: Extra agent configurations, such as `max_tokens` and `temperature` (optional).
            history_max_size: The maximum history size (default: 10).
        """
        self.__logger = LoggingConfig.get_logger(__name__)

        self.__logger.info(
            f"Initializing CreateAgent controller - Provider: {provider}, Model: {model}, Name: {name}"
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

        self.__chat_use_case: ChatWithAgentUseCase = AgentComposer.create_chat_use_case(
            provider=provider, model=model
        )
        self.__get_config_use_case: GetAgentConfigUseCase = (
            AgentComposer.create_get_config_use_case()
        )

        self.__get_all_available_tools_use_case: GetAllAvailableToolsUseCase = (
            AgentComposer.create_get_all_available_tools_use_case()
        )

        self.__get_system_available_tools_use_case: GetSystemAvailableToolsUseCase = (
            AgentComposer.create_get_system_available_tools_use_case()
        )

        self.__logger.info(
            f"CreateAgent controller initialized successfully - Agent: {self.__agent.name}"
        )

    def chat(
        self,
        message: str,
    ) -> str:
        """
        Sends a message to the agent and returns the response.

        Args:
            message: The user's message.

        Returns:
            The agent's response.
        """
        self.__logger.debug(
            f"Chat request received - Message length: {len(message)} chars"
        )

        input_dto = ChatInputDTO(
            message=message,
        )
        output_dto = self.__chat_use_case.execute(self.__agent, input_dto)

        self.__logger.debug(
            f"Chat response generated - Response length: {len(output_dto.response)} chars"
        )

        response: str = output_dto.response

        return response

    def get_configs(self) -> Dict[str, Any]:
        """
        Returns the agent's configurations.

        Returns:
            A dictionary containing the agent's configurations.
        """
        self.__logger.debug("Retrieving agent configurations")
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
        from ..infra import AvailableTools

        self.__logger.debug(
            "Retrieving all available tools for this agent (system + agent-specific)"
        )

        # Get system tools
        all_tools: Dict[str, str] = self.__get_system_available_tools_use_case.execute()

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
        all_system_tool_names = system_tool_registry_names | system_tool_internal_names

        # Add agent-specific tools (excluding system tools to avoid duplication)
        if self.__agent.tools:
            for tool in self.__agent.tools:
                tool_name_lower = tool.name.lower()
                # Only add if it's not already a system tool (by either registry name or internal name)
                if tool_name_lower not in all_system_tool_names:
                    all_tools[tool_name_lower] = tool.description

        self.__logger.info(
            f"Retrieved {len(all_tools)} tool(s) for agent '{self.__agent.name}'"
        )
        return all_tools

    def get_system_available_tools(self) -> Dict[str, str]:
        """Return a dict of system tools only.

        System tools are built-in tools provided by the AI Agent framework
        that are always available and can be added to any agent.

        Returns:
            A dict of system tool names and descriptions.
        """
        self.__logger.debug("Retrieving system available tools")
        output_dto: Dict[str, str] = (
            self.__get_system_available_tools_use_case.execute()
        )
        return output_dto

    def clear_history(self) -> None:
        """Clears the agent's history."""
        history_size = len(self.__agent.history)
        self.__agent.clear_history()
        self.__logger.info(f"Agent history cleared - Removed {history_size} message(s)")

    def get_metrics(self) -> List[ChatMetrics]:
        """
        Returns the performance metrics of the chat adapter.

        Returns:
            A list of metrics collected during interactions.
        """
        metrics: List[ChatMetrics] = self.__chat_use_case.get_metrics()
        self.__logger.debug(f"Retrieved {len(metrics)} metric(s)")
        return metrics

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in JSON format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A JSON string with the metrics.
        """
        from ..infra import MetricsCollector

        self.__logger.debug(
            f"Exporting metrics to JSON - Filepath: {filepath or 'None (return string)'}"
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        json_result: str = collector.export_json(filepath)

        if filepath:
            self.__logger.info(f"Metrics exported to JSON file: {filepath}")
        else:
            self.__logger.debug("Metrics exported as JSON string")

        return json_result

    def export_metrics_prometheus(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in Prometheus format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A string in Prometheus format with the metrics.
        """
        from ..infra import MetricsCollector

        self.__logger.debug(
            f"Exporting metrics to Prometheus - Filepath: {filepath or 'None (return string)'}"
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        prometheus_text: str = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)
            self.__logger.info(f"Metrics exported to Prometheus file: {filepath}")
        else:
            self.__logger.debug("Metrics exported as Prometheus string")

        return prometheus_text

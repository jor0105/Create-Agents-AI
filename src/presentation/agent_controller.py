from typing import Any, Dict, List, Optional, Sequence, Union

from src.application import (
    ChatInputDTO,
    ChatWithAgentUseCase,
    GetAgentAvailableToolsUseCase,
    GetAgentConfigUseCase,
)
from src.domain import Agent, BaseTool
from src.infra import ChatMetrics
from src.infra.config.logging_config import LoggingConfig
from src.main import AgentComposer


class AIAgent:
    """
    The presentation layer controller for interacting with AI agents.
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
            f"Initializing AIAgent controller - Provider: {provider}, Model: {model}, Name: {name}"
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

        self.__get_available_tools_use_case: GetAgentAvailableToolsUseCase = (
            AgentComposer.create_get_available_tools_use_case()
        )

        self.__logger.info(
            f"AIAgent controller initialized successfully - Agent: {self.__agent.name}"
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
        return output_dto.response

    def get_configs(self) -> Dict[str, Any]:
        """
        Returns the agent's configurations.

        Returns:
            A dictionary containing the agent's configurations.
        """
        self.__logger.debug("Retrieving agent configurations")
        output_dto = self.__get_config_use_case.execute(self.__agent)
        return output_dto.to_dict()

    def get_available_tools(self) -> Dict[str, BaseTool]:
        """Return a dict of available tool instances.

        This method will attempt to load lazy tools (like ReadLocalFileTool)
        if they haven't been loaded yet. If optional dependencies are missing,
        those tools will be silently skipped.

        Returns:
            A dict of supported tool instances.
        """
        self.__logger.debug("Retrieving agent available tools")
        output_dto: Dict[str, BaseTool] = self.__get_available_tools_use_case.execute()
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
        metrics = self.__chat_use_case.get_metrics()
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
        from src.infra.config.metrics import MetricsCollector

        self.__logger.debug(
            f"Exporting metrics to JSON - Filepath: {filepath or 'None (return string)'}"
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        json_result = collector.export_json(filepath)

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
        from src.infra.config.metrics import MetricsCollector

        self.__logger.debug(
            f"Exporting metrics to Prometheus - Filepath: {filepath or 'None (return string)'}"
        )

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        prometheus_text = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)
            self.__logger.info(f"Metrics exported to Prometheus file: {filepath}")
        else:
            self.__logger.debug("Metrics exported as Prometheus string")

        return prometheus_text

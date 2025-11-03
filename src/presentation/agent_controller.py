from typing import Any, Dict, List, Optional

from src.application import ChatInputDTO, ChatWithAgentUseCase, GetAgentConfigUseCase
from src.domain import Agent
from src.infra import ChatMetrics
from src.main import AgentComposer


class AIAgent:
    """
    The presentation layer controller for interacting with AI agents.
    It is responsible for coordinating requests and responses.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
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
        self.__agent: Agent = AgentComposer.create_agent(
            provider=provider,
            model=model,
            name=name,
            instructions=instructions,
            config=config,
            history_max_size=history_max_size,
        )

        self.__chat_use_case: ChatWithAgentUseCase = AgentComposer.create_chat_use_case(
            provider=provider, model=model
        )
        self.__get_config_use_case: GetAgentConfigUseCase = (
            AgentComposer.create_get_config_use_case()
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
        input_dto = ChatInputDTO(
            message=message,
        )
        output_dto = self.__chat_use_case.execute(self.__agent, input_dto)
        return output_dto.response

    def get_configs(self) -> Dict[str, Any]:
        """
        Returns the agent's configurations.

        Returns:
            A dictionary containing the agent's configurations.
        """
        output_dto = self.__get_config_use_case.execute(self.__agent)
        return output_dto.to_dict()

    def clear_history(self) -> None:
        """Clears the agent's history."""
        self.__agent.clear_history()

    def get_metrics(self) -> List[ChatMetrics]:
        """
        Returns the performance metrics of the chat adapter.

        Returns:
            A list of metrics collected during interactions.
        """
        return self.__chat_use_case.get_metrics()

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in JSON format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A JSON string with the metrics.
        """
        from src.infra.config.metrics import MetricsCollector

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        return collector.export_json(filepath)

    def export_metrics_prometheus(self, filepath: Optional[str] = None) -> str:
        """
        Exports metrics in Prometheus format.

        Args:
            filepath: The file path to save the metrics (optional).

        Returns:
            A string in Prometheus format with the metrics.
        """
        from src.infra.config.metrics import MetricsCollector

        collector = MetricsCollector()
        for metric in self.get_metrics():
            collector.add(metric)

        prometheus_text = collector.export_prometheus()

        if filepath:
            collector.export_prometheus_to_file(filepath)

        return prometheus_text

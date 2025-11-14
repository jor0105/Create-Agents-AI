from ..application.dtos import AgentConfigOutputDTO
from ..domain import Agent
from ..infra import LoggingConfig


class GetAgentConfigUseCase:
    """Use case for retrieving agent configurations."""

    def __init__(self):
        """Initialize the GetAgentConfigUseCase with logging."""
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self, agent: Agent) -> AgentConfigOutputDTO:
        """
        Returns the agent's configurations as a DTO.

        Args:
            agent: The agent instance.

        Returns:
            A DTO containing the agent's configurations.
        """
        self.__logger.debug(
            f"Retrieving configuration for agent - Name: {agent.name}, "
            f"Provider: {agent.provider}, Model: {agent.model}"
        )

        config_dto = AgentConfigOutputDTO(
            provider=agent.provider,
            model=agent.model,
            name=agent.name,
            instructions=agent.instructions,
            config=agent.config,
            tools=agent.tools,
            history=agent.history.to_dict_list(),
            history_max_size=agent.history.max_size,
        )

        self.__logger.debug(
            f"Configuration retrieved - History size: {len(agent.history)}/{agent.history.max_size}, "
            f"Tools: {len(agent.tools) if agent.tools else 0}"
        )

        return config_dto

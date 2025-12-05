from ...domain import Agent
from ..dtos import AgentConfigOutputDTO


class GetAgentConfigUseCase:
    """Use case for retrieving agent configurations."""

    def execute(self, agent: Agent) -> AgentConfigOutputDTO:
        """
        Returns the agent's configurations as a DTO.

        Args:
            agent: The agent instance.

        Returns:
            A DTO containing the agent's configurations.
        """
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

        return config_dto

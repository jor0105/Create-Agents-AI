from src.application.dtos import AgentConfigOutputDTO
from src.domain.entities.agent_domain import Agent


class GetAgentConfigUseCase:
    """Use Case for obtaining an agent's configurations."""

    def execute(self, agent: Agent) -> AgentConfigOutputDTO:
        """
        Returns the agent's configurations as a DTO.

        Args:
            agent: The agent instance.

        Returns:
            A DTO containing the agent's configurations.
        """
        return AgentConfigOutputDTO(
            provider=agent.provider,
            model=agent.model,
            name=agent.name,
            instructions=agent.instructions,
            config=agent.config,
            history=agent.history.to_dict_list(),
            history_max_size=agent.history.max_size,
        )

from src.application.dtos import AgentConfigOutputDTO
from src.domain import Agent


class GetAgentConfigUseCase:
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
            tools=agent.tools,
            history=agent.history.to_dict_list(),
            history_max_size=agent.history.max_size,
        )

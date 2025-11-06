from src.application.dtos import CreateAgentInputDTO
from src.domain import Agent, History, InvalidAgentConfigException

from .format_instructions_use_case import FormatInstructionsUseCase


class CreateAgentUseCase:
    """Use Case for creating a new agent instance."""

    def execute(self, input_dto: CreateAgentInputDTO) -> Agent:
        """
        Creates a new agent with the provided configurations.

        Args:
            input_dto: DTO with the data for agent creation.

        Returns:
            A new instance of the configured agent.

        Raises:
            InvalidAgentConfigException: If the input data is invalid.
            InvalidProviderException: If the provider is not supported.
            UnsupportedConfigException: If a configuration is not supported.
            InvalidConfigTypeException: If a configuration type is invalid.
        """
        try:
            input_dto.validate()
        except ValueError as e:
            raise InvalidAgentConfigException("input_dto", str(e))

        format_instructions = FormatInstructionsUseCase()
        instructions = format_instructions.execute(
            instructions=input_dto.instructions,
            tools=input_dto.tools,  # type: ignore
            provider=input_dto.provider,
        )

        agent = Agent(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=instructions,
            config=input_dto.config,
            tools=input_dto.tools,  # type: ignore
            history=History(max_size=input_dto.history_max_size),
        )

        return agent

from ...domain import Agent, History, InvalidAgentConfigException
from ...infra import LoggingConfig
from ..dtos import CreateAgentInputDTO


class CreateAgentUseCase:
    """Use Case for creating a new agent instance."""

    def __init__(self):
        """Initialize the CreateAgentUseCase with logging."""
        self.__logger = LoggingConfig.get_logger(__name__)

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
        self.__logger.info(
            f'Creating new agent - Provider: {input_dto.provider}, Model: {input_dto.model}'
        )
        self.__logger.debug(
            f'Agent configuration - Name: {input_dto.name}, '
            f'Tools: {len(input_dto.tools) if input_dto.tools else 0}, '
            f'History max size: {input_dto.history_max_size}'
        )

        try:
            input_dto.validate()
            self.__logger.debug('Input DTO validated successfully')
        except ValueError as e:
            self.__logger.error(f'Validation error in input DTO: {str(e)}')
            raise InvalidAgentConfigException('input_dto', str(e))

        agent = Agent(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            tools=input_dto.tools,  # type: ignore
            history=History(max_size=input_dto.history_max_size),
        )

        self.__logger.info(
            f'Agent created successfully - Name: {agent.name}, Provider: {agent.provider}, Model: {agent.model}'
        )

        return agent

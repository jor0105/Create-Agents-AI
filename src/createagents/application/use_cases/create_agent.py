from ...domain import Agent, History, InvalidAgentConfigException
from ...domain.interfaces import LoggerInterface
from ..dtos import CreateAgentInputDTO


class CreateAgentUseCase:
    """Use Case for creating a new agent instance."""

    def __init__(self, logger: LoggerInterface):
        """Initialize the CreateAgentUseCase with logging.

        Args:
            logger: Logger interface for logging operations.
        """
        self.__logger = logger

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
            'Creating new agent - Provider: %s, Model: %s',
            input_dto.provider,
            input_dto.model,
        )
        self.__logger.debug(
            'Agent configuration - Name: %s, Tools: %s, History max size: %s',
            input_dto.name,
            len(input_dto.tools) if input_dto.tools else 0,
            input_dto.history_max_size,
        )

        try:
            input_dto.validate()
        except ValueError as e:
            self.__logger.error(
                'Agent creation failed - validation error',
                extra={'error': str(e), 'provider': input_dto.provider},
            )
            raise InvalidAgentConfigException('input_dto', str(e)) from e

        agent = Agent(
            provider=input_dto.provider,
            model=input_dto.model,
            name=input_dto.name,
            instructions=input_dto.instructions,
            config=input_dto.config,
            tools=input_dto.tools,
            history=History(max_size=input_dto.history_max_size),
        )

        self.__logger.info(
            'Agent created',
            extra={
                'event': 'agent.created',
                'agent_name': agent.name,
                'provider': agent.provider,
                'model': agent.model,
                'tools_count': len(agent.tools) if agent.tools else 0,
                'history_max_size': agent.history.max_size,
            },
        )

        return agent

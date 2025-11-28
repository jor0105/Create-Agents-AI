from typing import List

from ...domain import Agent, ChatException
from ...infra import ChatMetrics, LoggingConfig
from ...utils import TextSanitizer
from ..dtos import ChatInputDTO, ChatOutputDTO
from ..interfaces import ChatRepository


class ChatWithAgentUseCase:
    """
    Use case for handling chat interactions with an AI agent.

    This class orchestrates the process of sending a user message to an agent,
    receiving the response, sanitizing the output, and updating the agent's
    conversation history. It also handles error management and logging during
    the interaction.
    """

    def __init__(self, chat_repository: ChatRepository):
        """
        Initializes the Use Case with its dependencies.

        Args:
            chat_repository: Repository for AI communication.
        """
        self.__chat_repository = chat_repository
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self, agent: Agent, input_dto: ChatInputDTO) -> ChatOutputDTO:
        """
        Sends a message to the agent and returns the response.

        Args:
            agent: The agent instance.
            input_dto: DTO with the user's message.

        Returns:
            A DTO with the agent's response.

        Raises:
            ValueError: If the input data is invalid.
            ChatException: If an error occurs during AI communication.
        """
        input_dto.validate()

        self.__logger.info(
            "Running chat with agent '%s' (model: %s)", agent.name, agent.model
        )
        self.__logger.debug('User message: %s...', input_dto.message[:100])

        try:
            response = self.__chat_repository.chat(
                model=agent.model,
                instructions=agent.instructions,
                config=agent.config,
                tools=agent.tools,
                history=agent.history.to_dict_list(),
                user_ask=input_dto.message,
            )

            final_response = TextSanitizer.format_markdown_for_terminal(
                response
            )

            if not final_response:
                self.__logger.error('Empty response received from repository')
                raise ChatException('Empty response received from repository')

            output_dto = ChatOutputDTO(response=final_response)

            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(final_response)

            self.__logger.info('Chat executed successfully')
            self.__logger.debug(
                'Response (first 100 chars): %s...', final_response[:100]
            )

            return output_dto

        except ChatException:
            self.__logger.error(
                'ChatException during chat execution', exc_info=True
            )
            raise
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            error_map = {
                ValueError: (
                    'Validation error',
                    'Validation error during chat: {}',
                ),
                TypeError: ('Type error', 'Type error during chat: {}'),
                KeyError: (
                    'Error processing response',
                    'Error processing AI response: {}',
                ),
            }
            msg, user_msg = error_map.get(
                type(e), ('Error', 'Error during chat: {}')
            )
            self.__logger.error('%s: %s', msg, str(e), exc_info=True)
            raise ChatException(user_msg.format(str(e))) from e
        except Exception as e:
            self.__logger.error('Unexpected error: %s', str(e), exc_info=True)
            raise ChatException(
                f'Unexpected error during communication with AI: {str(e)}',
                original_error=e,
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """
        Returns the metrics collected by the chat repository.

        Returns:
            A list of metrics if the repository supports it; otherwise, an empty list.
        """
        if hasattr(self.__chat_repository, 'get_metrics'):
            metrics = self.__chat_repository.get_metrics()
            if isinstance(metrics, list):
                return metrics
        return []

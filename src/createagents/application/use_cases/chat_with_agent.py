from typing import AsyncGenerator, List, Union

from ...domain import Agent, ChatException
from ...infra import ChatMetrics, LoggingConfig
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

    async def execute(
        self, agent: Agent, input_dto: ChatInputDTO
    ) -> Union[ChatOutputDTO, AsyncGenerator[str, None]]:
        """
        Sends a message to the agent and returns the response.

        Args:
            agent: The agent instance.
            input_dto: DTO with the user's message.

        Returns:
            Union[ChatOutputDTO, AsyncGenerator[str, None]]: The agent's response.
                - ChatOutputDTO: Complete response (if stream=False)
                - AsyncGenerator: Token stream (if stream=True)

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
            response = await self.__chat_repository.chat(
                model=agent.model,
                instructions=agent.instructions,
                config=agent.config,
                tools=agent.tools,
                history=agent.history.to_dict_list(),
                user_ask=input_dto.message,
            )

            if isinstance(response, AsyncGenerator):
                return self.__handle_streaming(agent, input_dto, response)

            # Standard non-streaming response
            if not response:
                self.__logger.error('Empty response received from repository')
                raise ChatException('Empty response received from repository')

            output_dto = ChatOutputDTO(response=response)

            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(response)

            self.__logger.info('Chat executed successfully')
            self.__logger.debug(
                'Response (first 100 chars): %s...', response[:100]
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

    async def __handle_streaming(
        self,
        agent: Agent,
        input_dto: ChatInputDTO,
        stream: AsyncGenerator[str, None],
    ) -> AsyncGenerator[str, None]:
        """
        Handles streaming responses by yielding tokens and preserving chat history.

        This method creates a wrapper generator that:
        1. Yields tokens as they arrive from the underlying stream
        2. Accumulates the complete response
        3. Updates the agent's conversation history after streaming completes

        Args:
            agent: The agent instance.
            input_dto: DTO with the user's message.
            stream: The token generator from the repository.

        Yields:
            str: Individual tokens from the model's response.

        Raises:
            ChatException: If an error occurs during streaming.
        """
        full_response = []

        try:
            self.__logger.info(
                'Starting streaming response for agent: %s', agent.name
            )
            async for token in stream:
                full_response.append(token)
                yield token

            # Streaming completed successfully
            complete_text = ''.join(full_response)
            if not complete_text:
                self.__logger.error('Empty response received from stream')
                raise ChatException('Empty response received from stream')

            # Update agent's conversation history
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(complete_text)
            self.__logger.info('Streaming chat executed successfully')
            self.__logger.debug(
                'Complete response (first 100 chars): %s...',
                complete_text[:100] if complete_text else '',
            )

        except ChatException:
            self.__logger.error(
                'ChatException during streaming', exc_info=True
            )
            raise
        except Exception as e:
            self.__logger.error(
                'Error during streaming: %s', str(e), exc_info=True
            )
            raise ChatException(
                f'Error during streaming: {str(e)}',
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

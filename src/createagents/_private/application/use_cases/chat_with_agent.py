from typing import AsyncGenerator, List, Optional, Union

from ...domain import Agent, ChatException, RunType, TraceContext
from ...domain.interfaces import ITraceLogger, LoggerInterface
from ...infra import ChatMetrics
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

    def __init__(
        self,
        chat_repository: ChatRepository,
        logger: LoggerInterface,
        trace_logger: Optional[ITraceLogger] = None,
    ):
        """
        Initializes the Use Case with its dependencies.

        Args:
            chat_repository: Repository for AI communication.
            logger: Logger interface for logging operations.
            trace_logger: Optional trace logger for detailed tracing.
        """
        self.__chat_repository = chat_repository
        self.__logger = logger
        self.__trace_logger = trace_logger

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
        # Extract available tool names from the agent for validation
        available_tools = None
        if agent.tools:
            available_tools = [tool.name for tool in agent.tools]
            self.__logger.debug(
                'Available tools for validation: %s', available_tools
            )

        input_dto.validate(available_tools=available_tools)

        # Determine if streaming is enabled from agent config
        is_streaming = (
            agent.config.get('stream', False) if agent.config else False
        )

        # Create root trace context for this chat interaction
        trace_ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat_with_agent',
            agent_name=agent.name,
            model=agent.model,
            metadata={
                'message_length': len(input_dto.message),
                'streaming': is_streaming,
                'tools_available': len(agent.tools) if agent.tools else 0,
                'tool_names': available_tools or [],
            },
        )

        # Log start of trace with full user message
        if self.__trace_logger:
            self.__trace_logger.start_trace(
                trace_ctx,
                inputs={
                    'user_message': input_dto.message,
                    'tool_choice': input_dto.tool_choice,
                    'history_length': len(agent.history.to_dict_list()),
                },
            )

        # Prepare history with user message
        history = agent.history.to_dict_list()
        history.append({'role': 'user', 'content': input_dto.message})

        try:
            response = await self.__chat_repository.chat(
                model=agent.model,
                instructions=agent.instructions,
                config=agent.config or {},
                tools=agent.tools,
                history=history,
                tool_choice=input_dto.tool_choice,
                trace_context=trace_ctx,
            )

            if isinstance(response, AsyncGenerator):
                return self.__handle_streaming(
                    agent, input_dto, response, trace_ctx
                )

            # Standard non-streaming response
            if not response:
                self.__logger.error('Empty response received from repository')
                if self.__trace_logger:
                    self.__trace_logger.end_trace(
                        trace_ctx,
                        outputs={'error': 'Empty response'},
                        status='error',
                    )
                raise ChatException('Empty response received from repository')

            output_dto = ChatOutputDTO(response=response)

            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(response)

            # Log trace completion with full response
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={
                        'response': response,
                        'response_length': len(response),
                    },
                    status='success',
                )

            self.__logger.info(
                'Chat completed',
                extra={
                    'event': 'chat.completed',
                    'trace_id': trace_ctx.trace_id,
                    'run_id': trace_ctx.run_id,
                    'agent_name': agent.name,
                    'model': agent.model,
                    'streaming': False,
                    'message_length': len(input_dto.message),
                    'response_length': len(response),
                    'tools_available': len(agent.tools) if agent.tools else 0,
                    'elapsed_ms': trace_ctx.elapsed_ms,
                },
            )

            return output_dto

        except ChatException:
            self.__logger.error(
                'ChatException during chat execution', exc_info=True
            )
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={'error': 'ChatException'},
                    status='error',
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
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={'error': str(e), 'error_type': type(e).__name__},
                    status='error',
                )
            raise ChatException(user_msg.format(str(e))) from e
        except Exception as e:
            self.__logger.error('Unexpected error: %s', str(e), exc_info=True)
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={'error': str(e), 'error_type': type(e).__name__},
                    status='error',
                )
            raise ChatException(
                f'Unexpected error during communication with AI: {str(e)}',
                original_error=e,
            ) from e

    async def __handle_streaming(
        self,
        agent: Agent,
        input_dto: ChatInputDTO,
        stream: AsyncGenerator[str, None],
        trace_ctx: TraceContext,
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
            trace_ctx: The trace context for this interaction.

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
                if self.__trace_logger:
                    self.__trace_logger.end_trace(
                        trace_ctx,
                        outputs={'error': 'Empty stream response'},
                        status='error',
                    )
                raise ChatException('Empty response received from stream')

            # Update agent's conversation history
            agent.add_user_message(input_dto.message)
            agent.add_assistant_message(complete_text)

            # Log trace completion with full response
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={
                        'response': complete_text,
                        'response_length': len(complete_text),
                    },
                    status='success',
                )

            self.__logger.info(
                'Chat completed',
                extra={
                    'event': 'chat.completed',
                    'trace_id': trace_ctx.trace_id,
                    'run_id': trace_ctx.run_id,
                    'agent_name': agent.name,
                    'streaming': True,
                    'message_length': len(input_dto.message),
                    'response_length': len(complete_text),
                    'elapsed_ms': trace_ctx.elapsed_ms,
                },
            )

        except ChatException:
            self.__logger.error(
                'ChatException during streaming', exc_info=True
            )
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={'error': 'ChatException'},
                    status='error',
                )
            raise
        except Exception as e:
            self.__logger.error(
                'Error during streaming: %s', str(e), exc_info=True
            )
            if self.__trace_logger:
                self.__trace_logger.end_trace(
                    trace_ctx,
                    outputs={'error': str(e), 'error_type': type(e).__name__},
                    status='error',
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

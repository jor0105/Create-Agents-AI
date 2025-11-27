import time
from typing import Any, Dict, List, Optional

from ....application.interfaces import ChatRepository
from ....domain import BaseTool, ChatException, ToolExecutor
from ...config import (
    ChatMetrics,
    EnvironmentConfig,
    LoggingConfig,
    retry_with_backoff,
)
from .client_openai import ClientOpenAI
from .tool_call_parser import ToolCallParser
from .tool_schema_formatter import ToolSchemaFormatter


class OpenAIChatAdapter(ChatRepository):
    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__timeout = int(EnvironmentConfig.get_env('OPENAI_TIMEOUT', '30'))
        self.__max_retries = int(
            EnvironmentConfig.get_env('OPENAI_MAX_RETRIES', '3')
        )
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OPENAI_MAX_TOOL_ITERATIONS', '100')
        )

        try:
            api_key = EnvironmentConfig.get_api_key(
                ClientOpenAI.API_OPENAI_NAME
            )
            self.__client = ClientOpenAI.get_client(api_key)
            self.__logger.info(
                f'OpenAI adapter initialized (timeout: {self.__timeout}s, '
                f'max_retries: {self.__max_retries})'
            )
        except EnvironmentError as e:
            self.__logger.error(f'Error configuring OpenAI: {str(e)}')
            raise ChatException(f'Error configuring OpenAI: {str(e)}', e)

    @retry_with_backoff(
        max_attempts=3, initial_delay=1.0, exceptions=(Exception,)
    )
    def __call_openai_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Calls the OpenAI API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: Internal AI configuration.
            tools: Optional list of tool schemas for function calling.

        Returns:
            The API response.
        """
        chat_kwargs: Dict[str, Any] = {
            'model': model,
            'input': messages,
        }

        if tools:
            chat_kwargs['tools'] = tools
        if config:
            config_copy = config.copy()
            param_to_change: Dict[str, str] = {
                'reasoning': 'think',
                'max_output_tokens': 'max_tokens',
            }

            for api_key, config_key in param_to_change.items():
                if config_key in config_copy:
                    config_copy[api_key] = config_copy.pop(config_key)
            for key, config_data in config_copy.items():
                if 'reasoning' == key:
                    chat_kwargs['reasoning'] = {'effort': config_data}
                else:
                    chat_kwargs[key] = config_data

        response_api = self.__client.responses.create(**chat_kwargs)

        return response_api

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Sends a message to OpenAI and returns the response.

        Implements tool calling loop:
        1. Send message to LLM
        2. If LLM requests tool calls, execute them
        3. Send tool results back to LLM
        4. Repeat until LLM provides final response

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI configuration.
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools available to the agent.

        Returns:
            The model's response.

        Raises:
            ChatException: If a communication error occurs.
        """
        start_time = time.time()

        try:
            self.__logger.debug(f'Starting chat with model {model} on OpenAI.')

            messages = []
            if instructions and instructions.strip():
                messages.append({'role': 'system', 'content': instructions})
            messages.extend(history)
            messages.append({'role': 'user', 'content': user_ask})

            # Prepare tool schemas if tools are provided
            tool_schemas = None
            tool_executor = None
            if tools:
                tool_schemas = (
                    ToolSchemaFormatter.format_tools_for_responses_api(tools)
                )
                tool_executor = ToolExecutor(tools)
                self.__logger.debug(
                    f'Tools enabled: {[tool.name for tool in tools]}'
                )

            iteration = 0
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    f'OpenAI tool calling iteration {iteration}/{self.__max_tool_iterations}'
                )
                self.__logger.debug(
                    f'Current message history size: {len(messages)}'
                )

                # Call OpenAI API
                response_api = self.__call_openai_api(
                    model, messages, config, tool_schemas
                )

                if ToolCallParser.has_tool_calls(response_api):
                    self.__logger.info('Tool calls detected in response')

                    if tool_executor is None:
                        self.__logger.error(
                            'Tool calls detected but no tools were provided'
                        )
                        raise ChatException(
                            'Tool calls detected but no tools were provided to the agent'
                        )

                    # For Responses API, append output items to messages
                    output_items = (
                        ToolCallParser.get_assistant_message_with_tool_calls(
                            response_api
                        )
                    )
                    if output_items:
                        messages.extend(output_items)

                    tool_calls = ToolCallParser.extract_tool_calls(
                        response_api
                    )
                    self.__logger.debug(f'Executing {len(tool_calls)} tool(s)')

                    for tool_call in tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        self.__logger.debug(
                            f"Executing tool '{tool_name}' with args: {tool_args}"
                        )

                        execution_result = tool_executor.execute_tool(
                            tool_name, **tool_args
                        )

                        tool_result_msg = (
                            ToolCallParser.format_tool_results_for_llm(
                                tool_call_id=tool_id,
                                tool_name=tool_name,
                                result=(
                                    str(execution_result.result)
                                    if execution_result.success
                                    else str(execution_result.error)
                                ),
                            )
                        )
                        messages.append(tool_result_msg)

                    continue

                content: str = response_api.output_text
                if not content:
                    self.__logger.warning('OpenAI returned an empty response.')
                    raise ChatException('OpenAI returned an empty response.')

                # Record metrics
                latency = (time.time() - start_time) * 1000
                usage = getattr(response_api, 'usage', None)
                if usage:
                    tokens_used = getattr(usage, 'total_tokens', None)
                    prompt_tokens = getattr(usage, 'prompt_tokens', None)
                    completion_tokens = getattr(
                        usage, 'completion_tokens', None
                    )
                else:
                    tokens_used = None
                    prompt_tokens = None
                    completion_tokens = None

                metrics = ChatMetrics(
                    model=model,
                    latency_ms=latency,
                    tokens_used=tokens_used,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    success=True,
                )
                self.__metrics.append(metrics)

                self.__logger.info(f'Chat completed: {metrics}')
                self.__logger.debug(
                    f'Response (first 100 chars): {content[:100]}...'
                )

                self.__logger.debug(
                    f'Response after formatting (first 100 chars): {content[:100]}...'
                )

                return content

            self.__logger.warning(
                f'Max tool iterations ({self.__max_tool_iterations}) reached'
            )
            raise ChatException(
                f'Max tool calling iterations ({self.__max_tool_iterations}) exceeded'
            )

        except ChatException:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message='OpenAI chat error',
            )
            self.__metrics.append(metrics)
            raise
        except AttributeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f'Error accessing response: {str(e)}',
            )
            self.__metrics.append(metrics)
            self.__logger.error(f'Error accessing OpenAI response: {str(e)}')
            raise ChatException(
                f'Error accessing OpenAI response: {str(e)}', original_error=e
            )
        except IndexError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f'Unexpected format: {str(e)}',
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f'OpenAI response has an unexpected format: {str(e)}'
            )
            raise ChatException(
                f'OpenAI response has an unexpected format: {str(e)}',
                original_error=e,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=str(e),
            )
            self.__metrics.append(metrics)
            self.__logger.error(f'Error communicating with OpenAI: {str(e)}')
            raise ChatException(
                f'Error communicating with OpenAI: {str(e)}', original_error=e
            )

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()

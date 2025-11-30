import time
from typing import Any, Dict, List, Optional

from ....domain import BaseTool, ChatException, ToolExecutor
from ...config import ChatMetrics, EnvironmentConfig, LoggingConfig
from .openai_client import OpenAIClient
from .tool_call_parser import ToolCallParser
from .tool_schema_formatter import ToolSchemaFormatter


class OpenAIHandler:
    """Handles tool execution loop for OpenAI."""

    def __init__(
        self,
        client: OpenAIClient,
        metrics_list: Optional[List[ChatMetrics]] = None,
    ):
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics = metrics_list if metrics_list is not None else []
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OPENAI_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    def execute_tool_loop(
        self,
        model: str,
        instructions: Optional[str],
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> str:
        """Executes the tool calling loop."""
        start_time = time.time()

        # Prepare tool schemas if tools are provided
        tool_schemas = None
        tool_executor = None
        if tools:
            tool_schemas = ToolSchemaFormatter.format_tools_for_responses_api(
                tools
            )
            tool_executor = ToolExecutor(tools)
            self.__logger.debug(
                'Tools enabled: %s', [tool.name for tool in tools]
            )

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'OpenAI tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )
                self.__logger.debug(
                    'Current message history size: %s', len(messages)
                )

                # Call OpenAI API
                response_api = self.__client.call_api(
                    model, instructions, messages, config, tool_schemas
                )

                if ToolCallParser.has_tool_calls(response_api):
                    self.__logger.info('Tool calls detected in response')

                    if tool_executor is None:
                        self.__logger.error(
                            'Tool calls detected but no tools were provided'
                        )
                        raise ChatException(
                            'Tool calls detected but no tools were provided '
                            'to the agent'
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
                    self.__logger.debug(
                        'Executing %s tool(s)', len(tool_calls)
                    )

                    for tool_call in tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        self.__logger.debug(
                            "Executing tool '%s' with args: %s",
                            tool_name,
                            tool_args,
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
                self.__record_success_metrics(model, start_time, response_api)

                self.__logger.debug(
                    'Response (first 100 chars): %s...', content[:100]
                )

                self.__logger.debug(
                    'Response after formatting (first 100 chars): %s...',
                    content[:100],
                )

                return content

            self.__logger.warning(
                'Max tool iterations (%s) reached', self.__max_tool_iterations
            )
            raise ChatException(
                f'Max tool calling iterations '
                f'({self.__max_tool_iterations}) exceeded'
            )

        except ChatException:
            self.__record_error_metrics(model, start_time, 'OpenAI chat error')
            raise
        except AttributeError as e:
            self.__record_error_metrics(
                model, start_time, f'Error accessing response: {str(e)}'
            )
            self.__logger.error('Error accessing OpenAI response: %s', e)
            raise ChatException(
                f'Error accessing OpenAI response: {str(e)}', original_error=e
            ) from e
        except IndexError as e:
            self.__record_error_metrics(
                model, start_time, f'Unexpected format: {str(e)}'
            )
            self.__logger.error(
                'OpenAI response has an unexpected format: %s', e
            )
            raise ChatException(
                f'OpenAI response has an unexpected format: {str(e)}',
                original_error=e,
            ) from e
        except (ValueError, TypeError, KeyError) as e:
            self.__record_error_metrics(
                model, start_time, f'Data error: {str(e)}'
            )
            self.__logger.error('Data error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Data error communicating with OpenAI: {str(e)}',
                original_error=e,
            ) from e
        except Exception as e:
            self.__record_error_metrics(model, start_time, str(e))
            self.__logger.error('Error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Error communicating with OpenAI: {str(e)}', original_error=e
            ) from e

    def __record_success_metrics(
        self, model: str, start_time: float, response_api: Any
    ) -> None:
        latency = (time.time() - start_time) * 1000
        usage = getattr(response_api, 'usage', None)
        if usage:
            tokens_used = getattr(usage, 'total_tokens', None)
            prompt_tokens = getattr(usage, 'prompt_tokens', None)
            completion_tokens = getattr(usage, 'completion_tokens', None)
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
        self.__logger.info('Chat completed: %s', metrics)

    def __record_error_metrics(
        self, model: str, start_time: float, error_message: str
    ) -> None:
        latency = (time.time() - start_time) * 1000
        metrics = ChatMetrics(
            model=model,
            latency_ms=latency,
            success=False,
            error_message=error_message,
        )
        self.__metrics.append(metrics)

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics."""
        return self.__metrics.copy()

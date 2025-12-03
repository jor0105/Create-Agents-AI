import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from ....domain import BaseTool, ChatException
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    LoggerInterface,
)
from ....domain.services.tool_executor import ToolExecutor
from ...config import ChatMetrics, EnvironmentConfig
from .openai_client import OpenAIClient
from .tool_call_parser import ToolCallParser


class OpenAIHandler:
    """Handles tool execution loop for OpenAI.

    This handler follows SOLID principles:
    - SRP: Only handles the tool execution loop orchestration
    - OCP: Extensible via injected dependencies
    - DIP: Depends on abstractions (interfaces) not concretions

    Dependencies are injected via constructor for testability.
    """

    def __init__(
        self,
        client: OpenAIClient,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        tool_executor_factory: Optional[Any] = None,
    ):
        """Initialize the handler with injected dependencies.

        Args:
            client: OpenAI API client.
            logger: Logger instance for logging operations.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
            tool_executor_factory: Optional factory for creating tool executors.
                If None, uses default ToolExecutor.
        """
        self.__client = client
        self.__logger = logger
        self.__metrics_recorder = metrics_recorder
        self.__schema_builder = schema_builder
        self.__tool_executor_factory = tool_executor_factory
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OPENAI_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    async def execute_tool_loop(
        self,
        model: str,
        instructions: Optional[str],
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> str:
        """Executes the tool calling loop.

        Args:
            model: The model name to use.
            instructions: System instructions.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.

        Returns:
            The final response text from the model.
        """
        start_time = time.time()

        # Prepare tool schemas if tools are provided
        tool_schemas = None
        tool_executor = None
        formatted_tool_choice = None
        if tools:
            # Use injected schema builder
            tool_schemas = self.__schema_builder.format_tools(tools)
            # Create tool executor via factory or directly
            if self.__tool_executor_factory:
                tool_executor = self.__tool_executor_factory(
                    tools, self.__logger
                )
            else:
                tool_executor = ToolExecutor(tools, self.__logger)
            # Format tool_choice only if tools are provided
            formatted_tool_choice = self.__schema_builder.format_tool_choice(
                tool_choice, tools
            )
            self.__logger.debug(
                'Tools enabled: %s', [tool.name for tool in tools]
            )
            if formatted_tool_choice:
                self.__logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
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
                response_api = await self.__client.call_api(
                    model,
                    instructions,
                    messages,
                    config,
                    tool_schemas,
                    formatted_tool_choice,
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
                        'Executing %s tool(s) in parallel', len(tool_calls)
                    )

                    # Execute all tools in parallel using asyncio.gather
                    async def execute_single_tool(tool_call: Dict[str, Any]):
                        """Execute a single tool and return formatted result."""
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        self.__logger.debug(
                            "Executing tool '%s' with args: %s",
                            tool_name,
                            tool_args,
                        )

                        execution_result = await tool_executor.execute_tool(
                            tool_name, **tool_args
                        )

                        result_text = (
                            str(execution_result.result)
                            if execution_result.success
                            else str(execution_result.error)
                        )

                        self.__logger.info(
                            "Tool '%s' response [%s]: %s",
                            tool_name,
                            'success' if execution_result.success else 'error',
                            result_text[:200] + '...'
                            if len(result_text) > 200
                            else result_text,
                        )
                        self.__logger.debug(
                            "Tool '%s' full response (ID: %s): %s",
                            tool_name,
                            tool_id,
                            result_text,
                        )

                        return ToolCallParser.format_tool_results_for_llm(
                            tool_call_id=tool_id,
                            tool_name=tool_name,
                            result=result_text,
                        )

                    # Execute all tools in parallel
                    tool_results = await asyncio.gather(
                        *[execute_single_tool(tc) for tc in tool_calls],
                        return_exceptions=True,
                    )

                    # Process results and add to messages
                    for i, result in enumerate(tool_results):
                        if isinstance(result, Exception):
                            self.__logger.error(
                                "Tool '%s' failed with exception: %s",
                                tool_calls[i]['name'],
                                result,
                            )
                            # Add error result to messages
                            error_msg = (
                                ToolCallParser.format_tool_results_for_llm(
                                    tool_call_id=tool_calls[i]['id'],
                                    tool_name=tool_calls[i]['name'],
                                    result=f'Error: {str(result)}',
                                )
                            )
                            messages.append(error_msg)
                        else:
                            messages.append(result)

                    continue

                content: str = response_api.output_text
                if not content:
                    self.__logger.warning('OpenAI returned an empty response.')
                    raise ChatException('OpenAI returned an empty response.')

                # Record metrics
                self.__metrics_recorder.record_success(
                    model, start_time, response_api, provider_type='openai'
                )

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
            self.__metrics_recorder.record_error(
                model, start_time, 'OpenAI chat error'
            )
            raise
        except AttributeError as e:
            self.__metrics_recorder.record_error(
                model, start_time, f'Error accessing response: {str(e)}'
            )
            self.__logger.error('Error accessing OpenAI response: %s', e)
            raise ChatException(
                f'Error accessing OpenAI response: {str(e)}', original_error=e
            ) from e
        except IndexError as e:
            self.__metrics_recorder.record_error(
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
            self.__metrics_recorder.record_error(
                model, start_time, f'Data error: {str(e)}'
            )
            self.__logger.error('Data error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Data error communicating with OpenAI: {str(e)}',
                original_error=e,
            ) from e
        except Exception as e:
            self.__metrics_recorder.record_error(model, start_time, str(e))
            self.__logger.error('Error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Error communicating with OpenAI: {str(e)}', original_error=e
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics."""
        return self.__metrics_recorder.get_metrics()

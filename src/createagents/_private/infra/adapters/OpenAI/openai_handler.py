import asyncio
import time
from typing import Any, Dict, List, Optional

from ....domain import (
    BaseTool,
    ChatException,
    RunType,
    TraceContext,
    ToolChoiceType,
)
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    ITraceLogger,
    LoggerInterface,
)
from ...config import ChatMetrics, EnvironmentConfig
from ..Common import BaseHandler
from .openai_client import OpenAIClient
from .openai_tool_call_parser import OpenAIToolCallParser


class OpenAIHandler(BaseHandler):
    """Handles tool execution loop for OpenAI.

    This handler follows SOLID principles:
    - SRP: Only handles the tool execution loop orchestration
    - OCP: Extensible via injected dependencies
    - DIP: Depends on abstractions (interfaces) not concretions

    Dependencies are injected via constructor for testability.
    Inherits common tool executor factory logic from BaseHandler.
    """

    def __init__(
        self,
        client: OpenAIClient,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        trace_logger: Optional[ITraceLogger] = None,
    ):
        """Initialize the handler with injected dependencies.

        Args:
            client: OpenAI API client.
            logger: Logger instance for logging operations.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
            trace_logger: Optional trace logger for persistent tracing.
        """
        super().__init__(
            logger=logger,
            metrics_recorder=metrics_recorder,
            schema_builder=schema_builder,
            trace_logger=trace_logger,
        )
        self.__client = client
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OPENAI_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    async def execute_tool_loop(
        self,
        model: str,
        instructions: Optional[str],
        history: List[Dict[str, str]],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[ToolChoiceType] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> str:
        """Executes the tool calling loop.

        Args:
            model: The model name to use.
            instructions: System instructions.
            history: List of history in the conversation.
            config: Configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.
            trace_context: Optional trace context for distributed tracing.

        Returns:
            The final response text from the model.
        """
        start_time = time.time()

        # Build trace extra for consistent logging
        trace_extra: Dict[str, Any] = {}
        if trace_context:
            trace_extra = trace_context.to_log_extra()

        # Prepare tool schemas if tools are provided
        tool_schemas = None
        tool_executor = None
        formatted_tool_choice = None
        if tools:
            # Use injected schema builder
            tool_schemas = self._schema_builder.multiple_format(tools)
            # Create tool executor using inherited factory from BaseHandler
            tool_executor = self._create_tool_executor(tools)
            # Format tool_choice only if tools are provided
            formatted_tool_choice = self._schema_builder.format_tool_choice(
                tool_choice, tools
            )
            self._logger.debug(
                'Tools enabled: %s', [tool.name for tool in tools]
            )
            if formatted_tool_choice:
                self._logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
                )

        iteration = 0
        # Track whether we should apply tool_choice (only on first iteration)
        # After a tool is executed, we reset to None to allow the model to respond
        current_tool_choice = formatted_tool_choice
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                # Create child trace context for this LLM iteration
                iteration_ctx = None
                if trace_context:
                    iteration_ctx = trace_context.create_child(
                        run_type=RunType.LLM,
                        operation=f'openai_iteration_{iteration}',
                        metadata={'iteration': iteration},
                    )
                    trace_extra = iteration_ctx.to_log_extra()

                self._logger.info(
                    'OpenAI tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                    extra={
                        **trace_extra,
                        'event': 'llm.iteration.start',
                        'iteration': iteration,
                        'max_iterations': self.__max_tool_iterations,
                    },
                )
                self._logger.debug(
                    'Current message history size: %s', len(history)
                )

                # Log LLM request via TraceLogger (persists to TraceStore)
                if self._trace_logger and iteration_ctx:
                    self._trace_logger.log_llm_request(
                        iteration_ctx,
                        model=model,
                        messages_count=len(history),
                        tools_available=len(tools) if tools else None,
                    )

                # Call OpenAI API
                llm_start_time = time.time()
                response_api = await self.__client.call_api(
                    model,
                    instructions,
                    history,
                    config,
                    tool_schemas,
                    current_tool_choice,
                )
                llm_duration_ms = (time.time() - llm_start_time) * 1000

                if OpenAIToolCallParser.has_tool_calls(response_api):
                    tool_calls = OpenAIToolCallParser.extract_tool_calls(
                        response_api
                    )

                    # Log LLM response with tool calls via TraceLogger
                    if self._trace_logger and iteration_ctx:
                        self._trace_logger.log_llm_response(
                            iteration_ctx,
                            model=model,
                            response_preview=f'Tool calls: {[tc["name"] for tc in tool_calls]}',
                            has_tool_calls=True,
                            tool_calls_count=len(tool_calls),
                            duration_ms=llm_duration_ms,
                        )

                    self._logger.info(
                        'Tool calls detected in response',
                        extra={
                            **trace_extra,
                            'event': 'llm.tool_calls_detected',
                        },
                    )

                    if tool_executor is None:
                        self._logger.error(
                            'Tool calls detected but no tools were provided'
                        )
                        raise ChatException(
                            'Tool calls detected but no tools were provided '
                            'to the agent'
                        )

                    # For Responses API, append output items to history
                    output_items = OpenAIToolCallParser.get_assistant_message_with_tool_calls(
                        response_api
                    )
                    if output_items:
                        history.extend(output_items)

                    self._logger.info(
                        'Executing %s tool(s) in parallel',
                        len(tool_calls),
                        extra={
                            **trace_extra,
                            'event': 'tool.execution.start',
                            'tool_count': len(tool_calls),
                            'tool_names': [tc['name'] for tc in tool_calls],
                        },
                    )

                    # Execute all tools in parallel using asyncio.gather
                    async def execute_single_tool(
                        tool_call: Dict[str, Any],
                        parent_ctx: Optional[TraceContext] = None,
                    ):
                        """Execute a single tool and return formatted result."""
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']
                        tool_start_time = time.time()

                        # Create tool trace context
                        tool_ctx = None
                        tool_trace_extra: Dict[str, Any] = {}
                        if parent_ctx:
                            tool_ctx = parent_ctx.create_child(
                                run_type=RunType.TOOL,
                                operation=f'tool_{tool_name}',
                                metadata={
                                    'tool_name': tool_name,
                                    'tool_call_id': tool_id,
                                },
                            )
                            tool_trace_extra = tool_ctx.to_log_extra()

                        # Log tool call start via TraceLogger (persists to TraceStore)
                        if self._trace_logger and tool_ctx:
                            self._trace_logger.log_tool_call(
                                tool_ctx, tool_name, tool_id, tool_args
                            )

                        self._logger.info(
                            "🔧 Executing tool '%s'",
                            tool_name,
                            extra={
                                **tool_trace_extra,
                                'event': 'tool.call.start',
                                'tool_name': tool_name,
                                'tool_call_id': tool_id,
                                'tool_args': self._sanitize_for_logging(
                                    tool_args
                                ),
                            },
                        )

                        execution_result = await tool_executor.execute_tool(
                            tool_name, **tool_args
                        )

                        result_text = (
                            str(execution_result.result)
                            if execution_result.success
                            else str(execution_result.error)
                        )

                        status = (
                            'success' if execution_result.success else 'error'
                        )
                        tool_duration_ms = (
                            time.time() - tool_start_time
                        ) * 1000

                        # Log tool result via TraceLogger (persists to TraceStore)
                        if self._trace_logger and tool_ctx:
                            self._trace_logger.log_tool_result(
                                tool_ctx,
                                tool_name,
                                tool_id,
                                result_text,
                                tool_duration_ms,
                                success=execution_result.success,
                            )

                        self._logger.info(
                            "🔧 Tool '%s' completed [%s]",
                            tool_name,
                            status,
                            extra={
                                **tool_trace_extra,
                                'event': 'tool.call.end',
                                'tool_name': tool_name,
                                'tool_call_id': tool_id,
                                'status': status,
                                'result_preview': (
                                    result_text[:500] + '...'
                                    if len(result_text) > 500
                                    else result_text
                                ),
                                'result_length': len(result_text),
                            },
                        )
                        self._logger.debug(
                            "Tool '%s' full response (ID: %s): %s",
                            tool_name,
                            tool_id,
                            result_text,
                        )

                        return (
                            OpenAIToolCallParser.format_tool_results_for_llm(
                                tool_call_id=tool_id,
                                tool_name=tool_name,
                                result=result_text,
                            )
                        )

                    # Execute all tools in parallel
                    tool_results = await asyncio.gather(
                        *[
                            execute_single_tool(tc, iteration_ctx)
                            for tc in tool_calls
                        ],
                        return_exceptions=True,
                    )

                    # Process results and add to history
                    for i, result in enumerate(tool_results):
                        if isinstance(result, BaseException):
                            self._logger.error(
                                "Tool '%s' failed with exception: %s",
                                tool_calls[i]['name'],
                                result,
                                extra={
                                    **trace_extra,
                                    'event': 'tool.call.error',
                                    'tool_name': tool_calls[i]['name'],
                                    'tool_call_id': tool_calls[i]['id'],
                                    'error': str(result),
                                },
                            )
                            # Add error result to history
                            error_msg = OpenAIToolCallParser.format_tool_results_for_llm(
                                tool_call_id=tool_calls[i]['id'],
                                tool_name=tool_calls[i]['name'],
                                result=f'Error: {str(result)}',
                            )
                            # Type is Dict[str, Any] from format_tool_results_for_llm
                            history.append(error_msg)  # type: ignore[arg-type]
                        else:
                            # After isinstance check, result is Dict[str, Any]
                            history.append(result)  # type: ignore[arg-type]

                    # Reset tool_choice after first tool execution
                    # This prevents infinite loops when a specific tool is forced
                    # After the tool is executed, we let the model decide what to do next
                    current_tool_choice = None

                    continue

                content: str = response_api.output_text
                if not content:
                    self._logger.warning(
                        'OpenAI returned an empty response.',
                        extra={
                            **trace_extra,
                            'event': 'llm.response.empty',
                        },
                    )
                    raise ChatException('OpenAI returned an empty response.')

                # Log LLM text response via TraceLogger (persists to TraceStore)
                if self._trace_logger and iteration_ctx:
                    # Extract token usage if available
                    tokens_used = None
                    usage = getattr(response_api, 'usage', None)
                    if usage:
                        tokens_used = getattr(usage, 'total_tokens', None)

                    self._trace_logger.log_llm_response(
                        iteration_ctx,
                        model=model,
                        response_preview=content,
                        has_tool_calls=False,
                        tool_calls_count=0,
                        tokens_used=tokens_used,
                        duration_ms=llm_duration_ms,
                    )

                # Record metrics
                self._metrics_recorder.record_success(
                    model, start_time, response_api, provider_type='openai'
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                self._logger.info(
                    '🤖 OpenAI response received',
                    extra={
                        **trace_extra,
                        'event': 'llm.response.complete',
                        'model': model,
                        'iteration': iteration,
                        'elapsed_ms': elapsed_ms,
                        'response_preview': (
                            content[:300] + '...'
                            if len(content) > 300
                            else content
                        ),
                        'response_length': len(content),
                    },
                )

                return content

            self._logger.warning(
                'Max tool iterations (%s) reached', self.__max_tool_iterations
            )
            raise ChatException(
                f'Max tool calling iterations '
                f'({self.__max_tool_iterations}) exceeded'
            )

        except ChatException:
            self._metrics_recorder.record_error(
                model, start_time, 'OpenAI chat error'
            )
            raise
        except AttributeError as e:
            self._metrics_recorder.record_error(
                model, start_time, f'Error accessing response: {str(e)}'
            )
            self._logger.error('Error accessing OpenAI response: %s', e)
            raise ChatException(
                f'Error accessing OpenAI response: {str(e)}', original_error=e
            ) from e
        except IndexError as e:
            self._metrics_recorder.record_error(
                model, start_time, f'Unexpected format: {str(e)}'
            )
            self._logger.error(
                'OpenAI response has an unexpected format: %s', e
            )
            raise ChatException(
                f'OpenAI response has an unexpected format: {str(e)}',
                original_error=e,
            ) from e
        except (ValueError, TypeError, KeyError) as e:
            self._metrics_recorder.record_error(
                model, start_time, f'Data error: {str(e)}'
            )
            self._logger.error('Data error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Data error communicating with OpenAI: {str(e)}',
                original_error=e,
            ) from e
        except Exception as e:
            self._metrics_recorder.record_error(model, start_time, str(e))
            self._logger.error('Error communicating with OpenAI: %s', e)
            raise ChatException(
                f'Error communicating with OpenAI: {str(e)}', original_error=e
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics."""
        return self._metrics_recorder.get_metrics()

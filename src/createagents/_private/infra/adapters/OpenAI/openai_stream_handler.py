import asyncio
import time
from typing import Any, Dict, AsyncGenerator, List, Optional

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
from ...config import EnvironmentConfig
from ..Common import BaseHandler
from .openai_client import OpenAIClient
from .openai_tool_call_parser import OpenAIToolCallParser


class OpenAIStreamHandler(BaseHandler):
    """Handles streaming responses from OpenAI with tool calling support.

    This handler follows Clean Architecture and SOLID principles:
    - All dependencies are injected via constructor (DIP)
    - Uses interfaces for metrics and schema building (OCP)
    - Single responsibility: manages streaming response flow
    - Inherits common tool executor factory logic from BaseHandler
    """

    def __init__(
        self,
        client: OpenAIClient,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        trace_logger: Optional[ITraceLogger] = None,
    ):
        """Initialize the stream handler with injected dependencies.

        Args:
            client: OpenAI API client.
            logger: Logger instance for logging.
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

    async def handle_stream(
        self,
        model: str,
        instructions: Optional[str],
        history: List[Dict[str, str]],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[ToolChoiceType] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the OpenAI API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.

        Args:
            model: The model name to use.
            instructions: System instructions.
            history: List of history in the conversation.
            config: Configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.
            trace_context: Optional trace context for distributed tracing.
        """
        start_time = time.time()

        # Build trace extra for consistent logging
        trace_extra: Dict[str, Any] = {}
        if trace_context:
            trace_extra = trace_context.to_log_extra()

        # Prepare tool schemas and executor if tools are provided
        tool_schemas = None
        tool_executor = None
        formatted_tool_choice = None
        if tools:
            tool_schemas = self._schema_builder.multiple_format(tools)
            tool_executor = self._create_tool_executor(tools)
            formatted_tool_choice = self._schema_builder.format_tool_choice(
                tool_choice, tools
            )
            self._logger.debug(
                'Streaming with tools enabled: %s',
                [tool.name for tool in tools],
            )
            if formatted_tool_choice:
                self._logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
                )

        self._logger.debug('Streaming mode enabled for OpenAI')

        # Accumulate token counts across all iterations (for tool calls)
        total_prompt_tokens = 0
        total_completion_tokens = 0

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
                        operation=f'openai_stream_iteration_{iteration}',
                        metadata={'iteration': iteration, 'streaming': True},
                    )
                    trace_extra = iteration_ctx.to_log_extra()

                self._logger.info(
                    'OpenAI streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                    extra={
                        **trace_extra,
                        'event': 'llm.stream.iteration.start',
                        'iteration': iteration,
                        'max_iterations': self.__max_tool_iterations,
                    },
                )

                # Call OpenAI API with streaming enabled
                stream_response = await self.__client.call_api(
                    model,
                    instructions,
                    history,
                    config,
                    tool_schemas,
                    current_tool_choice,
                )

                self._logger.debug(
                    'Streaming response received, iterating events'
                )

                # Track response state
                full_response = None
                has_yielded_content = False

                # Process streaming events from OpenAI Responses API
                async for event in stream_response:
                    event_type = getattr(event, 'type', None)

                    # Yield text tokens as they arrive
                    if event_type == 'response.output_text.delta':
                        if hasattr(event, 'delta'):
                            token = event.delta
                            if token:
                                yield token
                                has_yielded_content = True

                    elif event_type == 'response.content_part.added':
                        if hasattr(event, 'content_part'):
                            content_part = event.content_part
                            if hasattr(content_part, 'text'):
                                token = content_part.text
                                if token:
                                    yield token
                                    has_yielded_content = True

                    # Capture the completed event with full response
                    elif event_type == 'response.completed':
                        full_response = getattr(event, 'response', None)

                # Check if we have a valid response
                if not full_response:
                    self._logger.warning(
                        'No response object received from stream'
                    )
                    break

                # Extract text from full response if no deltas were streamed
                if not has_yielded_content:
                    if (
                        hasattr(full_response, 'output')
                        and full_response.output
                    ):
                        for item in full_response.output:
                            item_type = getattr(item, 'type', None)
                            if item_type == 'text':
                                text_content = getattr(item, 'text', None)
                                if text_content:
                                    yield text_content
                                    has_yielded_content = True

                # Extract and accumulate token usage from this iteration
                usage = getattr(full_response, 'usage', None)
                if usage:
                    prompt_tokens = getattr(usage, 'input_tokens', None)
                    completion_tokens = getattr(usage, 'output_tokens', None)
                    if prompt_tokens:
                        total_prompt_tokens += prompt_tokens
                    if completion_tokens:
                        total_completion_tokens += completion_tokens
                    self._logger.debug(
                        'Iteration %s tokens - prompt: %s, completion: %s',
                        iteration,
                        prompt_tokens,
                        completion_tokens,
                    )

                # Execute tool calls if present
                if tool_executor and OpenAIToolCallParser.has_tool_calls(
                    full_response
                ):
                    self._logger.info(
                        'Tool calls detected in streaming response',
                        extra={
                            **trace_extra,
                            'event': 'llm.stream.tool_calls_detected',
                        },
                    )
                    # Add output items to history for context
                    output_items = OpenAIToolCallParser.get_assistant_message_with_tool_calls(
                        full_response
                    )
                    if output_items:
                        history.extend(output_items)

                    # Extract and execute tool calls in parallel
                    tool_calls = OpenAIToolCallParser.extract_tool_calls(
                        full_response
                    )
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
                    current_tool_choice = None

                    # Continue to next iteration for final response
                    continue

                # Response complete, no tool calls - end stream
                break

            if iteration >= self.__max_tool_iterations:
                self._logger.warning(
                    'Max tool iterations (%s) reached during streaming',
                    self.__max_tool_iterations,
                )

            # Record metrics after streaming completes with accumulated tokens
            latency = (time.time() - start_time) * 1000
            total_tokens = (
                total_prompt_tokens + total_completion_tokens
                if total_prompt_tokens or total_completion_tokens
                else None
            )
            self._metrics_recorder.record_success_with_values(
                model=model,
                latency_ms=latency,
                tokens_used=total_tokens,
                prompt_tokens=total_prompt_tokens
                if total_prompt_tokens
                else None,
                completion_tokens=total_completion_tokens
                if total_completion_tokens
                else None,
            )
            self._logger.info(
                '🤖 Streaming chat completed',
                extra={
                    **trace_extra,
                    'event': 'llm.stream.complete',
                    'model': model,
                    'latency_ms': latency,
                    'total_tokens': total_tokens,
                    'prompt_tokens': total_prompt_tokens,
                    'completion_tokens': total_completion_tokens,
                    'iterations': iteration,
                },
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._metrics_recorder.record_error_with_values(
                model=model,
                latency_ms=latency,
                error_message=str(e),
            )
            self._logger.error(
                'Error during streaming: %s',
                e,
                extra={
                    **trace_extra,
                    'event': 'llm.stream.error',
                    'error': str(e),
                    'error_type': type(e).__name__,
                },
            )
            raise ChatException(
                f'Error during OpenAI streaming: {str(e)}',
                original_error=e,
            ) from e

import asyncio
import time
from typing import Any, Dict, AsyncGenerator, List, Optional

from ....domain import (
    ChatException,
    BaseTool,
    RunType,
    TraceContext,
    ToolChoiceType,
    ToolChoice,
    ToolChoiceMode,
)
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    ITraceLogger,
    LoggerInterface,
)
from ...config import EnvironmentConfig
from ..Common import BaseHandler
from .ollama_client import OllamaClient


class OllamaStreamHandler(BaseHandler):
    """Handles streaming responses from Ollama with tool calling support.

    This handler follows Clean Architecture and SOLID principles:
    - All dependencies are injected via constructor (DIP)
    - Uses interfaces for metrics and schema building (OCP)
    - Single responsibility: manages streaming response flow
    - Inherits common tool executor factory logic from BaseHandler
    """

    def __init__(
        self,
        client: OllamaClient,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        trace_logger: Optional[ITraceLogger] = None,
    ):
        """Initialize the stream handler with injected dependencies.

        Args:
            client: Ollama API client.
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
            EnvironmentConfig.get_env('OLLAMA_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    async def handle_stream(
        self,
        model: str,
        history: List[Dict[str, str]],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[ToolChoiceType] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the Ollama API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.

        Args:
            model: The model name to use.
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

        # Check if tool_choice='none' - if so, don't send tools to model
        # This simulates the tool_choice='none' behavior since Ollama doesn't
        # support the tool_choice parameter natively
        is_tool_choice_none = (
            tool_choice == 'none'
            or (
                isinstance(tool_choice, dict)
                and tool_choice.get('type') == 'none'
            )
            or (
                isinstance(tool_choice, ToolChoice)
                and tool_choice.mode == ToolChoiceMode.NONE
            )
        )

        if tools and not is_tool_choice_none:
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
        elif is_tool_choice_none:
            self._logger.debug(
                "tool_choice='none' - tools disabled for this request"
            )

        # Accumulate metrics across all iterations (for tool calls)
        total_prompt_tokens = 0
        total_completion_tokens = 0

        iteration = 0
        # Track whether we should apply tool_choice (only on first iteration)
        current_tool_choice = formatted_tool_choice
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1

                # Create child trace context for this LLM iteration
                iteration_ctx = None
                if trace_context:
                    iteration_ctx = trace_context.create_child(
                        run_type=RunType.LLM,
                        operation=f'ollama_stream_iteration_{iteration}',
                        metadata={'iteration': iteration, 'streaming': True},
                    )
                    trace_extra = iteration_ctx.to_log_extra()

                self._logger.info(
                    'Ollama streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                    extra={
                        **trace_extra,
                        'event': 'llm.stream.iteration.start',
                        'iteration': iteration,
                        'max_iterations': self.__max_tool_iterations,
                    },
                )

                stream_response = await self.__client.call_api(
                    model,
                    history,
                    config,
                    tool_schemas,
                    current_tool_choice,
                )

                has_yielded_content = False
                last_chunk = None
                tool_call_detected = False

                # OPTIMIZATION: Check for tool calls in EACH chunk as it arrives
                async for chunk in stream_response:
                    last_chunk = chunk

                    # EARLY DETECTION: Check if THIS chunk has tool calls
                    if (
                        tool_executor
                        and hasattr(chunk, 'message')
                        and hasattr(chunk.message, 'tool_calls')
                        and chunk.message.tool_calls
                    ):
                        tool_call_detected = True
                        self._logger.debug(
                            'Tool calls detected early in stream, will break'
                        )
                        # Break immediately - don't wait for rest of stream
                        break

                    # Yield content tokens as they arrive
                    if hasattr(chunk, 'message') and hasattr(
                        chunk.message, 'content'
                    ):
                        token = chunk.message.content
                        if token:
                            yield token
                            has_yielded_content = True

                # Extract metrics from the last chunk (Ollama sends metrics in final chunk)
                if last_chunk:
                    # Token counts
                    prompt_eval_count = getattr(
                        last_chunk, 'prompt_eval_count', None
                    )
                    eval_count = getattr(last_chunk, 'eval_count', None)
                    if prompt_eval_count:
                        total_prompt_tokens += prompt_eval_count
                    if eval_count:
                        total_completion_tokens += eval_count

                    self._logger.debug(
                        'Iteration %s tokens - prompt: %s, completion: %s',
                        iteration,
                        prompt_eval_count,
                        eval_count,
                    )

                # Process tool calls if detected
                if tool_call_detected and last_chunk and tool_executor:
                    self._logger.info(
                        'Tool calls detected, executing tools',
                        extra={
                            **trace_extra,
                            'event': 'llm.stream.tool_calls_detected',
                        },
                    )

                    # Add assistant message with tool calls to history
                    history.append(last_chunk.message)

                    # Execute tool calls in parallel
                    tool_calls = last_chunk.message.tool_calls
                    self._logger.info(
                        'Executing %s tool(s) in parallel',
                        len(tool_calls),
                        extra={
                            **trace_extra,
                            'event': 'tool.execution.start',
                            'tool_count': len(tool_calls),
                            'tool_names': [
                                tc.function.name for tc in tool_calls
                            ],
                        },
                    )

                    # Execute all tools in parallel using asyncio.gather
                    async def execute_single_tool(tool_call):
                        """Execute a single tool and return formatted result."""
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        tool_start_time = time.time()

                        # Create tool trace context
                        tool_ctx = None
                        tool_trace_extra: Dict[str, Any] = {}
                        if iteration_ctx:
                            tool_ctx = iteration_ctx.create_child(
                                run_type=RunType.TOOL,
                                operation=f'tool_{tool_name}',
                                metadata={'tool_name': tool_name},
                            )
                            tool_trace_extra = tool_ctx.to_log_extra()

                        # Log tool call start via TraceLogger (persists to TraceStore)
                        tool_call_id = f'ollama_stream_{tool_name}_{int(time.time() * 1000)}'
                        if self._trace_logger and tool_ctx:
                            self._trace_logger.log_tool_call(
                                tool_ctx, tool_name, tool_call_id, tool_args
                            )

                        self._logger.info(
                            "🔧 Executing tool '%s'",
                            tool_name,
                            extra={
                                **tool_trace_extra,
                                'event': 'tool.call.start',
                                'tool_name': tool_name,
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
                            else f'Error: {execution_result.error}'
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
                                tool_call_id,
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
                                'status': status,
                                'result_preview': (
                                    result_text[:500] + '...'
                                    if len(result_text) > 500
                                    else result_text
                                ),
                                'result_length': len(result_text),
                            },
                        )

                        return {
                            'role': 'tool',
                            'tool_name': tool_name,
                            'content': result_text,
                        }

                    # Execute all tools in parallel
                    tool_results = await asyncio.gather(
                        *[execute_single_tool(tc) for tc in tool_calls],
                        return_exceptions=True,
                    )

                    # Process results and add to history
                    for i, result in enumerate(tool_results):
                        if isinstance(result, BaseException):
                            tool_name = tool_calls[i].function.name
                            self._logger.error(
                                "Tool '%s' failed with exception: %s",
                                tool_name,
                                result,
                                extra={
                                    **trace_extra,
                                    'event': 'tool.call.error',
                                    'tool_name': tool_name,
                                    'error': str(result),
                                },
                            )
                            # Error message dict for Ollama tool response format
                            history.append(  # type: ignore[arg-type]
                                {
                                    'role': 'tool',
                                    'tool_name': tool_name,
                                    'content': f'Error: {str(result)}',
                                }
                            )
                        else:
                            # After isinstance check, result is Dict[str, Any]
                            history.append(result)  # type: ignore[arg-type]

                    # Reset tool_choice after first tool execution
                    current_tool_choice = None

                    # Continue to next iteration to get final response
                    # Reset for next iteration
                    has_yielded_content = False
                    tool_call_detected = False
                    continue

                # If we yielded content and no tool calls, we're done
                if has_yielded_content:
                    break

                # If this was a tool-only iteration (no content), continue to next iteration
                if tool_call_detected and not has_yielded_content:
                    self._logger.debug(
                        'Tool-only iteration, continuing to next'
                    )
                    continue

                # If we didn't yield anything and no tool calls, something's wrong
                if not has_yielded_content and not tool_call_detected:
                    self._logger.warning(
                        'No content yielded in streaming response'
                    )
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
                prompt_tokens=(
                    total_prompt_tokens if total_prompt_tokens else None
                ),
                completion_tokens=(
                    total_completion_tokens
                    if total_completion_tokens
                    else None
                ),
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
                f'Error during Ollama streaming: {str(e)}', original_error=e
            ) from e
        finally:
            await self.__client.stop_model(model)

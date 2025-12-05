import asyncio
import time
from typing import Any, Dict, List, Optional

from ....domain import (
    BaseTool,
    ChatException,
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
from ...config import ChatMetrics, EnvironmentConfig
from ..Common import BaseHandler
from .ollama_client import OllamaClient


class OllamaHandler(BaseHandler):
    """Handles tool execution loop for Ollama.

    This handler follows Clean Architecture and SOLID principles:
    - All dependencies are injected via constructor (DIP)
    - Uses interfaces for metrics and schema building (OCP)
    - Single responsibility: manages tool execution loop
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
        """Initialize the handler with injected dependencies.

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

    async def execute_tool_loop(
        self,
        model: str,
        history: List[Dict[str, str]],
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[ToolChoiceType] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> str:
        """
        Executes the tool calling loop.

        Args:
            model: The model name to use.
            history: List of history in the conversation.
            config: Configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.
            trace_context: Optional trace context for distributed tracing.

        Returns:
            The final response text from the model.

        Limitation:
            The native Ollama API (/api/chat) does NOT support the tool_choice parameter.
            The parameter is formatted for future compatibility, but is ignored by the API.
            If you need strict tool selection (e.g. required, specific), use the OpenAI-compatible endpoint (/v1/chat/completions).
        """
        start_time = time.time()

        # Build trace extra for consistent logging
        trace_extra: Dict[str, Any] = {}
        if trace_context:
            trace_extra = trace_context.to_log_extra()

        tool_executor = None
        tool_schemas = None
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
            tool_executor = self._create_tool_executor(tools)
            tool_schemas = self._schema_builder.multiple_format(tools)
            formatted_tool_choice = self._schema_builder.format_tool_choice(
                tool_choice, tools
            )
            if formatted_tool_choice:
                self._logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
                )
        elif is_tool_choice_none:
            self._logger.debug(
                "tool_choice='none' - tools disabled for this request"
            )

        iteration = 0
        final_response = None
        empty_response_count = 0
        max_empty_responses = 2
        response_api = None
        iteration_ctx = None
        # Track whether we should apply tool_choice (only on first iteration)
        current_tool_choice = formatted_tool_choice

        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1

                # Create child trace context for this LLM iteration
                if trace_context:
                    iteration_ctx = trace_context.create_child(
                        run_type=RunType.LLM,
                        operation=f'ollama_iteration_{iteration}',
                        metadata={'iteration': iteration},
                    )
                    trace_extra = iteration_ctx.to_log_extra()

                self._logger.info(
                    'Ollama tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                    extra={
                        **trace_extra,
                        'event': 'llm.iteration.start',
                        'iteration': iteration,
                        'max_iterations': self.__max_tool_iterations,
                    },
                )

                # Log LLM request via TraceLogger (persists to TraceStore)
                if self._trace_logger and iteration_ctx:
                    self._trace_logger.log_llm_request(
                        iteration_ctx,
                        model=model,
                        messages_count=len(history),
                        tools_available=len(tools) if tools else None,
                    )

                llm_start_time = time.time()
                response_api = await self.__client.call_api(
                    model,
                    history,
                    config,
                    tool_schemas,
                    current_tool_choice,
                )
                llm_duration_ms = (time.time() - llm_start_time) * 1000

                if (
                    hasattr(response_api.message, 'tool_calls')
                    and response_api.message.tool_calls
                ):
                    tool_calls = response_api.message.tool_calls

                    # Log LLM response with tool calls via TraceLogger
                    if self._trace_logger and iteration_ctx:
                        # Extract token usage from Ollama response
                        input_tokens = getattr(
                            response_api, 'prompt_eval_count', None
                        )
                        output_tokens = getattr(
                            response_api, 'eval_count', None
                        )
                        total_tokens = None
                        if input_tokens and output_tokens:
                            total_tokens = input_tokens + output_tokens

                        self._trace_logger.log_llm_response(
                            iteration_ctx,
                            model=model,
                            response_preview=f'Tool calls: {[tc.function.name for tc in tool_calls]}',
                            has_tool_calls=True,
                            tool_calls_count=len(tool_calls),
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens,
                            duration_ms=llm_duration_ms,
                        )

                    self._logger.info(
                        'Tool calls detected in response',
                        extra={
                            **trace_extra,
                            'event': 'llm.tool_calls_detected',
                        },
                    )
                    await self.__handle_tool_calls(
                        response_api,
                        history,
                        tool_executor,
                        iteration_ctx,
                        trace_extra,
                    )
                    # Reset tool_choice after first tool execution
                    current_tool_choice = None
                    continue

                content = response_api.message.content

                if not content:
                    empty_response_count += 1
                    if empty_response_count >= max_empty_responses:
                        summary = self.__generate_summary_from_tools(history)
                        if summary:
                            final_response = summary
                            break
                        raise ChatException(
                            'Ollama returned multiple empty responses.'
                        )

                    # Retry with simple prompt
                    retry_history = history.copy()
                    retry_history.append(
                        {
                            'role': 'user',
                            'content': (
                                'Based on the information gathered, please '
                                'provide a final answer to the original '
                                'question.'
                            ),
                        }
                    )
                    response_api = await self.__client.call_api(
                        model, retry_history, config, None
                    )
                    content = response_api.message.content
                    if content:
                        final_response = content
                        break
                    continue

                final_response = content

                # Log LLM text response via TraceLogger (persists to TraceStore)
                if self._trace_logger and iteration_ctx:
                    # Extract token usage from Ollama response
                    input_tokens = getattr(
                        response_api, 'prompt_eval_count', None
                    )
                    output_tokens = getattr(response_api, 'eval_count', None)
                    total_tokens = None
                    if input_tokens and output_tokens:
                        total_tokens = input_tokens + output_tokens

                    self._trace_logger.log_llm_response(
                        iteration_ctx,
                        model=model,
                        response_preview=final_response,
                        has_tool_calls=False,
                        tool_calls_count=0,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        duration_ms=llm_duration_ms,
                    )

                break

            if final_response is None:
                raise ChatException(
                    f'Max tool calling iterations '
                    f'({self.__max_tool_iterations}) exceeded'
                )

            # Extract token usage from Ollama response
            latency = (time.time() - start_time) * 1000
            prompt_tokens = (
                getattr(response_api, 'prompt_eval_count', None)
                if response_api
                else None
            )
            completion_tokens = (
                getattr(response_api, 'eval_count', None)
                if response_api
                else None
            )
            total_tokens = None
            if prompt_tokens and completion_tokens:
                total_tokens = prompt_tokens + completion_tokens

            self._metrics_recorder.record_success_with_values(
                model=model,
                latency_ms=latency,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            self._logger.info(
                '🤖 Ollama response received',
                extra={
                    **trace_extra,
                    'event': 'llm.response.complete',
                    'model': model,
                    'iteration': iteration,
                    'elapsed_ms': int(latency),
                    'response_preview': (
                        final_response[:300] + '...'
                        if len(final_response) > 300
                        else final_response
                    ),
                    'response_length': len(final_response),
                },
            )

            return final_response

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._metrics_recorder.record_error_with_values(
                model=model,
                latency_ms=latency,
                error_message=str(e),
            )
            raise
        finally:
            await self.__client.stop_model(model)

    async def __handle_tool_calls(
        self,
        response_api,
        history,
        tool_executor,
        parent_ctx: Optional[TraceContext] = None,
        trace_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle tool calls from Ollama response with parallel execution.

        Args:
            response_api: The Ollama API response containing tool calls.
            history: The conversation history to append results to.
            tool_executor: The tool executor instance.
            parent_ctx: Optional parent trace context.
            trace_extra: Optional trace extra dict for logging.
        """
        if trace_extra is None:
            trace_extra = {}

        tool_calls = response_api.message.tool_calls
        history.append(response_api.message)

        self._logger.info(
            'Executing %s tool(s) in parallel',
            len(tool_calls),
            extra={
                **trace_extra,
                'event': 'tool.execution.start',
                'tool_count': len(tool_calls),
                'tool_names': [tc.function.name for tc in tool_calls],
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
            if parent_ctx:
                tool_ctx = parent_ctx.create_child(
                    run_type=RunType.TOOL,
                    operation=f'tool_{tool_name}',
                    metadata={'tool_name': tool_name},
                )
                tool_trace_extra = tool_ctx.to_log_extra()

            # Log tool call start via TraceLogger (persists to TraceStore)
            # Note: Ollama doesn't provide tool_call_id like OpenAI
            tool_call_id = f'ollama_{tool_name}_{int(time.time() * 1000)}'
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
                    'tool_args': self._sanitize_for_logging(tool_args),
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

            status = 'success' if execution_result.success else 'error'
            tool_duration_ms = (time.time() - tool_start_time) * 1000

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
            if isinstance(result, Exception):
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
                history.append(
                    {
                        'role': 'tool',
                        'tool_name': tool_name,
                        'content': f'Error: {str(result)}',
                    }
                )
            else:
                history.append(result)

    def __generate_summary_from_tools(
        self, history: List[Dict[str, Any]]
    ) -> Optional[str]:
        try:
            tool_results = []
            for msg in history:
                if msg.get('role') == 'tool':
                    content = msg.get('content', '')
                    if content:
                        tool_results.append(
                            f'From {msg.get("tool_name", "unknown")}: '
                            f'{content[:500]}'
                        )

            if not tool_results:
                return None

            return 'Based on the gathered information:\n\n' + '\n\n'.join(
                tool_results[:3]
            )
        except Exception:
            return None

    def get_metrics(self) -> List[ChatMetrics]:
        """Return the list of collected metrics."""
        return self._metrics_recorder.get_metrics()

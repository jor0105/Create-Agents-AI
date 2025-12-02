import time
from typing import Any, Callable, Dict, AsyncGenerator, List, Optional, Union

from ....domain import ChatException, BaseTool, ToolExecutor
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    LoggerInterface,
)
from ...config import EnvironmentConfig
from .ollama_client import OllamaClient


class OllamaStreamHandler:
    """Handles streaming responses from Ollama with tool calling support.

    This handler follows Clean Architecture and SOLID principles:
    - All dependencies are injected via constructor (DIP)
    - Uses interfaces for metrics and schema building (OCP)
    - Single responsibility: manages streaming response flow
    """

    def __init__(
        self,
        client: OllamaClient,
        logger: LoggerInterface,
        metrics_recorder: IMetricsRecorder,
        schema_builder: IToolSchemaBuilder,
        tool_executor_factory: Optional[
            Callable[[List[BaseTool]], ToolExecutor]
        ] = None,
    ):
        """Initialize the stream handler with injected dependencies.

        Args:
            client: Ollama API client.
            logger: Logger instance for logging.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
            tool_executor_factory: Optional factory for creating ToolExecutor.
                Defaults to creating ToolExecutor with provided tools and logger.
        """
        self.__client = client
        self.__logger = logger
        self.__metrics_recorder = metrics_recorder
        self.__schema_builder = schema_builder
        self.__tool_executor_factory = (
            tool_executor_factory or self.__default_tool_executor_factory
        )
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OLLAMA_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    def __default_tool_executor_factory(
        self, tools: List[BaseTool]
    ) -> ToolExecutor:
        """Default factory for creating ToolExecutor instances.

        Args:
            tools: List of tools to provide to the executor.

        Returns:
            Configured ToolExecutor instance.
        """
        return ToolExecutor(tools, self.__logger)

    async def handle_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the Ollama API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.

        Args:
            model: The model name to use.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.
        """
        start_time = time.time()

        # Prepare tool schemas and executor if tools are provided
        tool_schemas = None
        tool_executor = None
        formatted_tool_choice = None
        if tools:
            tool_schemas = self.__schema_builder.format_tools(tools)
            tool_executor = self.__tool_executor_factory(tools)
            formatted_tool_choice = self.__schema_builder.format_tool_choice(
                tool_choice, tools
            )
            self.__logger.debug(
                'Streaming with tools enabled: %s',
                [tool.name for tool in tools],
            )
            if formatted_tool_choice:
                self.__logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
                )

        # Accumulate metrics across all iterations (for tool calls)
        total_prompt_tokens = 0
        total_completion_tokens = 0
        last_load_duration_ms: Optional[float] = None
        last_prompt_eval_duration_ms: Optional[float] = None
        last_eval_duration_ms: Optional[float] = None

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'Ollama streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                stream_response = await self.__client.call_api(
                    model,
                    messages,
                    config,
                    tool_schemas,
                    formatted_tool_choice,
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
                        self.__logger.debug(
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

                    # Duration metrics (use last values, not accumulated)
                    load_duration = getattr(last_chunk, 'load_duration', None)
                    if load_duration is not None:
                        last_load_duration_ms = load_duration / 1_000_000

                    prompt_eval_duration = getattr(
                        last_chunk, 'prompt_eval_duration', None
                    )
                    if prompt_eval_duration is not None:
                        last_prompt_eval_duration_ms = (
                            prompt_eval_duration / 1_000_000
                        )

                    eval_duration = getattr(last_chunk, 'eval_duration', None)
                    if eval_duration is not None:
                        last_eval_duration_ms = eval_duration / 1_000_000

                    self.__logger.debug(
                        'Iteration %s tokens - prompt: %s, completion: %s',
                        iteration,
                        prompt_eval_count,
                        eval_count,
                    )

                # Process tool calls if detected
                if tool_call_detected and last_chunk and tool_executor:
                    self.__logger.info('Tool calls detected, executing tools')

                    # Add assistant message with tool calls to history
                    messages.append(last_chunk.message)

                    # Execute tool calls
                    tool_calls = last_chunk.message.tool_calls
                    self.__logger.debug(
                        'Executing %s tool(s)', len(tool_calls)
                    )

                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments

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
                            else f'Error: {execution_result.error}'
                        )

                        messages.append(
                            {
                                'role': 'tool',
                                'tool_name': tool_name,
                                'content': result_text,
                            }
                        )

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
                    self.__logger.debug(
                        'Tool-only iteration, continuing to next'
                    )
                    continue

                # If we didn't yield anything and no tool calls, something's wrong
                if not has_yielded_content and not tool_call_detected:
                    self.__logger.warning(
                        'No content yielded in streaming response'
                    )
                    break

            if iteration >= self.__max_tool_iterations:
                self.__logger.warning(
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
            self.__metrics_recorder.record_success_with_values(
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
            self.__logger.info(
                'Streaming chat completed: latency=%.2fms, tokens=%s '
                '(accumulated over %s iteration(s))',
                latency,
                total_tokens,
                iteration,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.__metrics_recorder.record_error_with_values(
                model=model,
                latency_ms=latency,
                error_message=str(e),
            )
            self.__logger.error('Error during streaming: %s', e)
            raise ChatException(
                f'Error during Ollama streaming: {str(e)}', original_error=e
            ) from e
        finally:
            self.__client.stop_model(model)

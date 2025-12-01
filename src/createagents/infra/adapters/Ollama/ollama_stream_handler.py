import time
from typing import Any, Dict, AsyncGenerator, List, Optional

from ....domain import ChatException, BaseTool, ToolExecutor
from ...config import (
    ChatMetrics,
    EnvironmentConfig,
    LoggingConfig,
    create_logger,
)
from .ollama_client import OllamaClient
from .ollama_tool_schema_formatter import OllamaToolSchemaFormatter


class OllamaStreamHandler:
    """Handles streaming responses from Ollama with tool calling support."""

    def __init__(
        self,
        client: OllamaClient,
        metrics_list: Optional[List[ChatMetrics]] = None,
    ):
        self.__client = client
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics = metrics_list if metrics_list is not None else []
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env('OLLAMA_MAX_TOOL_ITERATIONS', '100')
            or '100'
        )

    async def handle_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the Ollama API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.
        """
        start_time = time.time()

        # Prepare tool schemas and executor if tools are provided
        tool_schemas = None
        tool_executor = None
        if tools:
            tool_schemas = OllamaToolSchemaFormatter.format_tools_for_ollama(
                tools
            )
            tool_executor = ToolExecutor(
                tools, create_logger(f'{__name__}.ToolExecutor')
            )
            self.__logger.debug(
                'Streaming with tools enabled: %s',
                [tool.name for tool in tools],
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
                    model, messages, config, tool_schemas
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
            metrics = ChatMetrics(
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
                load_duration_ms=last_load_duration_ms,
                prompt_eval_duration_ms=last_prompt_eval_duration_ms,
                eval_duration_ms=last_eval_duration_ms,
                success=True,
            )
            self.__metrics.append(metrics)
            self.__logger.info(
                'Streaming chat completed: %s (accumulated over %s iteration(s))',
                metrics,
                iteration,
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
            self.__logger.error('Error during streaming: %s', e)
            raise ChatException(
                f'Error during Ollama streaming: {str(e)}', original_error=e
            ) from e
        finally:
            self.__client.stop_model(model)

    def get_metrics(self) -> List[ChatMetrics]:
        """Returns the list of collected metrics."""
        return self.__metrics.copy()

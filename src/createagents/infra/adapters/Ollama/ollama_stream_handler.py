import asyncio
import time
from typing import Any, Dict, AsyncGenerator, List, Optional, Union

from ....domain import ChatException, BaseTool
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
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
    ):
        """Initialize the stream handler with injected dependencies.

        Args:
            client: Ollama API client.
            logger: Logger instance for logging.
            metrics_recorder: Metrics recorder for tracking performance.
            schema_builder: Tool schema builder for formatting tools.
        """
        super().__init__(
            logger=logger,
            metrics_recorder=metrics_recorder,
            schema_builder=schema_builder,
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
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
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
        """
        start_time = time.time()

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

        # Accumulate metrics across all iterations (for tool calls)
        total_prompt_tokens = 0
        total_completion_tokens = 0

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self._logger.info(
                    'Ollama streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                stream_response = await self.__client.call_api(
                    model,
                    history,
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
                    self._logger.info('Tool calls detected, executing tools')

                    # Add assistant message with tool calls to history
                    history.append(last_chunk.message)

                    # Execute tool calls in parallel
                    tool_calls = last_chunk.message.tool_calls
                    self._logger.debug(
                        'Executing %s tool(s) in parallel', len(tool_calls)
                    )

                    # Execute all tools in parallel using asyncio.gather
                    async def execute_single_tool(tool_call):
                        """Execute a single tool and return formatted result."""
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments

                        self._logger.debug(
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

                        # Log tool response for audit trail
                        self._logger.info(
                            "Tool '%s' response [%s]: %s",
                            tool_name,
                            'success' if execution_result.success else 'error',
                            result_text[:200] + '...'
                            if len(result_text) > 200
                            else result_text,
                        )
                        self._logger.debug(
                            "Tool '%s' full response: %s",
                            tool_name,
                            result_text,
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
                'Streaming chat completed: latency=%.2fms, tokens=%s '
                '(accumulated over %s iteration(s))',
                latency,
                total_tokens,
                iteration,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._metrics_recorder.record_error_with_values(
                model=model,
                latency_ms=latency,
                error_message=str(e),
            )
            self._logger.error('Error during streaming: %s', e)
            raise ChatException(
                f'Error during Ollama streaming: {str(e)}', original_error=e
            ) from e
        finally:
            self.__client.stop_model(model)

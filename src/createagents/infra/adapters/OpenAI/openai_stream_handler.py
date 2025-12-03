import asyncio
import time
from typing import Any, Dict, AsyncGenerator, List, Optional, Union

from ....domain import BaseTool, ChatException
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
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
    ):
        """Initialize the stream handler with injected dependencies.

        Args:
            client: OpenAI API client.
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
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
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

        self._logger.debug('Streaming mode enabled for OpenAI')

        # Accumulate token counts across all iterations (for tool calls)
        total_prompt_tokens = 0
        total_completion_tokens = 0

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self._logger.info(
                    'OpenAI streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                # Call OpenAI API with streaming enabled
                stream_response = await self.__client.call_api(
                    model,
                    instructions,
                    history,
                    config,
                    tool_schemas,
                    formatted_tool_choice,
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
                        'Executing %s tool(s) in parallel', len(tool_calls)
                    )

                    # Execute all tools in parallel using asyncio.gather
                    async def execute_single_tool(tool_call: Dict[str, Any]):
                        """Execute a single tool and return formatted result."""
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        self._logger.debug("Executing tool '%s'", tool_name)

                        execution_result = await tool_executor.execute_tool(
                            tool_name, **tool_args
                        )

                        result_text = (
                            str(execution_result.result)
                            if execution_result.success
                            else str(execution_result.error)
                        )

                        self._logger.info(
                            "Tool '%s' response [%s]: %s",
                            tool_name,
                            'success' if execution_result.success else 'error',
                            result_text[:200] + '...'
                            if len(result_text) > 200
                            else result_text,
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
                        *[execute_single_tool(tc) for tc in tool_calls],
                        return_exceptions=True,
                    )

                    # Process results and add to history
                    for i, result in enumerate(tool_results):
                        if isinstance(result, Exception):
                            self._logger.error(
                                "Tool '%s' failed with exception: %s",
                                tool_calls[i]['name'],
                                result,
                            )
                            error_msg = OpenAIToolCallParser.format_tool_results_for_llm(
                                tool_call_id=tool_calls[i]['id'],
                                tool_name=tool_calls[i]['name'],
                                result=f'Error: {str(result)}',
                            )
                            history.append(error_msg)
                        else:
                            history.append(result)

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
                f'Error during OpenAI streaming: {str(e)}',
                original_error=e,
            ) from e

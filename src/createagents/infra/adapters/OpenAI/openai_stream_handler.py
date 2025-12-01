import time
from typing import Any, Dict, AsyncGenerator, List, Optional

from ....domain import BaseTool, ChatException, ToolExecutor
from ...config import (
    ChatMetrics,
    EnvironmentConfig,
    LoggingConfig,
    create_logger,
)
from .openai_client import OpenAIClient
from .tool_call_parser import ToolCallParser
from .tool_schema_formatter import ToolSchemaFormatter


class OpenAIStreamHandler:
    """Handles streaming responses from OpenAI with tool calling support."""

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

    async def handle_stream(
        self,
        model: str,
        instructions: Optional[str],
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> AsyncGenerator[str, None]:
        """Yields tokens from the OpenAI API as they arrive.

        Supports tool calling with interrupted streaming: when tools are
        called during streaming, token yield is paused, tools are executed,
        and streaming resumes with the tool results.
        """
        start_time = time.time()

        # Prepare tool schemas and executor if tools are provided
        tool_schemas = None
        tool_executor = None
        if tools:
            tool_schemas = ToolSchemaFormatter.format_tools_for_responses_api(
                tools
            )
            tool_executor = ToolExecutor(
                tools, create_logger(f'{__name__}.ToolExecutor')
            )
            self.__logger.debug(
                'Streaming with tools enabled: %s',
                [tool.name for tool in tools],
            )

        self.__logger.debug('Streaming mode enabled for OpenAI')

        iteration = 0
        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'OpenAI streaming iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                # Call OpenAI API with streaming enabled
                stream_response = await self.__client.call_api(
                    model, instructions, messages, config, tool_schemas
                )

                self.__logger.debug(
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
                    self.__logger.warning(
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

                # Execute tool calls if present
                if tool_executor and ToolCallParser.has_tool_calls(
                    full_response
                ):
                    # Add output items to messages for context
                    output_items = (
                        ToolCallParser.get_assistant_message_with_tool_calls(
                            full_response
                        )
                    )
                    if output_items:
                        messages.extend(output_items)

                    # Extract and execute tool calls
                    tool_calls = ToolCallParser.extract_tool_calls(
                        full_response
                    )
                    self.__logger.info('Executing %s tool(s)', len(tool_calls))

                    for tool_call in tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['arguments']
                        tool_id = tool_call['id']

                        self.__logger.debug("Executing tool '%s'", tool_name)

                        execution_result = await tool_executor.execute_tool(
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

                    # Continue to next iteration for final response
                    continue

                # Response complete, no tool calls - end stream
                break

            if iteration >= self.__max_tool_iterations:
                self.__logger.warning(
                    'Max tool iterations (%s) reached during streaming',
                    self.__max_tool_iterations,
                )

            # Record metrics after streaming completes
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                tokens_used=None,  # Token count not available in streaming
                prompt_tokens=None,
                completion_tokens=None,
                success=True,
            )
            self.__metrics.append(metrics)
            self.__logger.info('Streaming chat completed: %s', metrics)

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
                f'Error during OpenAI streaming: {str(e)}',
                original_error=e,
            ) from e

    def get_metrics(self) -> List[ChatMetrics]:
        """Returns the list of collected metrics."""
        return self.__metrics.copy()

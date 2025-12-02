import time
from typing import Any, Callable, Dict, List, Optional, Union

from ....domain import BaseTool, ChatException, ToolExecutor
from ....domain.interfaces import (
    IMetricsRecorder,
    IToolSchemaBuilder,
    LoggerInterface,
)
from ...config import ChatMetrics, EnvironmentConfig
from .ollama_client import OllamaClient


class OllamaHandler:
    """Handles tool execution loop for Ollama.

    This handler follows Clean Architecture and SOLID principles:
    - All dependencies are injected via constructor (DIP)
    - Uses interfaces for metrics and schema building (OCP)
    - Single responsibility: manages tool execution loop
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
        """Initialize the handler with injected dependencies.

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

    async def execute_tool_loop(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> str:
        """Executes the tool calling loop.

        Args:
            model: The model name to use.
            messages: List of messages in the conversation.
            config: Optional configuration for the API call.
            tools: Optional list of tools available for the model.
            tool_choice: Optional tool choice configuration.

        Returns:
            The final response text from the model.
        """
        start_time = time.time()

        tool_executor = None
        tool_schemas = None
        formatted_tool_choice = None
        if tools:
            tool_executor = self.__tool_executor_factory(tools)
            tool_schemas = self.__schema_builder.format_tools(tools)
            formatted_tool_choice = self.__schema_builder.format_tool_choice(
                tool_choice, tools
            )
            if formatted_tool_choice:
                self.__logger.debug(
                    'Tool choice configured: %s', formatted_tool_choice
                )

        iteration = 0
        final_response = None
        empty_response_count = 0
        max_empty_responses = 2
        response_api = None

        try:
            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    'Ollama tool calling iteration %s/%s',
                    iteration,
                    self.__max_tool_iterations,
                )

                response_api = await self.__client.call_api(
                    model,
                    messages,
                    config,
                    tool_schemas,
                    formatted_tool_choice,
                )

                if (
                    hasattr(response_api.message, 'tool_calls')
                    and response_api.message.tool_calls
                ):
                    await self.__handle_tool_calls(
                        response_api, messages, tool_executor
                    )
                    continue

                content = response_api.message.content

                if not content:
                    empty_response_count += 1
                    if empty_response_count >= max_empty_responses:
                        summary = self.__generate_summary_from_tools(messages)
                        if summary:
                            final_response = summary
                            break
                        raise ChatException(
                            'Ollama returned multiple empty responses.'
                        )

                    # Retry with simple prompt
                    retry_messages = messages.copy()
                    retry_messages.append(
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
                        model, retry_messages, config, None
                    )
                    content = response_api.message.content
                    if content:
                        final_response = content
                        break
                    continue

                final_response = content
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

            self.__metrics_recorder.record_success_with_values(
                model=model,
                latency_ms=latency,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            return final_response

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.__metrics_recorder.record_error_with_values(
                model=model,
                latency_ms=latency,
                error_message=str(e),
            )
            raise
        finally:
            self.__client.stop_model(model)

    async def __handle_tool_calls(
        self, response_api, messages, tool_executor
    ) -> None:
        tool_calls = response_api.message.tool_calls
        messages.append(response_api.message)

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
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

    def __generate_summary_from_tools(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        try:
            tool_results = []
            for msg in messages:
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
        return self.__metrics_recorder.get_metrics()

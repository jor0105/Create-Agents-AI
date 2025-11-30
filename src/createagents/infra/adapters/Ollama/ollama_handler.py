import time
from typing import Any, Dict, List, Optional

from ....domain import BaseTool, ChatException, ToolExecutor
from ...config import ChatMetrics, EnvironmentConfig, LoggingConfig
from .ollama_client import OllamaClient
from .ollama_tool_schema_formatter import OllamaToolSchemaFormatter


class OllamaHandler:
    """Handles tool execution loop for Ollama."""

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
        )

    def execute_tool_loop(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
    ) -> str:
        """Executes the tool calling loop."""
        start_time = time.time()

        tool_executor = None
        tool_schemas = None
        if tools:
            tool_executor = ToolExecutor(tools)
            tool_schemas = OllamaToolSchemaFormatter.format_tools_for_ollama(
                tools
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

                response_api = self.__client.call_api(
                    model, messages, config, tool_schemas
                )

                if (
                    hasattr(response_api.message, 'tool_calls')
                    and response_api.message.tool_calls
                ):
                    self.__handle_tool_calls(
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
                    response_api = self.__client.call_api(
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

            self.__record_success_metrics(model, start_time, response_api)
            return final_response

        except Exception as e:
            self.__record_error_metrics(model, start_time, e)
            raise
        finally:
            self.__client.stop_model(model)

    def __handle_tool_calls(
        self, response_api, messages, tool_executor
    ) -> None:
        tool_calls = response_api.message.tool_calls
        messages.append(response_api.message)

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            execution_result = tool_executor.execute_tool(
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

    def __record_success_metrics(
        self, model: str, start_time: float, response_api: Any
    ) -> None:
        latency = (time.time() - start_time) * 1000
        prompt_eval_count = response_api.get('prompt_eval_count', 0)
        eval_count = response_api.get('eval_count', 0)
        total_tokens = prompt_eval_count + eval_count

        # Fix for the bug found in tests: check for None before division
        load_duration = response_api.get('load_duration')
        load_duration_ms = (
            load_duration / 1_000_000 if load_duration is not None else None
        )

        prompt_eval_duration = response_api.get('prompt_eval_duration')
        prompt_eval_duration_ms = (
            prompt_eval_duration / 1_000_000
            if prompt_eval_duration is not None
            else None
        )

        eval_duration = response_api.get('eval_duration')
        eval_duration_ms = (
            eval_duration / 1_000_000 if eval_duration is not None else None
        )

        metrics = ChatMetrics(
            model=model,
            latency_ms=latency,
            tokens_used=total_tokens,
            prompt_tokens=prompt_eval_count,
            completion_tokens=eval_count,
            load_duration_ms=load_duration_ms,
            prompt_eval_duration_ms=prompt_eval_duration_ms,
            eval_duration_ms=eval_duration_ms,
            success=True,
        )
        self.__metrics.append(metrics)

    def __record_error_metrics(
        self, model: str, start_time: float, error: Exception
    ) -> None:
        latency = (time.time() - start_time) * 1000
        metrics = ChatMetrics(
            model=model,
            latency_ms=latency,
            success=False,
            error_message=str(error),
        )
        self.__metrics.append(metrics)

    def get_metrics(self) -> List[ChatMetrics]:
        "Return the list of collected metrics."
        return self.__metrics.copy()

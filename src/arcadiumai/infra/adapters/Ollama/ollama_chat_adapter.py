import subprocess
import time
from typing import Any, Dict, List, Optional

from ollama import ChatResponse, chat

from ....application import ChatRepository
from ....domain import BaseTool, ChatException, ToolExecutor
from ...config import ChatMetrics, EnvironmentConfig, LoggingConfig, retry_with_backoff
from .ollama_tool_schema_formatter import OllamaToolSchemaFormatter


class OllamaChatAdapter(ChatRepository):
    """An adapter for communicating with Ollama.

    This adapter supports native tool calling using Ollama's built-in
    function calling capability (similar to OpenAI).

    Tool calling flow:
    1. Send tools schema to Ollama API
    2. Model decides whether to call tools based on the query
    3. If tool calls are detected, execute them
    4. Send tool results back to model
    5. Model generates final response
    """

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__host = EnvironmentConfig.get_env("OLLAMA_HOST", "http://localhost:11434")
        self.__max_retries = int(EnvironmentConfig.get_env("OLLAMA_MAX_RETRIES", "3"))
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env("OLLAMA_MAX_TOOL_ITERATIONS", "100")
        )

        self.__logger.info(
            f"Ollama adapter initialized (host: {self.__host}, "
            f"max_retries: {self.__max_retries}, "
            f"max_tool_iterations: {self.__max_tool_iterations})"
        )

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    def __call_ollama_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatResponse:
        """
        Calls the Ollama API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: I            "think": cls.validate_think,
            tools: Optional list of tool schemas.

        Returns:
            The API response.

        Raises:
            ChatException: If the API call fails after retries.
        """
        try:
            chat_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
            }

            if tools:
                chat_kwargs["tools"] = tools
            if config:
                config_copy = config.copy()
                if "think" in config_copy:
                    chat_kwargs["think"] = config_copy.pop("think")
                if "max_tokens" in config_copy:
                    config_copy["num_predict"] = config_copy.pop("max_tokens")
                chat_kwargs["options"] = config_copy

            response_api: ChatResponse = chat(**chat_kwargs)

            return response_api
        except Exception as e:
            self.__logger.error(
                f"Error calling Ollama API for model '{model}': {str(e)}"
            )
            raise

    def __stop_model(self, model: str) -> None:
        """
        Stops the Ollama model after use to free up memory.

        Args:
            model: The name of the model to stop.
        """
        try:
            subprocess.run(
                ["ollama", "stop", model],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.__logger.debug(f"Model {model} stopped successfully.")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.__logger.warning(f"Could not stop model {model}: {str(e)}")
        except Exception as e:
            self.__logger.warning(f"Error trying to stop model {model}: {str(e)}")

    def chat(
        self,
        model: str,
        instructions: Optional[str],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Sends a message to Ollama and returns the response.

        Implements native tool calling loop (similar to OpenAI):
        1. Send message to model with tools schema
        2. If model requests tool calls, execute them
        3. Send tool results back to model
        4. Repeat until model provides final response

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI settings.
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools (native Ollama API).

        Returns:
            The model's response.

        Raises:
            ChatException: If a communication error occurs.
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Starting chat with model {model} on Ollama.")

            # Setup tool executor and schemas if tools are provided
            tool_executor = None
            tool_schemas = None
            if tools:
                tool_executor = ToolExecutor(tools)
                tool_schemas = OllamaToolSchemaFormatter.format_tools_for_ollama(tools)
                self.__logger.debug(
                    f"Tools enabled (native API): {[tool.name for tool in tools]}"
                )

            messages = []
            if instructions and instructions.strip():
                messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            # Tool calling loop
            iteration = 0
            final_response = None
            empty_response_count = 0
            max_empty_responses = 2

            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.info(
                    f"Ollama tool calling iteration {iteration}/{self.__max_tool_iterations}"
                )
                self.__logger.debug(f"Current message history size: {len(messages)}")

                # Call Ollama API with tools
                response_api = self.__call_ollama_api(
                    model, messages, config, tool_schemas
                )

                # Check if response contains tool calls (native format)
                if (
                    hasattr(response_api.message, "tool_calls")
                    and response_api.message.tool_calls
                ):
                    tool_calls = response_api.message.tool_calls
                    self.__logger.info(
                        f"Tool calls detected: {len(tool_calls)} tool(s)"
                    )

                    # Verify that tools were provided
                    if tool_executor is None:
                        self.__logger.error(
                            "Tool calls detected but no tools were provided"
                        )
                        raise ChatException(
                            "Tool calls detected but no tools were provided to the agent"
                        )

                    # Add assistant message with tool calls to conversation
                    # For Ollama, we need to include the full message object
                    messages.append(response_api.message)

                    # Execute tools and collect results
                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments

                        self.__logger.debug(
                            f"Executing tool '{tool_name}' with args: {tool_args}"
                        )

                        # Execute tool
                        execution_result = tool_executor.execute_tool(
                            tool_name, **tool_args
                        )

                        # Format result
                        result_text = (
                            str(execution_result.result)
                            if execution_result.success
                            else f"Error: {execution_result.error}"
                        )

                        # Add tool result to messages (Ollama native format)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_name": tool_name,
                                "content": result_text,
                            }
                        )

                        self.__logger.debug(
                            f"Tool '{tool_name}' executed, result added to conversation"
                        )

                    # Continue loop to get final response from model
                    continue

                # No tool calls - this is the final response
                content: str = response_api.message.content

                if not content:
                    empty_response_count += 1
                    self.__logger.warning(
                        f"Ollama returned an empty response (count: {empty_response_count}/{max_empty_responses})"
                    )

                    # If we keep getting empty responses, try to generate a summary
                    if empty_response_count >= max_empty_responses:
                        self.__logger.warning(
                            "Max empty responses reached. Generating summary from conversation history."
                        )
                        # Generate a summary response based on the conversation
                        summary_prompt = self.__generate_summary_from_tools(messages)
                        if summary_prompt:
                            final_response = summary_prompt
                            break
                        else:
                            raise ChatException(
                                "Ollama returned multiple empty responses and could not generate summary."
                            )

                    # Retry without tool calls - send a simpler prompt
                    retry_messages = messages.copy()
                    retry_messages.append(
                        {
                            "role": "user",
                            "content": "Based on the information gathered, please provide a final answer to the original question.",
                        }
                    )

                    response_api = self.__call_ollama_api(
                        model, retry_messages, config, None
                    )
                    content = response_api.message.content

                    if content:
                        final_response = content
                        break
                    else:
                        # If still empty, use the content we have or raise
                        if iteration >= self.__max_tool_iterations - 1:
                            raise ChatException(
                                "Ollama returned empty responses. Unable to generate final answer."
                            )
                        continue

                final_response = content
                break

            # Check if we got a final response
            if final_response is None:
                self.__logger.warning(
                    f"Max tool iterations ({self.__max_tool_iterations}) reached"
                )
                raise ChatException(
                    f"Max tool calling iterations ({self.__max_tool_iterations}) exceeded"
                )

            # Record metrics
            latency = (time.time() - start_time) * 1000
            tokens_info = response_api.get("eval_count", None)

            metrics = ChatMetrics(
                model=model, latency_ms=latency, tokens_used=tokens_info, success=True
            )
            self.__metrics.append(metrics)

            self.__logger.info(f"Chat completed: {metrics}")
            self.__logger.debug(
                f"Response (first 100 chars): {final_response[:100]}..."
            )

            self.__logger.debug(
                f"Response after formatting (first 100 chars): {final_response[:100]}..."
            )

            return final_response

        except ChatException:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message="Ollama chat error",
            )
            self.__metrics.append(metrics)
            raise
        except KeyError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Missing key: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"The Ollama response has an invalid format. Missing key: {str(e)}"
            )
            raise ChatException(
                f"The Ollama response has an invalid format. Missing key: {str(e)}",
                original_error=e,
            )
        except TypeError as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model,
                latency_ms=latency,
                success=False,
                error_message=f"Type error: {str(e)}",
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"A type error occurred while processing the Ollama response: {str(e)}"
            )
            raise ChatException(
                f"A type error occurred while processing the Ollama response: {str(e)}",
                original_error=e,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            metrics = ChatMetrics(
                model=model, latency_ms=latency, success=False, error_message=str(e)
            )
            self.__metrics.append(metrics)
            self.__logger.error(
                f"An error occurred while communicating with Ollama: {str(e)}"
            )
            raise ChatException(
                f"An error occurred while communicating with Ollama: {str(e)}",
                original_error=e,
            )
        finally:
            self.__stop_model(model)

    def __generate_summary_from_tools(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate a summary response based on tool results in the conversation history.

        This is a fallback when the model returns empty responses after multiple
        tool calls. It extracts information from tool results and creates a summary.
        """
        try:
            tool_results = []
            for msg in messages:
                if msg.get("role") == "tool":
                    tool_name = msg.get("tool_name", "unknown")
                    content = msg.get("content", "")
                    if content:
                        tool_results.append(f"From {tool_name}: {content[:500]}")

            if not tool_results:
                return None

            # Create a summary based on gathered tool results
            summary = "Based on the gathered information:\n\n" + "\n\n".join(
                tool_results[:3]
            )
            self.__logger.info(
                f"Generated summary from {len(tool_results)} tool result(s)"
            )
            return summary
        except Exception as e:
            self.__logger.error(f"Error generating summary: {str(e)}")
            return None

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()

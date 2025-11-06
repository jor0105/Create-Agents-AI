import subprocess
import time
from typing import Any, Dict, List, Optional

from ollama import ChatResponse, chat

from src.application import ChatRepository
from src.domain import BaseTool, ChatException, ToolExecutor
from src.infra.adapters.Ollama.ollama_tool_call_parser import OllamaToolCallParser
from src.infra.config.environment import EnvironmentConfig
from src.infra.config.logging_config import LoggingConfig
from src.infra.config.metrics import ChatMetrics
from src.infra.config.retry import retry_with_backoff


class OllamaChatAdapter(ChatRepository):
    """An adapter for communicating with Ollama.

    This adapter now supports tool calling via prompt engineering.
    Unlike OpenAI which has native function calling, Ollama models
    are prompted to output tool requests in XML-like format that
    can be parsed and executed.

    Tool calling flow:
    1. Model outputs <tool_call> tags in response
    2. Parser detects and extracts tool calls
    3. Tools are executed
    4. Results are formatted and sent back to model
    5. Model generates final response
    """

    def __init__(self):
        self.__logger = LoggingConfig.get_logger(__name__)
        self.__metrics: List[ChatMetrics] = []

        self.__host = EnvironmentConfig.get_env("OLLAMA_HOST", "http://localhost:11434")
        self.__max_retries = int(EnvironmentConfig.get_env("OLLAMA_MAX_RETRIES", "3"))
        self.__max_tool_iterations = int(
            EnvironmentConfig.get_env("OLLAMA_MAX_TOOL_ITERATIONS", "5")
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
        config: Dict[str, Any],
    ) -> ChatResponse:
        """
        Calls the Ollama API with automatic retries.

        Args:
            model: The name of the model.
            messages: A list of messages.
            config: Internal AI settings.

        Returns:
            The API response.
        """
        if "max_tokens" in config:
            config["num_predict"] = config.pop("max_tokens")

        response_api: ChatResponse = chat(
            model=model,
            messages=messages,
            options=config,
        )

        return response_api

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
        config: Dict[str, Any],
        tools: Optional[List[BaseTool]],
        history: List[Dict[str, str]],
        user_ask: str,
    ) -> str:
        """
        Sends a message to Ollama and returns the response.

        Implements tool calling loop via prompt engineering:
        1. Send message to model
        2. If model outputs <tool_call> tags, parse and execute them
        3. Send tool results back to model
        4. Repeat until model provides final response

        Args:
            model: The name of the model.
            instructions: System instructions (optional).
            config: Internal AI settings.
            history: The conversation history.
            user_ask: The user's question.
            tools: Optional list of tools (via prompt engineering).

        Returns:
            The model's response.

        Raises:
            ChatException: If a communication error occurs.
        """
        start_time = time.time()

        try:
            self.__logger.debug(f"Starting chat with model {model} on Ollama.")

            # Setup tool executor if tools are provided
            tool_executor = None
            if tools:
                tool_executor = ToolExecutor(tools)
                self.__logger.debug(
                    f"Tools enabled (via prompt): {[tool.name for tool in tools]}"
                )

            # Build initial messages
            messages = []
            if instructions and instructions.strip():
                messages.append({"role": "system", "content": instructions})
            messages.extend(history)
            messages.append({"role": "user", "content": user_ask})

            # Tool calling loop
            iteration = 0
            final_response = None

            while iteration < self.__max_tool_iterations:
                iteration += 1
                self.__logger.debug(f"Tool iteration {iteration}")

                # Call Ollama API
                response_api = self.__call_ollama_api(model, messages, config)
                content: str = response_api.message.content

                if not content:
                    self.__logger.warning("Ollama returned an empty response.")
                    raise ChatException("Ollama returned an empty response.")

                # Check if response contains tool calls
                if OllamaToolCallParser.has_tool_calls(content):
                    self.__logger.info("Tool calls detected in response")

                    # Verify that tools were provided
                    if tool_executor is None:
                        self.__logger.error(
                            "Tool calls detected but no tools were provided"
                        )
                        raise ChatException(
                            "Tool calls detected but no tools were provided to the agent"
                        )

                    # Add assistant message with tool calls to conversation
                    messages.append({"role": "assistant", "content": content})

                    # Extract and execute tool calls
                    tool_calls = OllamaToolCallParser.extract_tool_calls(content)
                    self.__logger.debug(f"Executing {len(tool_calls)} tool(s)")

                    # Execute tools and collect results
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["arguments"]

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

                        tool_result_formatted = (
                            OllamaToolCallParser.format_tool_results_for_llm(
                                tool_name=tool_name, result=result_text
                            )
                        )
                        tool_results.append(tool_result_formatted)

                    # Add tool results as user message (simulating tool response)
                    combined_results = "\n\n".join(tool_results)
                    messages.append({"role": "user", "content": combined_results})

                    # Continue loop to get final response from model
                    continue

                # No tool calls - this is the final response
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

            # Remove any remaining tool call tags from final response
            final_response = OllamaToolCallParser.remove_tool_calls_from_response(
                final_response
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

    def get_metrics(self) -> List[ChatMetrics]:
        return self.__metrics.copy()

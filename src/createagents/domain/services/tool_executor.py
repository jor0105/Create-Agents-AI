import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..value_objects import BaseTool


@dataclass
class ToolExecutionResult:
    """Represents the result of a tool execution.

    Attributes:
        tool_name: Name of the tool that was executed.
        success: Whether the execution was successful.
        result: The result returned by the tool (if successful).
        error: Error message (if execution failed).
        execution_time_ms: Time taken to execute the tool in milliseconds.
    """

    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }

    def to_llm_message(self) -> str:
        """Format the result as a message for the LLM.

        Returns:
            A formatted string describing the tool execution result.
        """
        if self.success:
            return f"Tool '{self.tool_name}' executed successfully:\n{self.result}"
        else:
            return f"Tool '{self.tool_name}' failed with error: {self.error}"


class ToolExecutor:
    """Domain service for executing tools.

    This service follows the Dependency Inversion Principle by depending
    on the abstract BaseTool interface rather than concrete implementations.

    Responsibilities:
    - Execute tools by name with given arguments
    - Handle errors gracefully
    - Return structured results

    Example:
        ```python
        executor = ToolExecutor(available_tools)
        result = executor.execute_tool("web_search", query="Python tutorials")
        if result.success:
            print(result.result)
        ```
    """

    def __init__(self, tools: List[BaseTool]):
        """Initialize the executor with available tools.

        Args:
            tools: List of tool instances available for execution.
                   If None, no tools will be available.
        """
        # Import here to avoid circular dependency
        from ...infra import LoggingConfig

        self._tools_map: Dict[str, BaseTool] = {}
        self.__logger = LoggingConfig.get_logger(__name__)

        for tool in tools:
            self._tools_map[tool.name] = tool

        self.__logger.info(
            f'ToolExecutor initialized with {len(self._tools_map)} tool(s): {list(self._tools_map.keys())}'
        )
        self.__logger.debug(
            f'Tool details: {[{"name": t.name, "description": t.description[:50]} for t in tools]}'
        )

    def get_available_tool_names(self) -> List[str]:
        """Get list of available tool names.

        Returns:
            List of tool names that can be executed.
        """
        return list(self._tools_map.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if the tool exists, False otherwise.
        """
        return tool_name in self._tools_map

    def execute_tool(
        self, tool_name: str, **kwargs: Any
    ) -> ToolExecutionResult:
        """Execute a tool by name with given arguments.

        This method provides safe execution with comprehensive error handling,
        ensuring that tool failures don't crash the agent.

        Args:
            tool_name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool's execute method.

        Returns:
            A ToolExecutionResult containing the execution outcome.

        Example:
            ```python
            result = executor.execute_tool(
                "web_search",
                query="What is Clean Architecture?"
            )
            ```
        """
        import time

        start_time = time.time()

        self.__logger.info(f"Attempting to execute tool: '{tool_name}'")
        self.__logger.debug(f'Tool arguments: {kwargs}')

        if not self.has_tool(tool_name):
            available = ', '.join(self.get_available_tool_names())
            error_msg = (
                f"Tool '{tool_name}' not found. "
                f'Available tools: {available if available else "None"}'
            )
            self.__logger.error(error_msg)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        try:
            tool = self._tools_map[tool_name]
            self.__logger.debug(
                f"Executing tool '{tool_name}' with {len(kwargs)} argument(s)"
            )

            result = tool.execute(**kwargs)

            execution_time = (time.time() - start_time) * 1000

            self.__logger.info(
                f"Tool '{tool_name}' executed successfully in {execution_time:.2f}ms"
            )
            self.__logger.debug(
                f'Tool result (first 200 chars): {str(result)[:200]}...'
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except TypeError as e:
            error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
            execution_time = (time.time() - start_time) * 1000
            self.__logger.error(
                f"TypeError executing tool '{tool_name}': {error_msg} (execution time: {execution_time:.2f}ms)",
                exc_info=True,
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            execution_time = (time.time() - start_time) * 1000
            self.__logger.error(
                f"Exception executing tool '{tool_name}': {error_msg} (execution time: {execution_time:.2f}ms)",
                exc_info=True,
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
            )

    def execute_multiple_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """Execute multiple tools in sequence.

        Args:
            tool_calls: List of tool call specifications.
                       Each dict should have 'name' and 'arguments' keys.

        Returns:
            List of ToolExecutionResult objects.

        Example:
            ```python
            tool_calls = [
                {"name": "web_search", "arguments": {"query": "Python"}},
            ]
            results = executor.execute_multiple_tools(tool_calls)
            ```
        """
        self.__logger.info(f'Executing {len(tool_calls)} tool(s) in sequence')
        self.__logger.debug(
            f'Tool calls: {[call.get("name", "unknown") for call in tool_calls]}'
        )

        results = []

        for idx, call in enumerate(tool_calls, 1):
            tool_name = call.get('name', '')
            arguments = call.get('arguments', {})

            self.__logger.debug(
                f"Processing tool call {idx}/{len(tool_calls)}: '{tool_name}'"
            )

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                    self.__logger.debug(
                        f"Parsed JSON arguments for '{tool_name}'"
                    )
                except json.JSONDecodeError as e:
                    error_msg = f'Invalid JSON arguments: {arguments}'
                    self.__logger.error(
                        f"Failed to parse arguments for '{tool_name}': {str(e)}"
                    )
                    results.append(
                        ToolExecutionResult(
                            tool_name=tool_name,
                            success=False,
                            error=error_msg,
                        )
                    )
                    continue

            result = self.execute_tool(tool_name, **arguments)
            results.append(result)

        successful = sum(1 for r in results if r.success)
        self.__logger.info(
            f'Completed execution of {len(tool_calls)} tool(s): '
            f'{successful} successful, {len(tool_calls) - successful} failed'
        )

        return results

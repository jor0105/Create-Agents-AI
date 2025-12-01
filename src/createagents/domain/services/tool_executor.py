import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..interfaces import LoggerInterface
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
        """Convert the result to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the result.
        """
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

    def __init__(self, tools: List[BaseTool], logger: LoggerInterface):
        """Initialize the executor with available tools and logger.

        Args:
            tools: List of tool instances available for execution.
                   If None, no tools will be available.
            logger: Logger instance for logging tool execution events.
        """
        self._tools_map: Dict[str, BaseTool] = {}
        self.__logger = logger

        for tool in tools:
            self._tools_map[tool.name] = tool

        self.__logger.info(
            'ToolExecutor initialized with %s tool(s): %s',
            len(self._tools_map),
            list(self._tools_map.keys()),
        )
        self.__logger.debug(
            'Tool details: %s',
            [
                {'name': t.name, 'description': t.description[:50]}
                for t in tools
            ],
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

    async def execute_tool(
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
            result = await executor.execute_tool(
                "web_search",
                query="What is Clean Architecture?"
            )
            ```
        """
        import time  # pylint: disable=import-outside-toplevel

        start_time = time.time()

        self.__logger.info("Attempting to execute tool: '%s'", tool_name)
        self.__logger.debug('Tool arguments: %s', kwargs)

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
                "Executing tool '%s' with %s argument(s)",
                tool_name,
                len(kwargs),
            )

            import asyncio  # pylint: disable=import-outside-toplevel

            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**kwargs)
            else:
                # Run synchronous tools in a separate thread to avoid blocking
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool.execute(**kwargs)
                )

            execution_time = (time.time() - start_time) * 1000

            self.__logger.info(
                "Tool '%s' executed successfully in %.2fms",
                tool_name,
                execution_time,
            )
            self.__logger.debug(
                'Tool result (first 200 chars): %s...', str(result)[:200]
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
                "TypeError executing tool '%s': %s (execution time: %.2fms)",
                tool_name,
                error_msg,
                execution_time,
                exc_info=True,
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
            )

        except (ValueError, RuntimeError) as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            execution_time = (time.time() - start_time) * 1000
            self.__logger.error(
                "Runtime/Value error executing tool '%s': %s (execution time: %.2fms)",
                tool_name,
                error_msg,
                execution_time,
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
                "Exception executing tool '%s': %s (execution time: %.2fms)",
                tool_name,
                error_msg,
                execution_time,
                exc_info=True,
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
            )

    async def execute_multiple_tools(
        self, tool_calls: List[Dict[str, Any]], parallel: bool = False
    ) -> List[ToolExecutionResult]:
        """Execute multiple tools in sequence or parallel.

        Args:
            tool_calls: List of tool call specifications.
                       Each dict should have 'name' and 'arguments' keys.
            parallel: If True, execute tools in parallel using asyncio.gather().
                     If False (default), execute tools sequentially.
                     Use parallel execution with caution as it may cause
                     race conditions if tools have side effects.

        Returns:
            List of ToolExecutionResult objects.

        Example:
            ```python
            tool_calls = [
                {"name": "web_search", "arguments": {"query": "Python"}},
            ]
            # Sequential execution (default)
            results = await executor.execute_multiple_tools(tool_calls)

            # Parallel execution
            results = await executor.execute_multiple_tools(tool_calls, parallel=True)
            ```
        """
        execution_mode = 'parallel' if parallel else 'sequence'
        self.__logger.info(
            'Executing %s tool(s) in %s', len(tool_calls), execution_mode
        )
        self.__logger.debug(
            'Tool calls: %s',
            [call.get('name', 'unknown') for call in tool_calls],
        )

        if parallel:
            return await self._execute_parallel(tool_calls)
        else:
            return await self._execute_sequential(tool_calls)

    async def _execute_sequential(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """Execute tools sequentially.

        Args:
            tool_calls: List of tool call specifications.

        Returns:
            List of ToolExecutionResult objects.
        """
        results = []

        for idx, call in enumerate(tool_calls, 1):
            tool_name = call.get('name', '')
            arguments = call.get('arguments', {})

            self.__logger.debug(
                "Processing tool call %s/%s: '%s'",
                idx,
                len(tool_calls),
                tool_name,
            )

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                    self.__logger.debug(
                        "Parsed JSON arguments for '%s'", tool_name
                    )
                except json.JSONDecodeError as e:
                    error_msg = f'Invalid JSON arguments: {arguments}'
                    self.__logger.error(
                        "Failed to parse arguments for '%s': %s", tool_name, e
                    )
                    results.append(
                        ToolExecutionResult(
                            tool_name=tool_name,
                            success=False,
                            error=error_msg,
                        )
                    )
                    continue

            result = await self.execute_tool(tool_name, **arguments)
            results.append(result)

        successful = sum(1 for r in results if r.success)
        self.__logger.info(
            'Completed sequential execution of %s tool(s): %s successful, %s failed',
            len(tool_calls),
            successful,
            len(tool_calls) - successful,
        )

        return results

    async def _execute_parallel(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """Execute tools in parallel using asyncio.gather().

        WARNING: Parallel execution may cause race conditions if tools
        have side effects or depend on each other's results.

        Args:
            tool_calls: List of tool call specifications.

        Returns:
            List of ToolExecutionResult objects.
        """
        import asyncio  # pylint: disable=import-outside-toplevel

        tasks = []

        for idx, call in enumerate(tool_calls, 1):
            tool_name = call.get('name', '')
            arguments = call.get('arguments', {})

            self.__logger.debug(
                "Preparing parallel tool call %s/%s: '%s'",
                idx,
                len(tool_calls),
                tool_name,
            )

            # Parse JSON arguments if needed
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                    self.__logger.debug(
                        "Parsed JSON arguments for '%s'", tool_name
                    )
                except json.JSONDecodeError as e:
                    error_msg = f'Invalid JSON arguments: {arguments}'
                    self.__logger.error(
                        "Failed to parse arguments for '%s': %s", tool_name, e
                    )

                    # Create a coroutine that returns the error result
                    async def error_result():
                        return ToolExecutionResult(
                            tool_name=tool_name,
                            success=False,
                            error=error_msg,
                        )

                    tasks.append(error_result())
                    continue

            # Create task for this tool execution
            task = self.execute_tool(tool_name, **arguments)
            tasks.append(task)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if r.success)
        self.__logger.info(
            'Completed parallel execution of %s tool(s): %s successful, %s failed',
            len(tool_calls),
            successful,
            len(tool_calls) - successful,
        )

        return list(results)

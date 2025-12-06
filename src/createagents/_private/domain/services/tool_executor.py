import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..interfaces import LoggerInterface
from ..value_objects import BaseTool, ToolExecutionResult
from ..value_objects.tracing import RunType, TraceContext
from ..value_objects.tracing.context_var import (
    reset_trace_context,
    set_trace_context,
)
from .tool_argument_injector import LoggerFactory, ToolArgumentInjector

if TYPE_CHECKING:
    from ..interfaces.tracing import ITraceStore


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

    def __init__(
        self,
        tools: List[BaseTool],
        logger: LoggerInterface,
        logger_factory: Optional[LoggerFactory] = None,
        trace_context: Optional[TraceContext] = None,
        trace_store: Optional['ITraceStore'] = None,
    ):
        """Initialize the executor with available tools and logger.

        Args:
            tools: List of tool instances available for execution.
                   If None, no tools will be available.
            logger: Logger instance for logging tool execution events.
            logger_factory: Optional factory function to create loggers for tools.
            trace_context: Optional trace context for distributed tracing.
            trace_store: Optional trace store for persisting trace events.
        """
        self._tools_map: Dict[str, BaseTool] = {}
        self.__logger = logger
        self._argument_injector = ToolArgumentInjector(logger, logger_factory)
        self._trace_context = trace_context
        self._trace_store = trace_store

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
        self,
        tool_name: str,
        tool_call_id: Optional[str] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """Execute a tool by name with given arguments.

        This method provides safe execution with comprehensive error handling,
        ensuring that tool failures don't crash the agent. It also handles
        injection of InjectedToolArg parameters.

        Args:
            tool_name: Name of the tool to execute.
            tool_call_id: Optional tool call ID for InjectedToolCallId params.
            agent_state: Optional agent state for InjectedState params.
            **kwargs: Arguments to pass to the tool's run method.

        Returns:
            A ToolExecutionResult containing the execution outcome.

        Example:
            ```python
            result = await executor.execute_tool(
                "web_search",
                tool_call_id="call_123",
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

        # Set up trace context for this tool execution
        tokens = None
        if self._trace_context:
            tool_ctx = self._trace_context.create_child(
                run_type=RunType.TOOL,
                operation=f'tool.{tool_name}',
            )
            tokens = set_trace_context(tool_ctx, self._trace_store)

        try:
            tool = self._tools_map[tool_name]

            # Inject InjectedToolArg parameters if applicable
            injected_kwargs = self._argument_injector.inject_args(
                tool, kwargs, tool_call_id, agent_state
            )

            self.__logger.debug(
                "Executing tool '%s' with %s argument(s)",
                tool_name,
                len(injected_kwargs),
            )

            # Always use arun() which handles both sync and async tools
            # arun() is the async entry point that:
            # - For StructuredTool: calls _arun() which handles coroutine or func
            # - For BaseTool: calls execute_async() which wraps execute() if sync
            result = await tool.arun(**injected_kwargs)

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

        finally:
            # Always reset trace context to prevent leaks
            if tokens:
                reset_trace_context(tokens)

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

r"""Markers for tool arguments injected by runtime.

These markers are used to annotate tool parameters that should be
injected by the runtime system rather than provided by the LLM.
Parameters marked with these annotations are filtered out of the
tool schema exposed to the language model.

Example:
    ```python
    from typing import Annotated
    from createagents import tool
    from createagents.domain.value_objects import InjectedToolCallId

    @tool
    def my_tool(
        query: str,
        tool_call_id: Annotated[str, InjectedToolCallId]
    ) -> str:
        '''A tool that receives the tool call ID from runtime.'''
        return f"Executed with call_id: {tool_call_id}"
    ```
"""


class InjectedToolArg:
    """Marker for tool arguments injected by runtime, not exposed to LLM.

    Use this class as a type annotation marker via `typing.Annotated`
    to indicate that a parameter should be:
    1. Excluded from the tool's JSON schema (not visible to LLM)
    2. Injected by the runtime system when the tool is executed

    This is useful for passing context information like session IDs,
    user information, or other runtime data to tools without exposing
    these details to the language model.
    """

    pass


class InjectedToolCallId(InjectedToolArg):
    """Marker for injecting the tool call ID into a tool.

    When a parameter is annotated with this marker, the ToolExecutor
    will automatically inject the unique identifier for the current
    tool call. This is useful for logging, tracing, or correlating
    tool executions.

    Example:
        ```python
        from typing import Annotated
        from createagents import tool

        @tool
        def traceable_tool(
            data: str,
            call_id: Annotated[str, InjectedToolCallId]
        ) -> str:
            print(f"Executing tool call: {call_id}")
            return process(data)
        ```
    """

    pass


class InjectedState(InjectedToolArg):
    """Marker for injecting agent state into a tool.

    When a parameter is annotated with this marker, the runtime
    will inject the current agent state, allowing tools to access
    or modify shared state across tool invocations.
    """

    pass


class InjectedLogger(InjectedToolArg):
    r"""Marker for injecting a logger into a tool.

    When a parameter is annotated with this marker, the runtime
    will inject a configured logger instance, allowing tools to
    log execution details for debugging and monitoring.

    The injected logger is configured with the tool's name as the
    logger name, making it easy to filter and trace tool-specific logs.

    Example:
        ```python
        from typing import Annotated
        from logging import Logger
        from createagents import tool
        from createagents.domain.value_objects import InjectedLogger

        @tool
        def search_web(
            query: str,
            logger: Annotated[Logger, InjectedLogger]
        ) -> str:
            '''Search the web for information.'''
            logger.info(f"Searching for: {query}")
            results = perform_search(query)
            logger.debug(f"Found {len(results)} results")
            return results
        ```

    Benefits:
        - Automatic logger configuration
        - Consistent logging format across tools
        - Easy debugging for advanced users
        - No manual logger creation needed
    """

    pass


def is_injected_arg(annotation) -> bool:
    """Check if a type annotation contains an InjectedToolArg marker.

    This function inspects a type annotation (potentially from
    `typing.Annotated`) to determine if it contains an InjectedToolArg
    or any of its subclasses.

    Args:
        annotation: The type annotation to check. Can be a simple type,
            `Annotated` type, or any other type annotation.

    Returns:
        True if the annotation contains an InjectedToolArg marker,
        False otherwise.

    Example:
        ```python
        from typing import Annotated

        # Returns False
        is_injected_arg(str)

        # Returns True
        is_injected_arg(Annotated[str, InjectedToolCallId])

        # Returns True (custom marker)
        class MyInjected(InjectedToolArg): pass
        is_injected_arg(Annotated[int, MyInjected])
        ```
    """
    # Check if it's an Annotated type
    origin = getattr(annotation, '__origin__', None)

    if origin is None:
        return False

    # For Python 3.9+, Annotated has __origin__ = Annotated
    # We need to check __metadata__ for the markers
    metadata = getattr(annotation, '__metadata__', ())

    for meta in metadata:
        if isinstance(meta, InjectedToolArg):
            return True
        if isinstance(meta, type) and issubclass(meta, InjectedToolArg):
            return True

    return False


__all__ = [
    'InjectedToolArg',
    'InjectedToolCallId',
    'InjectedState',
    'InjectedLogger',
    'is_injected_arg',
]

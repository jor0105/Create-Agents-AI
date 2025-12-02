"""Decorator for creating tools from functions.

This module provides the `@tool` decorator, which is the primary and
recommended way to create tools in the CreateAgents framework.

Example:
    ```python
    from createagents import tool

    @tool
    def search(query: str, max_results: int = 10) -> str:
        '''Search the web for information.

        Args:
            query: The search query to execute.
            max_results: Maximum number of results to return.

        Returns:
            Search results as a formatted string.
        '''
        return f"Results for: {query}"

    # Using with custom name
    @tool("web_search")
    def my_search(query: str) -> str:
        '''Search the web.'''
        return f"Results: {query}"

    # Using with explicit Pydantic schema
    from pydantic import BaseModel, Field

    class CalculatorInput(BaseModel):
        expression: str = Field(description="Math expression")

    @tool(args_schema=CalculatorInput)
    def calculator(expression: str) -> str:
        '''Calculate a math expression.'''
        return str(eval(expression))
    ```
"""

from __future__ import annotations

import asyncio
from typing import (
    Any,
    Callable,
    Type,
    Union,
    overload,
)

from pydantic import BaseModel

from .structured_tool import StructuredTool


# Type alias for the tool decorator return types
ToolType = Union[
    StructuredTool, Callable[[Callable[..., Any]], StructuredTool]
]


@overload
def tool(
    name_or_func: Callable[..., Any],
    *,
    name: None = None,
    description: None = None,
    args_schema: None = None,
    infer_schema: bool = True,
    parse_docstring: bool = True,
    return_direct: bool = False,
) -> StructuredTool: ...


@overload
def tool(
    name_or_func: str,
    *,
    name: None = None,
    description: str | None = None,
    args_schema: Type[BaseModel] | None = None,
    infer_schema: bool = True,
    parse_docstring: bool = True,
    return_direct: bool = False,
) -> Callable[[Callable[..., Any]], StructuredTool]: ...


@overload
def tool(
    name_or_func: None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    args_schema: Type[BaseModel] | None = None,
    infer_schema: bool = True,
    parse_docstring: bool = True,
    return_direct: bool = False,
) -> Callable[[Callable[..., Any]], StructuredTool]: ...


def tool(
    name_or_func: str | Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    args_schema: Type[BaseModel] | None = None,
    infer_schema: bool = True,
    parse_docstring: bool = True,
    return_direct: bool = False,
) -> ToolType:
    """Convert a function into a tool for use by AI agents.

    The `@tool` decorator is the primary way to create tools in CreateAgents.
    It automatically infers the tool's name, description, and input schema
    from the function's signature and docstring.

    Args:
        name_or_func: Either:
            - A callable (when used as @tool without parentheses)
            - A string name (when used as @tool("name"))
            - None (when used as @tool() or @tool(key=value))
        name: The name of the tool. Defaults to the function name.
        description: The tool description. Defaults to docstring.
        args_schema: A Pydantic BaseModel for input validation.
            If not provided, one will be generated from the function
            signature when infer_schema=True.
        infer_schema: Whether to automatically infer the input schema
            from the function's type hints. Default True.
        parse_docstring: Whether to parse the function's docstring
            (Google-style) for parameter descriptions. Default True.
        return_direct: Whether to return the tool's output directly
            to the user without further LLM processing. Default False.

    Returns:
        If used as @tool (without parentheses): A StructuredTool instance.
        If used as @tool(...): A decorator that returns a StructuredTool.

    Examples:
        Basic usage - schema inferred from type hints and docstring:

        ```python
        @tool
        def get_weather(city: str, units: str = "celsius") -> str:
            '''Get the current weather for a city.

            Args:
                city: The city name to get weather for.
                units: Temperature units (celsius or fahrenheit).

            Returns:
                Weather information as a string.
            '''
            return f"Weather in {city}: 22°{units[0].upper()}"
        ```

        With custom name:

        ```python
        @tool("weather")
        def my_weather_function(city: str) -> str:
            '''Get weather.'''
            return f"Weather: {city}"
        ```

        With explicit Pydantic schema:

        ```python
        from pydantic import BaseModel, Field

        class SearchInput(BaseModel):
            query: str = Field(description="Search query")
            limit: int = Field(default=10, description="Max results")

        @tool(args_schema=SearchInput)
        def search(query: str, limit: int = 10) -> str:
            '''Search for information.'''
            return f"Found {limit} results for: {query}"
        ```

        Async tool:

        ```python
        @tool
        async def fetch_data(url: str) -> str:
            '''Fetch data from a URL.

            Args:
                url: The URL to fetch.

            Returns:
                The fetched content.
            '''
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.text
        ```
    """

    def _create_tool(
        func: Callable[..., Any],
        tool_name: str | None = None,
    ) -> StructuredTool:
        """Create a StructuredTool from a function."""
        # Determine if function is async
        is_async = asyncio.iscoroutinefunction(func)

        # Use provided name or fall back to function name
        final_name = tool_name or name or func.__name__

        if is_async:
            return StructuredTool.from_function(
                coroutine=func,
                name=final_name,
                description=description,
                args_schema=args_schema,
                infer_schema=infer_schema,
                parse_docstring=parse_docstring,
                return_direct=return_direct,
            )
        else:
            return StructuredTool.from_function(
                func=func,
                name=final_name,
                description=description,
                args_schema=args_schema,
                infer_schema=infer_schema,
                parse_docstring=parse_docstring,
                return_direct=return_direct,
            )

    # Case 1: @tool (without parentheses)
    # name_or_func is the decorated function
    if callable(name_or_func):
        return _create_tool(name_or_func)

    # Case 2: @tool("name") or @tool(name="name") or @tool()
    # Return a decorator that will receive the function
    def decorator(func: Callable[..., Any]) -> StructuredTool:
        tool_name = name_or_func if isinstance(name_or_func, str) else None
        return _create_tool(func, tool_name)

    return decorator


__all__ = ['tool']

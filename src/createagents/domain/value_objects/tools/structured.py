from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Type, cast

from pydantic import BaseModel, ValidationError

from ..utils import (
    _get_short_description,
    create_schema_from_function,
)


class StructuredTool:
    r"""A tool that wraps a Python function with automatic schema inference.

    StructuredTool provides a way to create tools from regular Python
    functions while automatically inferring the input schema from type
    hints and docstrings.

    Attributes:
        name: The unique name of the tool.
        description: Description of what the tool does.
        func: The synchronous function to execute.
        coroutine: The asynchronous function to execute.
        args_schema: Pydantic model for input validation.
        return_direct: Whether to return the result directly to the user.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any] | None = None,
        coroutine: Callable[..., Awaitable[Any]] | None = None,
        args_schema: Type[BaseModel] | None = None,
        return_direct: bool = False,
    ) -> None:
        """Initialize a StructuredTool.

        Args:
            name: The unique name of the tool.
            description: Description of what the tool does.
            func: The synchronous function to execute.
            coroutine: The asynchronous function to execute.
            args_schema: Pydantic model for input validation.
            return_direct: Whether to return result directly to user.

        Raises:
            ValueError: If neither func nor coroutine is provided.
        """
        if func is None and coroutine is None:
            raise ValueError(
                'Either func or coroutine must be provided to StructuredTool'
            )

        self.name = name
        self.description = description
        self.func = func
        self.coroutine = coroutine
        self.args_schema = args_schema
        self.return_direct = return_direct

    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any] | None = None,
        coroutine: Callable[..., Awaitable[Any]] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        args_schema: Type[BaseModel] | None = None,
        infer_schema: bool = True,
        parse_docstring: bool = True,
        return_direct: bool = False,
    ) -> 'StructuredTool':
        r"""Create a StructuredTool from a function.

        This class method provides a convenient way to create tools from
        functions with automatic inference of name, description, and
        input schema.

        Args:
            func: The synchronous function to wrap.
            coroutine: The asynchronous function to wrap.
            name: Tool name. Defaults to function name.
            description: Tool description. Defaults to docstring.
            args_schema: Pydantic model for inputs. If not provided and
                infer_schema is True, will be generated automatically.
            infer_schema: Whether to infer schema from function signature.
            parse_docstring: Whether to parse docstring for descriptions.
            return_direct: Whether to return result directly to user.

        Returns:
            A configured StructuredTool instance.

        Raises:
            ValueError: If neither func nor coroutine is provided.

        Example:
            ```python
            def search(query: str, limit: int = 10) -> str:
                Search for information.

                Args:
                    query: The search query.
                    limit: Maximum results.

                Returns:
                    Search results.
                return f"Results for: {query}"
            tool = StructuredTool.from_function(search)
            ```
        """
        if func is None and coroutine is None:
            raise ValueError(
                'Either func or coroutine must be provided to '
                'StructuredTool.from_function'
            )

        # Use the available function for inference (guaranteed to exist by check above)
        source_func = cast(Callable[..., Any], func or coroutine)

        # Infer name from function
        if name is None:
            name = source_func.__name__

        # Infer description from docstring
        if description is None:
            description = _get_short_description(source_func)
            if not description:
                description = f'Tool: {name}'

        # Infer schema if not provided
        if args_schema is None and infer_schema:
            args_schema = create_schema_from_function(
                source_func,
                model_name=f'{name.title().replace("_", "")}Input',
                parse_docstring=parse_docstring,
            )

        return cls(
            name=name,
            description=description,
            func=func,
            coroutine=coroutine,
            args_schema=args_schema,
            return_direct=return_direct,
        )

    def _validate_input(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input arguments using the Pydantic schema.

        Args:
            kwargs: The input arguments to validate.

        Returns:
            Validated arguments as a dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        if self.args_schema is None:
            return kwargs

        try:
            validated = self.args_schema(**kwargs)
            # Pydantic's model_dump returns Dict[str, Any] but is typed as Any
            return validated.model_dump()  # type: ignore[no-any-return]
        except ValidationError:
            raise

    async def _arun(self, **kwargs: Any) -> Any:
        """Execute the asynchronous tool function.

        Args:
            **kwargs: Arguments to pass to the function.

        Returns:
            The result of the async function execution.

        Raises:
            RuntimeError: If no async function is available and sync
                function cannot be used.
        """
        if self.coroutine is not None:
            return await self.coroutine(**kwargs)

        if self.func is not None:
            # Run sync function in executor
            loop = asyncio.get_running_loop()
            func = self.func  # Capture for lambda to satisfy mypy
            return await loop.run_in_executor(None, lambda: func(**kwargs))

        raise RuntimeError(
            f'Tool "{self.name}" does not have any callable function.'
        )

    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with validation.

        This is the main entry point for tool execution. It validates
        input arguments against the schema and then executes the function.

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the tool execution.

        Raises:
            ValidationError: If input validation fails.
            RuntimeError: If no function is available.
        """
        validated_kwargs = self._validate_input(kwargs)

        if self.func is None:
            raise RuntimeError(
                f'Tool "{self.name}" does not have a synchronous function. '
                'Use arun() for async execution.'
            )
        return self.func(**validated_kwargs)

    async def arun(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously with validation.

        This is the async entry point for tool execution. It validates
        input arguments and executes the function asynchronously.

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the async tool execution.

        Raises:
            ValidationError: If input validation fails.
            RuntimeError: If no function is available.
        """
        validated_kwargs = self._validate_input(kwargs)
        return await self._arun(**validated_kwargs)

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema in a provider-agnostic format.

        Returns:
            A dictionary containing the tool's name, description,
            and parameters schema.
        """
        parameters: Dict[str, Any] = {
            'type': 'object',
            'properties': {},
        }

        if self.args_schema is not None:
            schema = self.args_schema.model_json_schema()
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            parameters['properties'] = properties
            if required:
                parameters['required'] = required

        return {
            'name': self.name,
            'description': self.description,
            'parameters': parameters,
        }

    def __repr__(self) -> str:
        """Return string representation of the tool."""
        return f'StructuredTool(name={self.name!r})'

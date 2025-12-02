from __future__ import annotations

import asyncio
from abc import ABC
from typing import Any, Dict, Protocol, Type, runtime_checkable

from pydantic import BaseModel, ValidationError


@runtime_checkable
class ToolProtocol(Protocol):
    """Protocol defining the interface for all tools.

    This protocol allows duck-typing of tools, enabling both
    class-based tools (BaseTool subclasses) and function-based
    tools (StructuredTool) to be used interchangeably.
    """

    name: str
    description: str

    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments."""

    def get_schema(self) -> Dict[str, Any]:
        """Return the tool's schema."""


class BaseTool(ABC):
    r"""Base class for all tools that the agent can use.

    This class defines the contract that all tools must follow.
    Tools are capabilities that the AI agent can invoke to perform
    specific tasks (e.g., web search, calculations, API calls).

    Attributes:
        name: Unique identifier for the tool (e.g., 'web_search').
        description: Clear description of what the tool does.
        args_schema: Optional Pydantic model for input validation.

    Note:
        The preferred way to create tools is using the `@tool` decorator.
        This class is primarily used internally.
    """

    name: str = 'base_tool'
    description: str = 'Base tool description (should be overridden)'
    args_schema: Type[BaseModel] | None = None

    def _run(self, **kwargs: Any) -> Any:
        """Internal execution method - must be implemented by subclasses.

        This is the core method that performs the tool's functionality.
        Use the public `run()` method to execute with validation.

        Args:
            **kwargs: Keyword arguments specific to the tool.

        Returns:
            The result of the tool execution.
        """

    async def _arun(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously.

        Override this method to provide async-specific implementation.
        By default, runs the sync _run method in an executor.

        Args:
            **kwargs: Keyword arguments specific to the tool.

        Returns:
            The result of the async tool execution.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._run(**kwargs))

    def _validate_input(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input arguments using Pydantic schema.

        Args:
            kwargs: The input arguments to validate.

        Returns:
            Validated arguments as a dictionary.

        Raises:
            ValidationError: If validation fails and args_schema is set.
        """
        if self.args_schema is None:
            return kwargs

        try:
            validated = self.args_schema(**kwargs)
            return validated.model_dump()
        except ValidationError:
            raise

    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with validation.

        This is the main entry point for tool execution. It validates
        input arguments against the schema and then calls _run().

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the tool execution.

        Raises:
            ValidationError: If input validation fails.
        """
        validated_kwargs = self._validate_input(kwargs)
        return self._run(**validated_kwargs)

    async def arun(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously with validation.

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the async tool execution.

        Raises:
            ValidationError: If input validation fails.
        """
        validated_kwargs = self._validate_input(kwargs)
        return await self._arun(**validated_kwargs)

    def get_schema(self) -> Dict[str, Any]:
        """Return a generic schema describing the tool.

        This method returns a provider-agnostic schema that contains
        all necessary information about the tool. Infrastructure adapters
        can transform this schema to their specific format.

        The schema is generated from the Pydantic args_schema model.

        Returns:
            A dictionary with 'name', 'description', and 'parameters' keys.

        Raises:
            NotImplementedError: If args_schema is not defined.
        """
        if self.args_schema is None:
            raise NotImplementedError(
                f"Tool '{self.name}' must define 'args_schema' with a Pydantic model. "
                "The legacy 'parameters' dict is no longer supported."
            )

        # Generate schema from Pydantic model
        pydantic_schema = self.args_schema.model_json_schema()
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': pydantic_schema.get('properties', {}),
                'required': pydantic_schema.get('required', []),
            },
        }

    def __repr__(self) -> str:
        """Return string representation of the tool."""
        return f'{self.__class__.__name__}(name={self.name!r})'


__all__ = ['BaseTool', 'ToolProtocol']

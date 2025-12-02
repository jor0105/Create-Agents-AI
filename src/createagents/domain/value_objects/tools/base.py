from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, Type, runtime_checkable

from pydantic import BaseModel


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

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool's main logic - IMPLEMENT THIS METHOD.

        This is the core method that performs the tool's functionality.
        Arguments are already validated by the time this is called.

        Args:
            **kwargs: Keyword arguments specific to the tool (validated).

        Returns:
            The result of the tool execution.

        Example:
            def execute(self, query: str, limit: int = 10) -> str:
                return f"Searching for: {query}"
        """

    async def execute_async(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously - OPTIONAL OVERRIDE.

        Override this method ONLY if you need custom async implementation.
        By default, runs the sync execute() method in an executor.

        Most tools don't need to override this - the default is fine!

        Args:
            **kwargs: Keyword arguments specific to the tool.

        Returns:
            The result of the async tool execution.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))

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

        validated = self.args_schema(**kwargs)
        return validated.model_dump()

    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with validation - CALLED BY AI/SYSTEM.

        This is the main entry point used by the AI agent system.
        It validates input arguments and calls your execute() method.

        DO NOT override this method unless you know what you're doing!

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the tool execution.

        Raises:
            ValidationError: If input validation fails.
        """
        validated_kwargs = self._validate_input(kwargs)
        return self.execute(**validated_kwargs)

    async def arun(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously with validation - CALLED BY AI/SYSTEM.

        This is the async entry point used by the AI agent system.
        It validates input arguments and calls your execute_async() method.

        DO NOT override this method unless you know what you're doing!

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the async tool execution.

        Raises:
            ValidationError: If input validation fails.
        """
        validated_kwargs = self._validate_input(kwargs)
        return await self.execute_async(**validated_kwargs)

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

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Union


# Type alias for tool_choice parameter (for external API compatibility)
ToolChoiceType = Union[
    Literal['auto', 'none', 'required'],
    Dict[str, Any],
]


class ToolChoiceMode(str, Enum):
    """Predefined modes for tool selection behavior.

    Attributes:
        AUTO: Let the model decide whether to call a tool (default).
        NONE: Force the model to not call any tool.
        REQUIRED: Force the model to call at least one tool.
    """

    AUTO = 'auto'
    NONE = 'none'
    REQUIRED = 'required'


@dataclass(frozen=True)
class ToolChoice:
    """Value object representing tool selection configuration.

    This immutable value object encapsulates the tool_choice parameter
    with proper validation and conversion methods. It follows the
    Value Object pattern from DDD.

    Attributes:
        mode: The selection mode (auto, none, required, or specific).
        function_name: The specific function name when forcing a tool.

    Examples:
        ```python
        # Default behavior - let model decide
        choice = ToolChoice.auto()

        # Force no tool calls
        choice = ToolChoice.none()

        # Force at least one tool call
        choice = ToolChoice.required()

        # Force a specific tool
        choice = ToolChoice.for_function("search")

        # Parse from user input
        choice = ToolChoice.from_value("auto")
        choice = ToolChoice.from_value({"type": "function", "function": {"name": "search"}})
        ```
    """

    mode: ToolChoiceMode | str
    function_name: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the tool choice after initialization."""
        if self.mode == 'specific' and not self.function_name:
            raise ValueError(
                "function_name is required when mode is 'specific'"
            )

    @classmethod
    def auto(cls) -> 'ToolChoice':
        """Create a ToolChoice that lets the model decide."""
        return cls(mode=ToolChoiceMode.AUTO)

    @classmethod
    def none(cls) -> 'ToolChoice':
        """Create a ToolChoice that prevents tool calls."""
        return cls(mode=ToolChoiceMode.NONE)

    @classmethod
    def required(cls) -> 'ToolChoice':
        """Create a ToolChoice that forces at least one tool call."""
        return cls(mode=ToolChoiceMode.REQUIRED)

    @classmethod
    def for_function(cls, name: str) -> 'ToolChoice':
        """Create a ToolChoice that forces a specific function.

        Args:
            name: The name of the function to force.

        Returns:
            A ToolChoice configured for the specific function.
        """
        return cls(mode='specific', function_name=name)

    @classmethod
    def specific(cls, name: str) -> 'ToolChoice':
        """Alias for for_function() for convenience.

        Args:
            name: The name of the function to force.

        Returns:
            A ToolChoice configured for the specific function.

        Example:
            ```python
            # These are equivalent:
            ToolChoice.specific("weather")
            ToolChoice.for_function("weather")
            ```
        """
        return cls.for_function(name)

    @classmethod
    def _parse_dict(cls, value: Dict[str, Any]) -> 'ToolChoice':
        """Parse a dictionary format tool_choice.

        Args:
            value: Dictionary with 'type' and 'function' keys.

        Returns:
            A ToolChoice for the specified function.

        Raises:
            ValueError: If the dictionary format is invalid.
        """
        if 'type' not in value:
            raise ValueError("tool_choice dict must contain 'type' key")

        if value['type'] != 'function':
            raise ValueError("tool_choice dict 'type' must be 'function'")

        if 'function' not in value:
            raise ValueError("tool_choice dict must contain 'function' key")

        func_spec = value['function']
        if not isinstance(func_spec, dict) or 'name' not in func_spec:
            raise ValueError(
                "tool_choice function spec must be a dict with 'name' key"
            )

        return cls.for_function(func_spec['name'])

    @classmethod
    def from_value(
        cls,
        value: Optional[ToolChoiceType],
        available_tools: Optional[List[str]] = None,
    ) -> Optional['ToolChoice']:
        """Create a ToolChoice from various input formats.

        This factory method handles all the different ways a user might
        specify tool_choice, providing a unified interface.

        Args:
            value: The tool_choice value to parse. Can be:
                - None: Returns None
                - "auto", "none", "required": Creates corresponding mode
                - A tool name string: Creates specific function mode
                - {"type": "function", "function": {"name": "..."}}: Specific function

        Returns:
            A ToolChoice instance, or None if value is None.

        Raises:
            ValueError: If the value format is invalid.
        """
        if value is None:
            return None

        if isinstance(value, str):
            # Check predefined modes
            try:
                mode = ToolChoiceMode(value)
                return cls(mode=mode)
            except ValueError:
                pass

            # Could be a tool name shorthand
            if available_tools and value in available_tools:
                return cls.for_function(value)

            # Invalid string
            raise ValueError(
                f"Invalid tool_choice '{value}'. "
                f"Must be 'auto', 'none', 'required', or a valid tool name."
            )

        if isinstance(value, dict):
            return cls._parse_dict(value)

        raise ValueError(
            f'Invalid tool_choice type: {type(value).__name__}. '
            'Must be a string or dict.'
        )

    def validate_against_tools(self, tool_names: Set[str]) -> None:
        """Validate that the specified function exists in available tools.

        Args:
            tool_names: Set of available tool names.

        Raises:
            ValueError: If function_name is set but not in tool_names.
        """
        if self.is_specific_function and self.function_name not in tool_names:
            raise ValueError(
                f"tool_choice specifies unknown tool '{self.function_name}'. "
                f'Available tools: {sorted(tool_names)}'
            )

    def to_openai_format(self) -> Union[str, Dict[str, Any]]:
        """Convert to OpenAI Chat Completions API format.

        This is the format used by the Chat Completions API and compatible APIs
        (e.g., Ollama with OpenAI compatibility mode).

        Returns:
            String for simple modes ('auto', 'none', 'required'),
            or dict for specific function:
            `{'type': 'function', 'function': {'name': 'func_name'}}`
        """
        if isinstance(self.mode, ToolChoiceMode):
            return self.mode.value

        # Specific function mode (Chat Completions format)
        return {
            'type': 'function',
            'function': {'name': self.function_name},
        }

    def to_responses_api_format(self) -> Union[str, Dict[str, Any]]:
        """Convert to OpenAI Responses API format.

        The Responses API uses a different format for specific function calls
        compared to the Chat Completions API.

        Returns:
            String for simple modes ('auto', 'none', 'required'),
            or dict for specific function:
            `{'type': 'function', 'name': 'func_name'}`
        """
        if isinstance(self.mode, ToolChoiceMode):
            return self.mode.value

        # Specific function mode (Responses API format)
        return {
            'type': 'function',
            'name': self.function_name,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary.

        Returns:
            Dictionary representation of the tool choice.
        """
        if isinstance(self.mode, ToolChoiceMode):
            return {'mode': self.mode.value}

        return {
            'mode': 'specific',
            'function_name': self.function_name,
        }

    @property
    def is_specific_function(self) -> bool:
        """Check if this choice forces a specific function."""
        return self.function_name is not None

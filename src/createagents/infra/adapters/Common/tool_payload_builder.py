from typing import Any, Dict, List, Optional, Union

from ....domain.interfaces import IToolSchemaBuilder, LoggerInterface
from ....domain.value_objects import BaseTool, ToolChoice, ToolChoiceType


class ToolPayloadBuilder(IToolSchemaBuilder):
    """Unified tool payload builder for all providers.

    This class implements the IToolSchemaBuilder interface and provides
    common functionality for formatting tool schemas.

    Supports two formats:
    - 'openai' (OpenAI): Flat structure with name, description, parameters
    - 'ollama': Nested structure with function wrapper (required by Ollama API)

    Design:
    - Follows Open/Closed Principle: extend via composition or inheritance
    - Follows Single Responsibility: only handles schema formatting
    - Follows Dependency Inversion: depends on abstractions (BaseTool)

    Attributes:
        _logger: Logger instance for debugging and info messages.
        _format_style: The output format style ('openai' or 'ollama').
        _strict: Whether to enable strict mode for structured outputs (OpenAI only).
    """

    def __init__(
        self,
        logger: LoggerInterface,
        format_style: str,
        strict: bool = False,
    ) -> None:
        """Initialize the ToolPayloadBuilder.

        Args:
            logger: Logger instance for logging operations.
            format_style: Output format style. Options:
                - 'openai': OpenAI Responses API format (flat structure)
                - 'ollama': Ollama native format (nested with 'function' key)
            strict: If True, enables OpenAI's 'Structured Outputs' mode.
                   - GUARANTEES that the model's output exactly matches the schema.
                   - REQUIRES all fields in schema to be 'required' (no optional fields without explicit null).
                   - Adds 'strict: true' and 'additionalProperties: false' to the payload.
                   - Use with caution: requires strict adherence to schema rules in tool definitions.
        """
        self._logger = logger
        self._format_style = format_style
        self._strict = strict

    def single_format(self, tool: BaseTool) -> Dict[str, Any]:
        """Convert a single tool to provider-specific format.

        Args:
            tool: A BaseTool instance from the domain layer.

        Returns:
            A dictionary formatted for the provider's API.
        """
        schema = tool.get_schema()

        self._logger.debug(
            "Formatting tool '%s' for %s (strict=%s)",
            schema['name'],
            self._format_style,
            self._strict,
        )

        # Handle OpenAI's 'Strict Mode' (Structured Outputs)
        # When enabled, this forces the model to follow the schema 100%.
        # Requirement: 'additionalProperties' must be False.
        # Note: This mode is less forgiving. If your Pydantic model has optional fields
        # with default values (not marked as required), this might cause issues unless
        # handled carefully (e.g., Union[T, None]).
        parameters = schema['parameters'].copy()
        if self._strict and self._format_style == 'openai':
            parameters['additionalProperties'] = False

        if self._format_style == 'ollama':
            # Ollama requires nested structure with 'function' wrapper
            # See: https://docs.ollama.com/capabilities/tool-calling
            return {
                'type': 'function',
                'function': {
                    'name': schema['name'],
                    'description': schema['description'],
                    'parameters': parameters,
                },
            }

        # OpenAI Responses API uses flat structure
        result: Dict[str, Any] = {
            'type': 'function',
            'name': schema['name'],
            'description': schema['description'],
            'parameters': parameters,
        }

        if self._strict:
            # Enables the strict schema enforcement on the provider side.
            # This prevents hallucinations of non-existent parameters.
            result['strict'] = True

        return result

    def multiple_format(self, tools: List[BaseTool]) -> List[Dict[str, Any]]:
        """Convert multiple tools to provider-specific format.

        Args:
            tools: List of BaseTool instances.

        Returns:
            List of dictionaries formatted for the provider's API.
        """
        if not tools:
            self._logger.debug('No tools to format')
            return []

        self._logger.info(
            'Formatting %s tool(s) for %s (strict=%s)',
            len(tools),
            self._format_style,
            self._strict,
        )

        formatted = []
        for tool in tools:
            try:
                formatted.append(self.single_format(tool))
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                self._logger.error(
                    'Error formatting tool %s: %s',
                    getattr(tool, 'name', 'unknown'),
                    e,
                    exc_info=True,
                )
                continue

        # Log formatted tool names based on format style
        if self._format_style == 'ollama':
            self._logger.debug(
                'Formatted tools: %s',
                [t['function']['name'] for t in formatted],
            )
        else:
            self._logger.debug(
                'Formatted tools: %s',
                [t['name'] for t in formatted],
            )

        return formatted

    def format_tool_choice(
        self,
        tool_choice: Optional[ToolChoiceType],
        tools: Optional[List[BaseTool]] = None,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Format tool_choice parameter for provider API.

        Uses the domain ToolChoice value object for validation and formatting.

        Args:
            tool_choice: The tool_choice configuration from the user.
            tools: Optional list of available tools for validation.

        Returns:
            Formatted tool_choice for provider API, or None if not specified.
        """
        if tool_choice is None:
            return None

        self._logger.debug('Formatting tool_choice: %s', tool_choice)

        try:
            # Get available tool names for validation
            available_tools = [tool.name for tool in tools] if tools else None

            # Use domain ToolChoice for parsing and validation
            choice = ToolChoice.from_value(tool_choice, available_tools)

            if choice is None:
                return None

            # All providers currently use OpenAI format for tool_choice
            return choice.to_openai_format()

        except ValueError as e:
            self._logger.warning(
                "Invalid tool_choice: %s. Using 'auto'.",
                e,
            )
            return 'auto'


__all__ = ['ToolPayloadBuilder']

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ToolCallInfo:
    """Information about a single tool call execution.

    Attributes:
        tool_name: Name of the tool that was called.
        arguments: Arguments passed to the tool.
        result: Result returned by the tool.
        success: Whether the tool execution was successful.
    """

    tool_name: str
    arguments: dict
    result: str
    success: bool = True


@dataclass(frozen=True)
class ChatResponse:
    """Response from a chat interaction.

    This value object contains the final response text and metadata
    about any tool calls that were executed.

    Attributes:
        content: The final text response from the AI.
        tool_calls: List of tool calls that were executed (if any).
    """

    content: str
    tool_calls: List[ToolCallInfo] = field(default_factory=list)

    def has_tool_calls(self) -> bool:
        """Check if any tools were called during this interaction.

        Returns:
            True if tools were called, False otherwise.
        """
        return len(self.tool_calls) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary representation.

        Returns:
            Dictionary with content and tool_calls.
        """
        return {
            'content': self.content,
            'tool_calls': [
                {
                    'tool_name': tc.tool_name,
                    'arguments': tc.arguments,
                    'result': tc.result,
                    'success': tc.success,
                }
                for tc in self.tool_calls
            ],
        }

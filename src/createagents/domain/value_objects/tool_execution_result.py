from dataclasses import dataclass
from typing import Any, Dict, Optional


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


__all__ = ['ToolExecutionResult']

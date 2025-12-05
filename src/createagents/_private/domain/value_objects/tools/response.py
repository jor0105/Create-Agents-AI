from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Status codes for tool responses."""

    SUCCESS = 'success'
    ERROR = 'error'
    PARTIAL = 'partial'


@dataclass(frozen=True, slots=True)
class ToolResponseMetadata:
    """Metadata for tool responses.

    Provides context about the tool execution including timing,
    version information, and execution details.
    """

    tool_name: str
    executed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    execution_time_ms: Optional[float] = None
    version: str = '1.0.0'

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'tool_name': self.tool_name,
            'executed_at': self.executed_at,
            'execution_time_ms': self.execution_time_ms,
            'version': self.version,
        }


@dataclass(frozen=True, slots=True)
class ToolResponse(Generic[T]):
    """Standardized response container for all tools.

    This class ensures that all tool outputs follow a consistent format,
    making it easier for AI agents to parse and process results.

    Attributes:
        status: The execution status (success, error, partial).
        data: The actual response data (type varies by tool).
        message: Human-readable message describing the result.
        metadata: Execution metadata (timing, tool info, etc.).
        error_code: Optional error code for error responses.

    Example:
        >>> response = ToolResponse.success(
        ...     data="2024-12-04",
        ...     message="Current date retrieved successfully",
        ...     tool_name="currentdate"
        ... )
        >>> print(response.format())
    """

    status: ResponseStatus
    data: Optional[T]
    message: str
    metadata: ToolResponseMetadata
    error_code: Optional[str] = None

    @classmethod
    def success(
        cls,
        data: T,
        message: str,
        tool_name: str,
        execution_time_ms: Optional[float] = None,
    ) -> 'ToolResponse[T]':
        """Create a successful response.

        Args:
            data: The response data.
            message: Success message.
            tool_name: Name of the tool.
            execution_time_ms: Optional execution time in milliseconds.

        Returns:
            A ToolResponse with success status.
        """
        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            metadata=ToolResponseMetadata(
                tool_name=tool_name,
                execution_time_ms=execution_time_ms,
            ),
        )

    @classmethod
    def error(
        cls,
        message: str,
        tool_name: str,
        error_code: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
    ) -> 'ToolResponse[T]':
        """Create an error response.

        Args:
            message: Error message.
            tool_name: Name of the tool.
            error_code: Optional error code for categorization.
            execution_time_ms: Optional execution time in milliseconds.

        Returns:
            A ToolResponse with error status.
        """
        return cls(
            status=ResponseStatus.ERROR,
            data=None,
            message=message,
            metadata=ToolResponseMetadata(
                tool_name=tool_name,
                execution_time_ms=execution_time_ms,
            ),
            error_code=error_code,
        )

    @classmethod
    def partial(
        cls,
        data: T,
        message: str,
        tool_name: str,
        execution_time_ms: Optional[float] = None,
    ) -> 'ToolResponse[T]':
        """Create a partial success response.

        Used when the tool partially completed its task
        (e.g., truncated content due to size limits).

        Args:
            data: The partial response data.
            message: Message explaining the partial result.
            tool_name: Name of the tool.
            execution_time_ms: Optional execution time in milliseconds.

        Returns:
            A ToolResponse with partial status.
        """
        return cls(
            status=ResponseStatus.PARTIAL,
            data=data,
            message=message,
            metadata=ToolResponseMetadata(
                tool_name=tool_name,
                execution_time_ms=execution_time_ms,
            ),
        )

    def format(self) -> str:
        """Format the response as a clean string for AI consumption.

        Returns:
            A well-formatted string representation optimized for AI parsing.
        """
        if self.status == ResponseStatus.ERROR:
            return f'[{self.metadata.tool_name.upper()} ERROR] {self.message}'

        if self.status == ResponseStatus.PARTIAL:
            return f'{self.data}\n\n[Note: {self.message}]'

        return str(self.data) if self.data is not None else self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format.

        Returns:
            Dictionary representation of the response.
        """
        result: Dict[str, Any] = {
            'status': self.status.value,
            'message': self.message,
            'metadata': self.metadata.to_dict(),
        }
        if self.data is not None:
            result['data'] = self.data
        if self.error_code:
            result['error_code'] = self.error_code
        return result


__all__ = [
    'ResponseStatus',
    'ToolResponse',
    'ToolResponseMetadata',
]

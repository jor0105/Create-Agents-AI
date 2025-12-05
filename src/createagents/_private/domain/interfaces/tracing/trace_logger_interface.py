from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ...value_objects import TraceContext


class ITraceLogger(ABC):
    """Interface for trace-aware logging.

    This interface extends basic logging with trace context support,
    allowing structured logging of hierarchical operations.

    Implementations should:
    - Include trace context in all log entries
    - Support starting/ending traces
    - Provide methods for logging operations with inputs/outputs
    """

    @abstractmethod
    def start_trace(
        self,
        trace_context: TraceContext,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log the start of a trace/operation.

        Args:
            trace_context: The trace context for this operation.
            message: Human-readable message describing the operation.
            data: Optional additional data to log.
            inputs: Optional input data to log (alias for data).
        """

    @abstractmethod
    def end_trace(
        self,
        trace_context: TraceContext,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        error_stack: Optional[str] = None,
    ) -> None:
        """Log the end of a trace/operation.

        Args:
            trace_context: The trace context for this operation.
            message: Human-readable message describing the completion.
            data: Optional additional data to log.
            outputs: Optional output data to log (alias for data).
            status: Status of the operation ('success' or 'error').
            error_message: Error description (OpenTelemetry compatible).
            error_type: Exception class name (OpenTelemetry compatible).
            error_stack: Stack trace (OpenTelemetry compatible).
        """

    @abstractmethod
    def log_event(
        self,
        trace_context: TraceContext,
        event: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        level: str = 'info',
    ) -> None:
        """Log an event within a trace.

        Args:
            trace_context: The trace context for this operation.
            event: Event type/name (e.g., 'tool.call', 'llm.response').
            message: Human-readable message.
            data: Optional event data.
            level: Log level ('debug', 'info', 'warning', 'error').
        """

    @abstractmethod
    def log_tool_call(
        self,
        trace_context: TraceContext,
        tool_name: str,
        tool_call_id: str,
        inputs: Dict[str, Any],
    ) -> None:
        """Log a tool call with inputs.

        Args:
            trace_context: The trace context.
            tool_name: Name of the tool being called.
            tool_call_id: Unique ID for this tool call.
            inputs: Input arguments for the tool.
        """

    @abstractmethod
    def log_tool_result(
        self,
        trace_context: TraceContext,
        tool_name: str,
        tool_call_id: str,
        result: Any,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Log a tool execution result.

        Args:
            trace_context: The trace context.
            tool_name: Name of the tool that was called.
            tool_call_id: Unique ID for this tool call.
            result: Output from the tool (or error message).
            duration_ms: Execution time in milliseconds.
            success: Whether the tool execution succeeded.
        """

    @abstractmethod
    def log_llm_request(
        self,
        trace_context: TraceContext,
        model: str,
        messages_count: int,
        tools_available: Optional[int] = None,
    ) -> None:
        """Log an LLM API request.

        Args:
            trace_context: The trace context.
            model: Model being called.
            messages_count: Number of messages in the request.
            tools_available: Number of tools available to the model.
        """

    @abstractmethod
    def log_llm_response(
        self,
        trace_context: TraceContext,
        model: str,
        response_preview: str,
        has_tool_calls: bool,
        tool_calls_count: int = 0,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Log an LLM API response.

        Args:
            trace_context: The trace context.
            model: Model that responded.
            response_preview: Preview of the response (first N chars).
            has_tool_calls: Whether the response contains tool calls.
            tool_calls_count: Number of tool calls in response.
            input_tokens: Input/prompt tokens used (if available).
            output_tokens: Output/completion tokens used (if available).
            total_tokens: Total tokens used (if available).
            duration_ms: Response time in milliseconds.
        """

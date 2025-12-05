"""Interface for trace persistence.

This module defines the minimal contract for trace storage.

Users implementing custom trace stores only need to implement
the `save` method.

Design Philosophy:
    - Minimal interface (only `save` is required)
    - Data passed as Dict, not internal classes (decoupling)
    - Compatible with any backend (OpenTelemetry, Datadog, etc.)
    - Read/query methods are in concrete implementations, not the interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ...value_objects.tracing import TraceEntry


class ITraceStore(ABC):
    """Minimal interface for trace persistence.

    To create a custom trace store, you only need to implement
    the `save` method.

    Example - Minimal Implementation::

        class MyStore(ITraceStore):
            def save(self, data: Dict[str, Any]) -> None:
                requests.post("https://my-backend/traces", json=data)

    Example - OpenTelemetry::

        class OTelStore(ITraceStore):
            def __init__(self):
                self.tracer = trace.get_tracer(__name__)

            def save(self, data: Dict[str, Any]) -> None:
                with self.tracer.start_span(data["operation"]) as span:
                    span.set_attribute("trace_id", data["trace_id"])
                    span.set_attribute("run_type", data["run_type"])

    Data Format:
        The `data` dict contains these keys:

        Required:
        - trace_id: str - Unique identifier for the trace
        - run_id: str - Unique identifier for this span/run
        - run_type: str - One of: 'chat', 'llm', 'tool', 'chain', 'agent'
        - operation: str - Human-readable operation name
        - event: str - 'trace.start', 'trace.end', 'tool.call', etc.
        - timestamp: str - ISO format timestamp

        Context:
        - parent_run_id: str | None - Parent span ID (None for root)
        - session_id: str | None - Session grouping ID
        - agent_name: str | None - Name of the agent
        - model: str | None - Model being used
        - status: str | None - 'success', 'error', or None

        Payloads:
        - inputs: dict | None - Input data
        - outputs: dict | None - Output data
        - data: dict | None - Additional event data
        - metadata: dict - Extensible metadata

        Timing:
        - duration_ms: float | None - Duration in milliseconds

        Token Tracking (LangSmith compatible):
        - input_tokens: int | None - Input/prompt token count
        - output_tokens: int | None - Output/completion token count
        - total_tokens: int | None - Total tokens used

        Error Tracking (OpenTelemetry/Datadog compatible):
        - error_message: str | None - Error description
        - error_type: str | None - Exception class name
        - error_stack: str | None - Stack trace

        Cost Tracking:
        - cost_usd: float | None - Estimated cost in USD (user-provided)
    """

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Save a trace entry.

        This is the ONLY required method to implement.

        Args:
            data: Trace data as a dictionary. See class docstring for format.
        """

    def save_entry(self, entry: TraceEntry) -> None:
        """Internal method for backward compatibility.

        This wraps `save()` for internal use. Users should
        implement `save()` instead.
        """
        self.save(entry.to_dict())

"""
Tracing API for CreateAgentsAI.

This module exposes a minimal, decoupled interface for trace storage.
Users can integrate any observability platform by implementing `ITraceStore`.

Quick Start
-----------
Using built-in trace stores::

    from createagents import CreateAgent
    from createagents.tracing import FileTraceStore

    agent = CreateAgent(
        provider="openai",
        model="gpt-4o-mini",
        trace_store=FileTraceStore()
    )

Creating a custom trace store (minimal)::

    from createagents.tracing import ITraceStore

    class MyStore(ITraceStore):
        def save(self, data: dict) -> None:
            # data is a plain dict - send to your backend
            requests.post("https://my-backend/traces", json=data)

OpenTelemetry Integration::

    from createagents.tracing import ITraceStore
    from opentelemetry import trace

    class OTelStore(ITraceStore):
        def __init__(self):
            self.tracer = trace.get_tracer(__name__)

        def save(self, data: dict) -> None:
            with self.tracer.start_span(data["operation"]) as span:
                span.set_attribute("trace_id", data["trace_id"])
                span.set_attribute("run_type", data["run_type"])
                if data.get("error_message"):
                    span.set_status(StatusCode.ERROR, data["error_message"])

Data Format
-----------
The `save(data)` method receives a dict with these keys:

Core (always present):
    - trace_id: str - Unique identifier for the trace
    - run_id: str - Unique identifier for this span/run
    - run_type: str - 'chat', 'llm', 'tool', 'chain', 'agent'
    - operation: str - Human-readable operation name
    - event: str - 'trace.start', 'trace.end', 'tool.call', etc.
    - timestamp: str - ISO format timestamp

Context:
    - parent_run_id: str | None - Parent span ID
    - session_id: str | None - Session grouping ID
    - agent_name: str | None - Name of the agent
    - model: str | None - Model being used
    - status: str | None - 'success' or 'error'

Payloads:
    - inputs: dict | None - Input data
    - outputs: dict | None - Output data
    - duration_ms: float | None - Duration in milliseconds

Error Tracking (OpenTelemetry/Datadog):
    - error_message: str | None - Error description
    - error_type: str | None - Exception class name
    - error_stack: str | None - Stack trace

Token/Cost Tracking (LangSmith):
    - input_tokens: int | None - Input token count
    - output_tokens: int | None - Output token count
    - total_tokens: int | None - Total tokens used
    - cost_usd: float | None - Estimated cost in USD

Exports
-------
Interface:
    ITraceStore: Abstract interface - implement `save(data: dict)` method.

Built-in Stores:
    FileTraceStore: Persists traces to JSONL files.
    InMemoryTraceStore: Keeps traces in memory (dev/testing).
"""

from .._private.domain.interfaces.tracing import ITraceStore
from .._private.infra import FileTraceStore, InMemoryTraceStore

__all__ = [
    # Interface (contract for custom implementations)
    'ITraceStore',
    # Built-in Stores
    'FileTraceStore',
    'InMemoryTraceStore',
]

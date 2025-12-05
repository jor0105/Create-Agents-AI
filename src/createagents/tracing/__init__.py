"""
Tracing API for CreateAgentsAI.

Exposes types for implementing custom trace stores and integrating with
observability platforms (OpenTelemetry, Jaeger, Zipkin, Datadog, etc.).

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

Creating a custom trace store::

    from createagents.tracing import ITraceStore, TraceEntry

    class MyCustomTraceStore(ITraceStore):
        def save_entry(self, entry: TraceEntry) -> None:
            # Send to your backend
            ...

        def list_traces(self, limit=20, **filters):
            ...

        def get_trace(self, trace_id: str):
            ...

        def export_traces(self, trace_ids=None, format="json"):
            ...

        def clear_traces(self, older_than=None, trace_ids=None):
            ...

        def get_trace_count(self):
            ...

OpenTelemetry Integration::

    from createagents.tracing import ITraceStore, TraceEntry
    from opentelemetry import trace

    class OTelTraceStore(ITraceStore):
        def __init__(self):
            self.tracer = trace.get_tracer(__name__)

        def save_entry(self, entry: TraceEntry) -> None:
            with self.tracer.start_span(entry.operation) as span:
                span.set_attribute("trace_id", entry.trace_id)
                span.set_attribute("run_type", entry.run_type)
                span.set_attribute("run_id", entry.run_id)
        # ... implement other abstract methods

See ``examples/opentelemetry_tracing.py`` for a complete example.

Exports
-------
Interfaces:
    ITraceStore: Abstract interface for trace persistence.

Value Objects:
    TraceEntry: Single trace event (unit of persistence).
    TraceSummary: Aggregated summary of a complete trace.
    TraceContext: Immutable context for a trace/span.
    RunType: Enum of operation types (CHAT, TOOL, LLM, etc.).

Built-in Stores:
    FileTraceStore: Persists traces to JSONL files.
    InMemoryTraceStore: Keeps traces in memory (dev/testing).

Helpers:
    build_trace_summary: Builds TraceSummary from TraceEntry list.
"""

from .._private.domain import (
    TraceContext,
    TraceEntry,
    TraceSummary,
    ITraceStore,
    build_trace_summary,
    RunType,
)
from .._private.infra import FileTraceStore, InMemoryTraceStore

__all__ = [
    # Interfaces (contracts for custom implementations)
    'ITraceStore',
    # Value Objects (data structures)
    'TraceContext',
    'TraceEntry',
    'TraceSummary',
    'RunType',
    # Built-in Stores
    'FileTraceStore',
    'InMemoryTraceStore',
    # Helpers
    'build_trace_summary',
]

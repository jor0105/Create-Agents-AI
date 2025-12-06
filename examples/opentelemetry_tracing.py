#!/usr/bin/env python3
"""
OpenTelemetry Integration Example for CreateAgentsAI

This example demonstrates how to create a custom ITraceStore implementation
that sends trace data to OpenTelemetry, enabling integration with observability
platforms like Jaeger, Zipkin, Grafana Tempo, Datadog, etc.

REQUIREMENTS:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

    Or with poetry:
    poetry add opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

RUNNING THIS EXAMPLE:
    1. Start a local Jaeger instance (optional, for visualization):
       docker run -d --name jaeger \
         -e COLLECTOR_OTLP_ENABLED=true \
         -p 16686:16686 \
         -p 4317:4317 \
         jaegertracing/all-in-one:latest

    2. Run this script:
       python examples/opentelemetry_tracing.py

    3. Open Jaeger UI at http://localhost:16686 to see the traces

Author: CreateAgentsAI Team
"""

import asyncio
from typing import Any, Dict, Optional

from createagents import CreateAgent
from createagents.tracing import ITraceStore

# OpenTelemetry imports (install separately)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print('⚠️  OpenTelemetry not installed. Install with:')
    print(
        '   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp'
    )
    print()


class OpenTelemetryTraceStore(ITraceStore):
    """Custom ITraceStore that sends traces to OpenTelemetry.

    This implementation bridges CreateAgentsAI's tracing system with
    OpenTelemetry, enabling export to any OTEL-compatible backend.

    Features:
        - Converts trace data dicts to OTEL Spans
        - Maps agent operations to span names
        - Includes all trace metadata as span attributes
        - Supports hierarchical trace structures (parent-child spans)

    Example:
        >>> store = OpenTelemetryTraceStore(service_name="my-agent")
        >>> agent = CreateAgent(..., trace_store=store)
    """

    def __init__(
        self,
        service_name: str = 'createagents',
        otlp_endpoint: Optional[str] = None,
        console_export: bool = False,
    ):
        """Initialize the OpenTelemetry trace store.

        Args:
            service_name: Name of the service for OTEL resource.
            otlp_endpoint: OTLP gRPC endpoint (e.g., "localhost:4317").
                          If None, uses OTEL_EXPORTER_OTLP_ENDPOINT env var
                          or defaults to localhost:4317.
            console_export: If True, also prints spans to console (for debugging).
        """
        self._service_name = service_name
        self._active_spans: Dict[str, Any] = {}  # run_id -> span
        self._trace_count = 0

        # Setup OpenTelemetry
        resource = Resource.create({'service.name': service_name})
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter (sends to Jaeger, Tempo, etc.)
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint, insecure=True
            )
        else:
            otlp_exporter = OTLPSpanExporter(insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Optionally add console exporter for debugging
        if console_export:
            provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(__name__)

    def save(self, data: Dict[str, Any]) -> None:
        """Save a trace entry, creating/updating OTEL spans as needed.

        This is the only required method in ITraceStore.
        The data dict contains all trace information.
        """
        self._trace_count += 1
        event = data.get('event', '')

        # Handle different event types
        if event == 'trace.start':
            self._start_span(data)
        elif event == 'trace.end':
            self._end_span(data)
        elif event in (
            'tool.call',
            'tool.result',
            'llm.request',
            'llm.response',
        ):
            self._add_span_event(data)

    def _start_span(self, data: Dict[str, Any]) -> None:
        """Start a new OTEL span for a trace.start event."""
        run_type = data.get('run_type', 'unknown')
        operation = data.get('operation', 'unknown')
        span_name = f'{run_type}.{operation}'

        # Create span with parent context if available
        parent_run_id = data.get('parent_run_id')
        parent_span = None
        if parent_run_id and parent_run_id in self._active_spans:
            parent_span = self._active_spans[parent_run_id]

        if parent_span:
            ctx = trace.set_span_in_context(parent_span)
            span = self._tracer.start_span(span_name, context=ctx)
        else:
            span = self._tracer.start_span(span_name)

        # Set span attributes
        span.set_attribute('trace_id', data.get('trace_id', ''))
        span.set_attribute('run_id', data.get('run_id', ''))
        span.set_attribute('run_type', run_type)
        span.set_attribute('operation', operation)

        if data.get('agent_name'):
            span.set_attribute('agent.name', data['agent_name'])
        if data.get('model'):
            span.set_attribute('llm.model', data['model'])
        if data.get('session_id'):
            span.set_attribute('session.id', data['session_id'])

        # Store for later reference
        run_id = data.get('run_id', '')
        if run_id:
            self._active_spans[run_id] = span

    def _end_span(self, data: Dict[str, Any]) -> None:
        """End an OTEL span for a trace.end event."""
        run_id = data.get('run_id', '')
        span = self._active_spans.pop(run_id, None)
        if not span:
            return

        # Set final attributes
        duration_ms = data.get('duration_ms')
        if duration_ms is not None:
            span.set_attribute('duration_ms', duration_ms)

        outputs = data.get('outputs')
        if outputs and isinstance(outputs, dict):
            for key, value in outputs.items():
                span.set_attribute(f'output.{key}', str(value)[:1000])

        # Set status based on entry status
        status = data.get('status')
        if status == 'success':
            span.set_status(Status(StatusCode.OK))
        elif status == 'error':
            error_msg = data.get('error_message', 'Operation failed')
            span.set_status(Status(StatusCode.ERROR, error_msg))

        span.end()

    def _add_span_event(self, data: Dict[str, Any]) -> None:
        """Add an event to the current span."""
        run_id = data.get('run_id', '')
        span = self._active_spans.get(run_id)
        if not span:
            # If no span for this run_id, try parent
            parent_run_id = data.get('parent_run_id')
            if parent_run_id:
                span = self._active_spans.get(parent_run_id)
            if not span:
                return

        event = data.get('event', 'unknown')

        # Build event attributes
        attributes: Dict[str, Any] = {'event_type': event}

        extra_data = data.get('data')
        if extra_data and isinstance(extra_data, dict):
            for key, value in extra_data.items():
                attributes[key] = str(value)[:500]  # Truncate long values

        inputs = data.get('inputs')
        if inputs:
            attributes['inputs'] = str(inputs)[:500]

        outputs = data.get('outputs')
        if outputs:
            attributes['outputs'] = str(outputs)[:500]

        duration_ms = data.get('duration_ms')
        if duration_ms is not None:
            attributes['duration_ms'] = duration_ms

        span.add_event(event, attributes=attributes)

    def get_trace_count(self) -> int:
        """Get number of trace entries processed."""
        return self._trace_count

    def shutdown(self) -> None:
        """Flush and shutdown the OTEL provider."""
        provider = trace.get_tracer_provider()
        if hasattr(provider, 'force_flush'):
            provider.force_flush()
        if hasattr(provider, 'shutdown'):
            provider.shutdown()


# =============================================================================
# Example Usage
# =============================================================================


async def main():
    """Demonstrate OpenTelemetry integration with CreateAgentsAI."""
    if not OTEL_AVAILABLE:
        print('❌ Cannot run example without OpenTelemetry installed.')
        print(
            '   Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp'
        )
        return

    print('🔭 OpenTelemetry Tracing Example')
    print('=' * 50)
    print()

    # Create OpenTelemetry trace store
    # This will send traces to localhost:4317 (default OTLP endpoint)
    otel_store = OpenTelemetryTraceStore(
        service_name='createagents-demo',
        console_export=True,  # Also print to console for demo
    )

    print('📡 Sending traces to OpenTelemetry (localhost:4317)')
    print('   If you have Jaeger running, view at http://localhost:16686')
    print()

    # Create agent with OpenTelemetry tracing
    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        name='OTELDemoAgent',
        instructions='You are a helpful assistant. Keep responses brief.',
        trace_store=otel_store,  # <-- This enables OTEL tracing!
    )

    print('💬 Sending test message to agent...')
    print()

    try:
        response = await agent.chat('What is 2 + 2? Answer in one word.')
        print(f'🤖 Agent response: {response}')
    except Exception as e:
        print(f'⚠️  Error (expected if no API key): {e}')

    print()
    print('📊 Traces sent to OpenTelemetry!')
    print(f'   Total trace entries: {otel_store.get_trace_count()}')

    # Ensure all spans are flushed
    otel_store.shutdown()
    print('✅ OTEL provider shutdown complete')


if __name__ == '__main__':
    asyncio.run(main())

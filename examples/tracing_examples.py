#!/usr/bin/env python3
"""
Tracing Examples for CreateAgentsAI

This example demonstrates the different ways to use the tracing system:
1. No tracing (default)
2. FileTraceStore - persists to disk
3. InMemoryTraceStore - keeps in memory
4. Custom ITraceStore - for advanced integrations

Author: CreateAgentsAI Team
"""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from createagents import CreateAgent
from createagents.tracing import (
    FileTraceStore,
    InMemoryTraceStore,
    ITraceStore,
)


async def example_no_tracing():
    """Example 1: No tracing (default behavior)."""
    print('=' * 60)
    print('Example 1: No Tracing (Default)')
    print('=' * 60)

    CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        name='NoTraceAgent',
    )

    print('✅ Agent created without tracing')
    print('   No trace data will be collected or stored')
    print()


async def example_file_tracing():
    """Example 2: FileTraceStore - persists traces to disk."""
    print('=' * 60)
    print('Example 2: FileTraceStore (Disk Persistence)')
    print('=' * 60)

    # Option A: Default location (~/.createagents/traces/)
    file_store = FileTraceStore()
    print(f'📁 Default trace directory: {file_store.DEFAULT_TRACE_DIR}')

    # Option B: Custom directory
    with TemporaryDirectory() as temp_dir:
        custom_store = FileTraceStore(trace_dir=Path(temp_dir))
        print(f'📁 Custom trace directory: {temp_dir}')

        CreateAgent(
            provider='openai',
            model='gpt-5-nano',
            name='FileTraceAgent',
            trace_store=custom_store,
        )

        print('✅ Agent created with FileTraceStore')
        print('   Traces will be saved as JSONL files')
        print()


async def example_memory_tracing():
    """Example 3: InMemoryTraceStore - keeps traces in memory."""
    print('=' * 60)
    print('Example 3: InMemoryTraceStore (In-Memory)')
    print('=' * 60)

    # Good for testing, development, and short-lived sessions
    memory_store = InMemoryTraceStore(max_traces=100)

    CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        name='MemoryTraceAgent',
        trace_store=memory_store,
    )

    print('✅ Agent created with InMemoryTraceStore')
    print('   Traces kept in memory (lost on process exit)')
    print('   Max traces: 100 (oldest evicted when full)')
    print()

    # You can access trace data later
    print('📊 Trace store methods available:')
    print(f'   - get_trace_count(): {memory_store.get_trace_count()}')
    print('   - list_traces(): returns list of TraceSummary')
    print('   - get_trace(trace_id): returns single TraceSummary')
    print('   - export_traces(): returns JSON/JSONL string')
    print()


async def example_custom_store():
    """Example 4: Custom ITraceStore implementation."""
    print('=' * 60)
    print('Example 4: Custom ITraceStore (Advanced)')
    print('=' * 60)

    # Simple example: A store that just prints traces
    class PrintingTraceStore(ITraceStore):
        """A simple trace store that prints entries to console."""

        def __init__(self):
            self._count = 0

        def save(self, data: dict) -> None:
            """Save trace entry by printing to console."""
            self._count += 1
            event = data.get('event', 'unknown')
            operation = data.get('operation', 'unknown')
            run_type = data.get('run_type', 'unknown')
            print(f'   📍 [{event}] {operation} - {run_type}')

        def get_trace_count(self) -> int:
            return int(self._count)

    custom_store = PrintingTraceStore()

    CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        name='CustomStoreAgent',
        trace_store=custom_store,
    )

    print('✅ Agent created with custom PrintingTraceStore')
    print('   You can implement ITraceStore for:')
    print('   - OpenTelemetry (see opentelemetry_tracing.py)')
    print('   - Database storage (PostgreSQL, MongoDB, etc.)')
    print('   - Cloud services (AWS X-Ray, Google Cloud Trace, etc.)')
    print('   - Message queues (Kafka, RabbitMQ, etc.)')
    print()


async def example_with_chat():
    """Example 5: Actually using tracing with a chat."""
    print('=' * 60)
    print('Example 5: Tracing a Real Conversation')
    print('=' * 60)

    memory_store = InMemoryTraceStore()

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        name='TracedChatAgent',
        instructions='You are a helpful assistant. Be brief.',
        trace_store=memory_store,
        config={'stream': False},
    )

    print('💬 Sending message to agent...')

    try:
        response = await agent.chat("Hello! What's 2+2?")
        print(f'🤖 Response: {response}')
        print()

        # Inspect the traces
        print('📊 Trace Data:')
        print(f'   Total traces: {memory_store.get_trace_count()}')

        traces = memory_store.list_traces(limit=5)
        for trace in traces:
            print(f'   - {trace["trace_id"]}')
            print(f'     Agent: {trace["agent_name"]}')
            duration = trace.get('duration_ms')
            print(
                f'     Duration: {duration:.2f}ms'
                if duration
                else '     Duration: N/A'
            )
            print(f'     Tool calls: {trace["tool_calls_count"]}')
            print(f'     Status: {trace["status"]}')

    except Exception as e:
        print(f'⚠️  Error: {e}')
        print('   (Set OPENAI_API_KEY to run this example)')

    print()


async def main():
    """Run all examples."""
    print()
    print('🔍 CreateAgentsAI Tracing Examples')
    print('=' * 60)
    print()

    await example_no_tracing()
    await example_file_tracing()
    await example_memory_tracing()
    await example_custom_store()
    await example_with_chat()

    print('=' * 60)
    print('✅ All examples completed!')
    print()
    print('📚 Summary:')
    print('   - Use FileTraceStore() for production (persists to disk)')
    print('   - Use InMemoryTraceStore() for dev/testing')
    print('   - Implement ITraceStore for custom backends')
    print('   - See opentelemetry_tracing.py for OTEL integration')
    print()


if __name__ == '__main__':
    asyncio.run(main())

"""Tests for TraceLogger with TraceStore integration."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from createagents.domain.interfaces.trace_store_interface import (
    ITraceStore,
    TraceEntry,
)
from createagents.domain.value_objects.tracing import RunType, TraceContext
from createagents.infra.config.trace_logger import TraceLogger, create_trace_logger
from createagents.infra.stores import InMemoryTraceStore


class MockLogger:
    """Mock logger for testing TraceLogger."""

    def __init__(self):
        self.messages = []

    def info(self, msg, *args, **kwargs):
        self.messages.append(('info', msg % args if args else msg))

    def debug(self, msg, *args, **kwargs):
        self.messages.append(('debug', msg % args if args else msg))

    def warning(self, msg, *args, **kwargs):
        self.messages.append(('warning', msg % args if args else msg))

    def error(self, msg, *args, **kwargs):
        self.messages.append(('error', msg % args if args else msg))


class TestTraceLoggerWithStore:
    """Tests for TraceLogger with trace store."""

    def test_init_without_store(self):
        """Test initialization without trace store."""
        logger = MockLogger()
        trace_logger = TraceLogger(logger=logger)

        assert trace_logger.trace_store is None

    def test_init_with_store(self):
        """Test initialization with trace store."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        assert trace_logger.trace_store is store

    def test_start_trace_persists_entry(self):
        """Test that start_trace persists entry to store."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(
            RunType.CHAT, 'test_op', agent_name='TestAgent'
        )

        trace_logger.start_trace(ctx, inputs={'message': 'hello'})

        trace = store.get_trace(ctx.trace_id)
        assert trace is not None
        assert len(trace.entries) == 1
        assert trace.entries[0].event == 'trace.start'

    def test_end_trace_persists_entry(self):
        """Test that end_trace persists entry to store."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.CHAT, 'test_op')

        trace_logger.start_trace(ctx)
        trace_logger.end_trace(ctx, outputs={'result': 'ok'}, status='success')

        trace = store.get_trace(ctx.trace_id)
        assert len(trace.entries) == 2
        end_entry = [e for e in trace.entries if e.event == 'trace.end'][0]
        assert end_entry.status == 'success'

    def test_log_tool_call_persists_entry(self):
        """Test that log_tool_call persists entry."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.TOOL, 'tool_exec')

        trace_logger.log_tool_call(
            ctx,
            tool_name='get_weather',
            tool_call_id='call_123',
            inputs={'city': 'SP'},
        )

        trace = store.get_trace(ctx.trace_id)
        tool_entry = trace.entries[0]
        assert tool_entry.event == 'tool.call'
        assert tool_entry.inputs == {'city': 'SP'}

    def test_log_tool_result_persists_entry(self):
        """Test that log_tool_result persists entry."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.TOOL, 'tool_exec')

        trace_logger.log_tool_result(
            ctx,
            tool_name='get_weather',
            tool_call_id='call_123',
            result='25°C',
            duration_ms=150.0,
            success=True,
        )

        trace = store.get_trace(ctx.trace_id)
        result_entry = trace.entries[0]
        assert result_entry.event == 'tool.result'
        assert result_entry.duration_ms == 150.0

    def test_log_llm_request_persists_entry(self):
        """Test that log_llm_request persists entry."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.LLM, 'llm_call')

        trace_logger.log_llm_request(
            ctx, model='gpt-4', messages_count=5, tools_available=3
        )

        trace = store.get_trace(ctx.trace_id)
        llm_entry = trace.entries[0]
        assert llm_entry.event == 'llm.request'

    def test_log_llm_response_persists_entry(self):
        """Test that log_llm_response persists entry."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.LLM, 'llm_call')

        trace_logger.log_llm_response(
            ctx,
            model='gpt-4',
            response_preview='Hello!',
            has_tool_calls=False,
            tokens_used=50,
            duration_ms=500.0,
        )

        trace = store.get_trace(ctx.trace_id)
        llm_entry = trace.entries[0]
        assert llm_entry.event == 'llm.response'
        assert llm_entry.duration_ms == 500.0

    def test_log_event_persists_entry(self):
        """Test that log_event persists entry."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(RunType.CHAT, 'chat')

        trace_logger.log_event(
            ctx, event='custom.event', message='Something happened'
        )

        trace = store.get_trace(ctx.trace_id)
        assert trace.entries[0].event == 'custom.event'

    def test_store_setter(self):
        """Test setting trace store after initialization."""
        logger = MockLogger()
        trace_logger = TraceLogger(logger=logger)

        assert trace_logger.trace_store is None

        store = InMemoryTraceStore()
        trace_logger.trace_store = store

        assert trace_logger.trace_store is store

    def test_session_id_persisted(self):
        """Test that session_id is persisted in entries."""
        logger = MockLogger()
        store = InMemoryTraceStore()
        trace_logger = TraceLogger(logger=logger, trace_store=store)

        ctx = TraceContext.create_root(
            RunType.CHAT, 'chat', session_id='sess-abc'
        )

        trace_logger.start_trace(ctx)

        trace = store.get_trace(ctx.trace_id)
        assert trace.session_id == 'sess-abc'


class TestCreateTraceLoggerFactory:
    """Tests for create_trace_logger factory function."""

    def test_create_without_persistence(self):
        """Test creating trace logger without persistence."""
        trace_logger = create_trace_logger('test')

        assert isinstance(trace_logger, TraceLogger)
        assert trace_logger.trace_store is None

    def test_create_with_explicit_store(self):
        """Test creating trace logger with explicit store."""
        store = InMemoryTraceStore()
        trace_logger = create_trace_logger('test', trace_store=store)

        assert trace_logger.trace_store is store

    def test_create_with_enable_persistence(self):
        """Test creating trace logger with file persistence enabled."""
        import tempfile
        import os
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['TRACE_STORE_PATH'] = tmpdir
            try:
                trace_logger = create_trace_logger(
                    'test', enable_persistence=True
                )
                assert trace_logger.trace_store is not None
            finally:
                del os.environ['TRACE_STORE_PATH']

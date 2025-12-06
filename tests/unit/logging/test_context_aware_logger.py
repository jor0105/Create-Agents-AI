"""Unit tests for ContextAwareLogger.

These tests verify that the ContextAwareLogger correctly:
1. Delegates to the base logger when no trace context is active
2. Enriches logs with trace context when active
3. Persists logs to TraceStore when active
4. Handles all log levels correctly
"""

from typing import Any, Dict, List, Optional


from createagents._private.domain.interfaces import LoggerInterface
from createagents._private.domain.interfaces.tracing import ITraceStore
from createagents._private.domain.value_objects.tracing import (
    RunType,
    TraceContext,
)
from createagents._private.domain.value_objects.tracing.context_var import (
    reset_trace_context,
    set_trace_context,
)
from createagents._private.infra.config.logging.context_aware_logger import (
    ContextAwareLogger,
)


class MockLogger(LoggerInterface):
    """Mock logger for testing."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'debug',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'info',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'warning',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'error',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'critical',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append(
            {
                'level': 'exception',
                'message': message,
                'args': args,
                'kwargs': kwargs,
            }
        )


class MockTraceStore(ITraceStore):
    """Mock trace store for testing."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def save(self, data: Dict[str, Any]) -> None:
        self.entries.append(data)

    def save_entry(self, entry: Any) -> None:
        self.entries.append(entry)

    def get_entries(
        self,
        trace_id: Optional[str] = None,
        run_id: Optional[str] = None,
        session_id: Optional[str] = None,
        run_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        return self.entries

    def get_trace_summary(self, trace_id: str) -> Optional[Any]:
        return None

    def list_traces(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Any]:
        return []


class TestContextAwareLoggerWithoutContext:
    """Tests for ContextAwareLogger when no trace context is active."""

    def test_delegates_to_base_logger(self):
        """Logs are passed through to base logger."""
        mock_logger = MockLogger()
        logger = ContextAwareLogger('test', mock_logger)

        logger.info('Hello %s', 'world')

        assert len(mock_logger.calls) == 1
        assert mock_logger.calls[0]['level'] == 'info'
        assert mock_logger.calls[0]['message'] == 'Hello %s'
        assert mock_logger.calls[0]['args'] == ('world',)

    def test_all_levels_work(self):
        """All log levels delegate correctly."""
        mock_logger = MockLogger()
        logger = ContextAwareLogger('test', mock_logger)

        logger.debug('debug msg')
        logger.info('info msg')
        logger.warning('warning msg')
        logger.error('error msg')
        logger.critical('critical msg')

        levels = [call['level'] for call in mock_logger.calls]
        assert levels == ['debug', 'info', 'warning', 'error', 'critical']

    def test_exception_sets_exc_info(self):
        """Exception method sets exc_info=True."""
        mock_logger = MockLogger()
        logger = ContextAwareLogger('test', mock_logger)

        logger.exception('error with traceback')

        assert len(mock_logger.calls) == 1
        assert mock_logger.calls[0]['kwargs'].get('exc_info') is True


class TestContextAwareLoggerWithContext:
    """Tests for ContextAwareLogger when trace context is active."""

    def test_enriches_extra_with_trace_context(self):
        """Logs include trace_id and run_id in extra."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test.module', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_operation')
        tokens = set_trace_context(ctx, mock_store)

        try:
            logger.info('Test message')

            assert len(mock_logger.calls) == 1
            extra = mock_logger.calls[0]['kwargs'].get('extra', {})
            assert extra.get('trace_id') == ctx.trace_id
            assert extra.get('run_id') == ctx.run_id
            assert extra.get('logger_name') == 'test.module'
        finally:
            reset_trace_context(tokens)

    def test_persists_to_trace_store(self):
        """Logs are persisted to TraceStore."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test.module', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_operation')
        tokens = set_trace_context(ctx, mock_store)

        try:
            logger.info('Persisted message')

            assert len(mock_store.entries) == 1
            entry = mock_store.entries[0]
            assert entry['event'] == 'tool.log'
            assert entry['trace_id'] == ctx.trace_id
            assert entry['run_id'] == ctx.run_id
            assert entry['level'] == 'INFO'
            assert entry['message'] == 'Persisted message'
            assert entry['logger_name'] == 'test.module'
            assert 'timestamp' in entry
        finally:
            reset_trace_context(tokens)

    def test_formats_message_with_args(self):
        """Message formatting works correctly for persistence."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_op')
        tokens = set_trace_context(ctx, mock_store)

        try:
            logger.info('Value is %d and name is %s', 42, 'test')

            entry = mock_store.entries[0]
            assert entry['message'] == 'Value is 42 and name is test'
        finally:
            reset_trace_context(tokens)

    def test_all_levels_persist(self):
        """All log levels are persisted."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_op')
        tokens = set_trace_context(ctx, mock_store)

        try:
            logger.debug('debug')
            logger.info('info')
            logger.warning('warning')
            logger.error('error')
            logger.critical('critical')

            levels = [entry['level'] for entry in mock_store.entries]
            assert levels == ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        finally:
            reset_trace_context(tokens)


class TestContextAwareLoggerEdgeCases:
    """Edge case tests for ContextAwareLogger."""

    def test_handles_formatting_errors_gracefully(self):
        """Formatting errors don't crash logging."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_op')
        tokens = set_trace_context(ctx, mock_store)

        try:
            # Invalid format args shouldn't crash
            logger.info('Value is %d', 'not_a_number')

            # Should still log to base logger
            assert len(mock_logger.calls) == 1
            # Should still persist (with fallback message)
            assert len(mock_store.entries) == 1
        finally:
            reset_trace_context(tokens)

    def test_preserves_existing_extra(self):
        """Existing 'extra' kwargs are preserved."""
        mock_logger = MockLogger()
        mock_store = MockTraceStore()
        logger = ContextAwareLogger('test', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_op')
        tokens = set_trace_context(ctx, mock_store)

        try:
            logger.info('Test', extra={'custom_key': 'custom_value'})

            extra = mock_logger.calls[0]['kwargs'].get('extra', {})
            assert extra.get('custom_key') == 'custom_value'
            assert extra.get('trace_id') == ctx.trace_id
        finally:
            reset_trace_context(tokens)

    def test_context_without_store_still_enriches(self):
        """Context enrichment works even without store."""
        mock_logger = MockLogger()
        logger = ContextAwareLogger('test', mock_logger)

        ctx = TraceContext.create_root(RunType.TOOL, 'test_op')
        tokens = set_trace_context(ctx, None)  # No store

        try:
            logger.info('Test message')

            extra = mock_logger.calls[0]['kwargs'].get('extra', {})
            assert extra.get('trace_id') == ctx.trace_id
        finally:
            reset_trace_context(tokens)

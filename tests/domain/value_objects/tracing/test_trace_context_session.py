"""Tests for TraceContext session_id support."""

import pytest

from createagents.domain.value_objects.tracing import RunType, TraceContext


class TestTraceContextSessionId:
    """Tests for session_id functionality."""

    def test_create_root_with_session_id(self):
        """Test creating root trace with session_id."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            session_id='session-abc123',
        )

        assert ctx.session_id == 'session-abc123'

    def test_create_root_without_session_id(self):
        """Test that session_id defaults to None."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
        )

        assert ctx.session_id is None

    def test_child_inherits_session_id(self):
        """Test that child traces inherit session_id from parent."""
        parent = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            session_id='session-xyz',
        )
        child = parent.create_child(
            run_type=RunType.LLM,
            operation='llm_call',
        )

        assert child.session_id == 'session-xyz'

    def test_with_metadata_preserves_session_id(self):
        """Test that with_metadata preserves session_id."""
        ctx1 = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            session_id='sess-123',
        )
        ctx2 = ctx1.with_metadata({'key': 'value'})

        assert ctx2.session_id == 'sess-123'

    def test_to_dict_includes_session_id(self):
        """Test that to_dict includes session_id."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            session_id='my-session',
        )
        data = ctx.to_dict()

        assert 'session_id' in data
        assert data['session_id'] == 'my-session'

    def test_to_log_extra_includes_session_id(self):
        """Test that to_log_extra includes session_id."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            session_id='log-session',
        )
        extra = ctx.to_log_extra()

        assert 'session_id' in extra
        assert extra['session_id'] == 'log-session'

    def test_nested_children_inherit_session_id(self):
        """Test that deeply nested children inherit session_id."""
        root = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='root',
            session_id='deep-session',
        )
        child1 = root.create_child(RunType.LLM, 'child1')
        child2 = child1.create_child(RunType.TOOL, 'child2')
        child3 = child2.create_child(RunType.CHAIN, 'child3')

        assert child1.session_id == 'deep-session'
        assert child2.session_id == 'deep-session'
        assert child3.session_id == 'deep-session'

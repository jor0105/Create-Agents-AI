"""Unit tests for TraceContext value object.

Tests cover:
- Creation of root traces
- Creation of child traces
- Metadata handling
- Serialization (to_dict, to_log_extra)
- Elapsed time calculation
"""

import time

import pytest

from createagents.domain.value_objects.tracing import RunType, TraceContext


class TestRunType:
    """Tests for RunType enum."""

    def test_run_type_values(self):
        """Test that all expected run types exist."""
        assert RunType.CHAT.value == 'chat'
        assert RunType.LLM.value == 'llm'
        assert RunType.TOOL.value == 'tool'
        assert RunType.CHAIN.value == 'chain'
        assert RunType.RETRIEVER.value == 'retriever'
        assert RunType.EMBEDDING.value == 'embedding'
        assert RunType.AGENT.value == 'agent'
        assert RunType.PARSER.value == 'parser'

    def test_run_type_count(self):
        """Test that we have all expected run types."""
        assert len(RunType) == 8


class TestTraceContextCreation:
    """Tests for TraceContext creation methods."""

    def test_create_root_minimal(self):
        """Test creating a root trace with minimal parameters."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='test_operation',
        )

        assert ctx.trace_id is not None
        assert ctx.run_id is not None
        assert ctx.parent_run_id is None
        assert ctx.run_type == RunType.CHAT
        assert ctx.operation == 'test_operation'
        assert ctx.agent_name is None
        assert ctx.model is None
        assert ctx.metadata == {}
        assert ctx.start_time is not None

    def test_create_root_full(self):
        """Test creating a root trace with all parameters."""
        metadata = {'key': 'value', 'count': 42}
        ctx = TraceContext.create_root(
            run_type=RunType.AGENT,
            operation='agent_chat',
            agent_name='TestAgent',
            model='gpt-4',
            metadata=metadata,
        )

        assert ctx.trace_id is not None
        assert ctx.run_id is not None
        assert ctx.parent_run_id is None
        assert ctx.run_type == RunType.AGENT
        assert ctx.operation == 'agent_chat'
        assert ctx.agent_name == 'TestAgent'
        assert ctx.model == 'gpt-4'
        assert ctx.metadata == metadata
        assert ctx.start_time is not None

    def test_create_root_generates_unique_ids(self):
        """Test that each root trace has unique IDs."""
        ctx1 = TraceContext.create_root(RunType.CHAT, 'op1')
        ctx2 = TraceContext.create_root(RunType.CHAT, 'op2')

        assert ctx1.trace_id != ctx2.trace_id
        assert ctx1.run_id != ctx2.run_id

    def test_trace_id_format(self):
        """Test that trace_id has expected prefix."""
        ctx = TraceContext.create_root(RunType.CHAT, 'test')
        assert ctx.trace_id.startswith('trace-')

    def test_run_id_format(self):
        """Test that run_id has expected prefix."""
        ctx = TraceContext.create_root(RunType.CHAT, 'test')
        assert ctx.run_id.startswith('run-')


class TestTraceContextChild:
    """Tests for creating child traces."""

    def test_create_child_basic(self):
        """Test creating a basic child trace."""
        parent = TraceContext.create_root(RunType.CHAT, 'parent_op')
        child = parent.create_child(
            run_type=RunType.LLM,
            operation='child_op',
        )

        assert child.trace_id == parent.trace_id
        assert child.run_id != parent.run_id
        assert child.parent_run_id == parent.run_id
        assert child.run_type == RunType.LLM
        assert child.operation == 'child_op'
        assert child.agent_name == parent.agent_name
        assert child.model == parent.model

    def test_create_child_inherits_agent_info(self):
        """Test that child inherits agent_name and model from parent."""
        parent = TraceContext.create_root(
            run_type=RunType.AGENT,
            operation='agent_op',
            agent_name='MyAgent',
            model='gpt-4o',
        )
        child = parent.create_child(RunType.TOOL, 'tool_op')

        assert child.agent_name == 'MyAgent'
        assert child.model == 'gpt-4o'

    def test_create_child_with_metadata(self):
        """Test creating a child with additional metadata."""
        parent = TraceContext.create_root(RunType.CHAT, 'parent')
        child = parent.create_child(
            run_type=RunType.TOOL,
            operation='tool_call',
            metadata={'tool_name': 'web_search', 'call_id': 'call_123'},
        )

        assert child.metadata == {
            'tool_name': 'web_search',
            'call_id': 'call_123',
        }

    def test_create_nested_children(self):
        """Test creating nested child traces."""
        root = TraceContext.create_root(RunType.CHAT, 'root')
        child1 = root.create_child(RunType.LLM, 'llm_call')
        child2 = child1.create_child(RunType.TOOL, 'tool_call')

        # All share same trace_id
        assert root.trace_id == child1.trace_id == child2.trace_id

        # Parent chain is correct
        assert root.parent_run_id is None
        assert child1.parent_run_id == root.run_id
        assert child2.parent_run_id == child1.run_id


class TestTraceContextMetadata:
    """Tests for metadata handling."""

    def test_with_metadata_creates_new_context(self):
        """Test that with_metadata creates a new context (immutability)."""
        ctx1 = TraceContext.create_root(RunType.CHAT, 'op')
        ctx2 = ctx1.with_metadata({'key': 'value'})

        assert ctx1 is not ctx2
        assert ctx1.metadata == {}
        assert ctx2.metadata == {'key': 'value'}

    def test_with_metadata_preserves_other_fields(self):
        """Test that with_metadata preserves all other fields."""
        ctx1 = TraceContext.create_root(
            run_type=RunType.AGENT,
            operation='op',
            agent_name='Agent1',
            model='gpt-4',
        )
        ctx2 = ctx1.with_metadata({'key': 'value'})

        assert ctx2.trace_id == ctx1.trace_id
        assert ctx2.run_id == ctx1.run_id
        assert ctx2.parent_run_id == ctx1.parent_run_id
        assert ctx2.run_type == ctx1.run_type
        assert ctx2.operation == ctx1.operation
        assert ctx2.agent_name == ctx1.agent_name
        assert ctx2.model == ctx1.model
        assert ctx2.start_time == ctx1.start_time

    def test_with_metadata_merges_existing(self):
        """Test that with_metadata merges with existing metadata."""
        ctx1 = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='op',
            metadata={'existing': 'value'},
        )
        ctx2 = ctx1.with_metadata({'new': 'data'})

        assert ctx2.metadata == {'existing': 'value', 'new': 'data'}


class TestTraceContextSerialization:
    """Tests for serialization methods."""

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all relevant fields."""
        ctx = TraceContext.create_root(
            run_type=RunType.AGENT,
            operation='agent_chat',
            agent_name='TestBot',
            model='gpt-4',
            metadata={'key': 'value'},
        )
        data = ctx.to_dict()

        assert 'trace_id' in data
        assert 'run_id' in data
        assert 'parent_run_id' in data
        assert 'run_type' in data
        assert 'operation' in data
        assert 'agent_name' in data
        assert 'model' in data
        assert 'metadata' in data
        assert 'start_time' in data

        assert data['trace_id'] == ctx.trace_id
        assert data['run_type'] == 'agent'  # String, not enum
        assert data['agent_name'] == 'TestBot'

    def test_to_log_extra_format(self):
        """Test that to_log_extra returns proper format for logging."""
        ctx = TraceContext.create_root(
            run_type=RunType.CHAT,
            operation='chat',
            agent_name='Bot',
            model='gpt-4',
        )
        extra = ctx.to_log_extra()

        assert extra['trace_id'] == ctx.trace_id
        assert extra['run_id'] == ctx.run_id
        assert extra['parent_run_id'] is None
        assert extra['run_type'] == 'chat'
        assert extra['operation'] == 'chat'
        assert extra['agent_name'] == 'Bot'
        assert extra['model'] == 'gpt-4'

    def test_to_log_extra_child(self):
        """Test to_log_extra for child context."""
        parent = TraceContext.create_root(RunType.CHAT, 'parent')
        child = parent.create_child(RunType.TOOL, 'tool')
        extra = child.to_log_extra()

        assert extra['trace_id'] == parent.trace_id
        assert extra['run_id'] == child.run_id
        assert extra['parent_run_id'] == parent.run_id


class TestTraceContextTiming:
    """Tests for elapsed time calculation."""

    def test_elapsed_ms_returns_positive(self):
        """Test that elapsed_ms returns positive value."""
        ctx = TraceContext.create_root(RunType.CHAT, 'op')
        time.sleep(0.01)  # 10ms
        elapsed = ctx.elapsed_ms

        assert elapsed >= 10
        assert elapsed < 1000  # Should not take more than 1 second

    def test_elapsed_ms_property(self):
        """Test that elapsed_ms is a property (not method)."""
        ctx = TraceContext.create_root(RunType.CHAT, 'op')

        # Should be accessible as property (not callable)
        elapsed = ctx.elapsed_ms
        assert isinstance(elapsed, float)


class TestTraceContextImmutability:
    """Tests for immutability of TraceContext."""

    def test_frozen_dataclass(self):
        """Test that TraceContext fields cannot be modified."""
        ctx = TraceContext.create_root(RunType.CHAT, 'op')

        with pytest.raises(AttributeError):
            ctx.trace_id = 'new-id'  # type: ignore

        with pytest.raises(AttributeError):
            ctx.run_type = RunType.TOOL  # type: ignore

    def test_metadata_can_be_accessed_but_not_reassigned(self):
        """Test that metadata dict cannot be reassigned."""
        ctx = TraceContext.create_root(
            RunType.CHAT, 'op', metadata={'key': 'value'}
        )

        with pytest.raises(AttributeError):
            ctx.metadata = {}  # type: ignore

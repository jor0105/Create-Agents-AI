import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


from createagents.domain.interfaces.trace_store_interface import (
    TraceEntry,
    TraceSummary,
)
from createagents.infra.stores import (
    FileTraceStore,
    InMemoryTraceStore,
)


def create_sample_entry(
    trace_id: str = 'trace-123',
    run_id: str = 'run-001',
    event: str = 'trace.start',
    run_type: str = 'chat',
    operation: str = 'test_op',
    status: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_name: str = 'TestAgent',
    model: str = 'gpt-4',
    inputs: Optional[dict] = None,
    outputs: Optional[dict] = None,
    duration_ms: Optional[float] = None,
) -> TraceEntry:
    """Create a sample trace entry for testing."""
    return TraceEntry(
        timestamp=datetime.now(timezone.utc),
        trace_id=trace_id,
        run_id=run_id,
        run_type=run_type,
        operation=operation,
        event=event,
        status=status,
        parent_run_id=parent_run_id,
        session_id=session_id,
        agent_name=agent_name,
        model=model,
        inputs=inputs,
        outputs=outputs,
        duration_ms=duration_ms,
    )


class TestTraceEntry:
    def test_create_entry(self):
        entry = create_sample_entry()
        assert entry.trace_id == 'trace-123'
        assert entry.run_id == 'run-001'
        assert entry.event == 'trace.start'

    def test_to_dict(self):
        entry = create_sample_entry(inputs={'msg': 'hello'})
        data = entry.to_dict()

        assert data['trace_id'] == 'trace-123'
        assert data['run_id'] == 'run-001'
        assert data['inputs'] == {'msg': 'hello'}
        assert 'timestamp' in data

    def test_from_dict(self):
        original = create_sample_entry(outputs={'result': 'ok'})
        data = original.to_dict()

        restored = TraceEntry.from_dict(data)

        assert restored.trace_id == original.trace_id
        assert restored.run_id == original.run_id
        assert restored.outputs == original.outputs

    def test_optional_fields_not_included_when_none(self):
        entry = create_sample_entry()
        data = entry.to_dict()

        assert 'inputs' not in data
        assert 'outputs' not in data
        assert 'duration_ms' not in data


class TestInMemoryTraceStore:
    def test_save_and_get_trace(self):
        store = InMemoryTraceStore()

        entry1 = create_sample_entry(event='trace.start')
        entry2 = create_sample_entry(run_id='run-002', event='trace.end')

        store.save_entry(entry1)
        store.save_entry(entry2)

        trace = store.get_trace('trace-123')

        assert trace is not None
        assert trace.trace_id == 'trace-123'
        assert len(trace.entries) == 2

    def test_get_nonexistent_trace(self):
        store = InMemoryTraceStore()
        trace = store.get_trace('nonexistent')
        assert trace is None

    def test_list_traces(self):
        store = InMemoryTraceStore()

        for i in range(5):
            store.save_entry(
                create_sample_entry(trace_id=f'trace-{i}', run_id=f'run-{i}')
            )

        traces = store.list_traces(limit=3)

        assert len(traces) == 3

    def test_list_traces_filter_by_session(self):
        store = InMemoryTraceStore()

        store.save_entry(
            create_sample_entry(trace_id='t1', session_id='session-A')
        )
        store.save_entry(
            create_sample_entry(trace_id='t2', session_id='session-B')
        )
        store.save_entry(
            create_sample_entry(trace_id='t3', session_id='session-A')
        )

        traces = store.list_traces(session_id='session-A')

        assert len(traces) == 2
        assert all(t.session_id == 'session-A' for t in traces)

    def test_list_traces_filter_by_agent_name(self):
        store = InMemoryTraceStore()

        store.save_entry(
            create_sample_entry(trace_id='t1', agent_name='AgentA')
        )
        store.save_entry(
            create_sample_entry(trace_id='t2', agent_name='AgentB')
        )

        traces = store.list_traces(agent_name='AgentA')

        assert len(traces) == 1
        assert traces[0].agent_name == 'AgentA'

    def test_export_traces_jsonl(self):
        store = InMemoryTraceStore()

        store.save_entry(create_sample_entry(trace_id='t1'))
        store.save_entry(create_sample_entry(trace_id='t2'))

        exported = store.export_traces(format='jsonl')

        lines = exported.strip().split('\n')
        assert len(lines) == 2

        for line in lines:
            data = json.loads(line)
            assert 'trace_id' in data

    def test_export_traces_json(self):
        store = InMemoryTraceStore()
        store.save_entry(create_sample_entry())

        exported = store.export_traces(format='json')
        data = json.loads(exported)

        assert isinstance(data, list)
        assert len(data) == 1

    def test_clear_all_traces(self):
        store = InMemoryTraceStore()

        for i in range(3):
            store.save_entry(create_sample_entry(trace_id=f't{i}'))

        count = store.clear_traces()

        assert count == 3
        assert store.get_trace_count() == 0

    def test_clear_specific_traces(self):
        store = InMemoryTraceStore()

        store.save_entry(create_sample_entry(trace_id='t1'))
        store.save_entry(create_sample_entry(trace_id='t2'))
        store.save_entry(create_sample_entry(trace_id='t3'))

        count = store.clear_traces(trace_ids=['t1', 't3'])

        assert count == 2
        assert store.get_trace_count() == 1
        assert store.get_trace('t2') is not None

    def test_max_traces_eviction(self):
        store = InMemoryTraceStore(max_traces=3)

        for i in range(5):
            store.save_entry(create_sample_entry(trace_id=f't{i}'))

        assert store.get_trace_count() == 3
        assert store.get_trace('t0') is None
        assert store.get_trace('t1') is None
        assert store.get_trace('t4') is not None

    def test_trace_summary_fields(self):
        store = InMemoryTraceStore()

        store.save_entry(
            create_sample_entry(
                event='trace.start',
                agent_name='MyAgent',
                model='gpt-4',
                session_id='sess-1',
            )
        )
        store.save_entry(
            create_sample_entry(
                run_id='run-002',
                event='tool.call',
                operation='tool_weather',
            )
        )
        store.save_entry(
            create_sample_entry(
                run_id='run-003',
                event='trace.end',
                status='success',
                duration_ms=1500.0,
            )
        )

        trace = store.get_trace('trace-123')

        assert trace.agent_name == 'MyAgent'
        assert trace.model == 'gpt-4'
        assert trace.session_id == 'sess-1'
        assert trace.status == 'success'
        assert trace.duration_ms == 1500.0
        assert trace.tool_calls_count == 1


class TestFileTraceStore:
    def test_save_and_get_trace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileTraceStore(trace_dir=Path(tmpdir))

            entry = create_sample_entry()
            store.save_entry(entry)

            trace = store.get_trace('trace-123')

            assert trace is not None
            assert trace.trace_id == 'trace-123'

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store1 = FileTraceStore(trace_dir=Path(tmpdir))
            store1.save_entry(create_sample_entry())

            store2 = FileTraceStore(trace_dir=Path(tmpdir))
            trace = store2.get_trace('trace-123')

            assert trace is not None

    def test_list_traces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileTraceStore(trace_dir=Path(tmpdir))

            for i in range(3):
                store.save_entry(
                    create_sample_entry(trace_id=f't{i}', run_id=f'r{i}')
                )

            traces = store.list_traces()

            assert len(traces) == 3

    def test_export_traces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileTraceStore(trace_dir=Path(tmpdir))

            store.save_entry(create_sample_entry())

            exported = store.export_traces(format='jsonl')

            lines = exported.strip().split('\n')
            assert len(lines) >= 1

    def test_clear_all_traces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileTraceStore(trace_dir=Path(tmpdir))

            store.save_entry(create_sample_entry(trace_id='t1'))
            store.save_entry(create_sample_entry(trace_id='t2'))

            count = store.clear_traces()

            assert count == 2
            assert store.get_trace_count() == 0

    def test_file_format_is_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileTraceStore(trace_dir=Path(tmpdir))

            store.save_entry(create_sample_entry())
            store.save_entry(create_sample_entry(run_id='r2'))

            files = list(Path(tmpdir).glob('*.jsonl'))
            assert len(files) == 1

            content = files[0].read_text()
            lines = content.strip().split('\n')
            assert len(lines) == 2

            for line in lines:
                data = json.loads(line)
                assert 'trace_id' in data


class TestTraceSummary:
    def test_is_complete_property(self):
        summary_incomplete = TraceSummary(
            trace_id='t1',
            session_id=None,
            agent_name='Test',
            model='gpt-4',
            start_time=datetime.now(timezone.utc),
            end_time=None,
            duration_ms=None,
            status='in_progress',
            run_count=1,
            tool_calls_count=0,
        )
        assert not summary_incomplete.is_complete

        summary_complete = TraceSummary(
            trace_id='t2',
            session_id=None,
            agent_name='Test',
            model='gpt-4',
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration_ms=100.0,
            status='success',
            run_count=1,
            tool_calls_count=0,
        )
        assert summary_complete.is_complete

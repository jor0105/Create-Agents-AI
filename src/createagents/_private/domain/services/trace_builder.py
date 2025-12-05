"""Service for building trace summaries from trace entries."""

from typing import List

from ..value_objects.tracing import TraceEntry, TraceSummary


def build_trace_summary(
    trace_id: str, entries: List[TraceEntry]
) -> TraceSummary:
    """Build a TraceSummary from a list of trace entries.

    This is a shared helper function used by trace store implementations
    to construct TraceSummary objects from raw entry data.

    Args:
        trace_id: The trace identifier.
        entries: List of trace entries belonging to this trace.

    Returns:
        A fully populated TraceSummary object.

    Raises:
        ValueError: If entries list is empty.
    """
    if not entries:
        raise ValueError(f'No entries for trace_id: {trace_id}')

    sorted_entries = sorted(entries, key=lambda e: e.timestamp)
    first_entry = sorted_entries[0]

    # Find end trace events to determine completion status
    end_entries = [e for e in entries if e.event == 'trace.end']
    end_time = end_entries[-1].timestamp if end_entries else None
    duration = end_entries[-1].duration_ms if end_entries else None

    # Determine status based on end events
    status = 'in_progress'
    if end_entries:
        status = end_entries[-1].status or 'completed'

    # Count tool calls
    tool_calls = sum(1 for e in entries if e.event == 'tool.call')

    return TraceSummary(
        trace_id=trace_id,
        session_id=first_entry.session_id,
        agent_name=first_entry.agent_name,
        model=first_entry.model,
        start_time=first_entry.timestamp,
        end_time=end_time,
        duration_ms=duration,
        status=status,
        run_count=len({e.run_id for e in entries}),
        tool_calls_count=tool_calls,
        entries=sorted_entries,
    )


__all__ = ['build_trace_summary']

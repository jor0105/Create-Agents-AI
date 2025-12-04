"""In-memory implementation of ITraceStore."""

import json
from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional

from ...domain.interfaces.trace_store_interface import (
    ITraceStore,
    TraceEntry,
    TraceSummary,
)
from ...domain.services import build_trace_summary


class InMemoryTraceStore(ITraceStore):
    """In-memory implementation of trace storage.

    Stores traces in memory using thread-safe data structures.
    Suitable for development, testing, and short-lived sessions.

    Note: Data is lost when the process terminates.
    For persistence, use FileTraceStore instead.
    """

    def __init__(self, max_traces: int = 1000):
        """Initialize the in-memory trace store.

        Args:
            max_traces: Maximum number of traces to keep in memory.
                        Oldest traces are evicted when limit is reached.
        """
        self._max_traces = max_traces
        self._entries: Dict[str, List[TraceEntry]] = defaultdict(list)
        self._trace_order: List[str] = []
        self._lock = Lock()

    def save_entry(self, entry: TraceEntry) -> None:
        """Save a trace entry to memory."""
        with self._lock:
            trace_id = entry.trace_id

            if trace_id not in self._entries:
                self._trace_order.append(trace_id)
                self._evict_if_needed()

            self._entries[trace_id].append(entry)

    def get_trace(self, trace_id: str) -> Optional[TraceSummary]:
        """Get a trace summary by ID."""
        with self._lock:
            entries = self._entries.get(trace_id)
            if not entries:
                return None

            return build_trace_summary(trace_id, entries)

    def list_traces(
        self,
        limit: int = 20,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        agent_name: Optional[str] = None,
    ) -> List[TraceSummary]:
        """List traces with optional filters."""
        with self._lock:
            summaries: List[TraceSummary] = []

            for trace_id in reversed(self._trace_order):
                entries = self._entries.get(trace_id, [])
                if not entries:
                    continue

                summary = build_trace_summary(trace_id, entries)

                if session_id and summary.session_id != session_id:
                    continue
                if since and summary.start_time < since:
                    continue
                if agent_name and summary.agent_name != agent_name:
                    continue

                summaries.append(summary)

                if len(summaries) >= limit:
                    break

            return summaries

    def export_traces(
        self,
        trace_ids: Optional[List[str]] = None,
        format: str = 'jsonl',
    ) -> str:
        """Export traces to string format."""
        with self._lock:
            ids_to_export = trace_ids or list(self._entries.keys())
            all_entries: List[TraceEntry] = []

            for trace_id in ids_to_export:
                entries = self._entries.get(trace_id, [])
                all_entries.extend(entries)

            all_entries.sort(key=lambda e: e.timestamp)

            if format == 'json':
                return json.dumps(
                    [e.to_dict() for e in all_entries],
                    indent=2,
                    default=str,
                    ensure_ascii=False,
                )
            else:
                lines = [
                    json.dumps(e.to_dict(), default=str, ensure_ascii=False)
                    for e in all_entries
                ]
                return '\n'.join(lines)

    def clear_traces(
        self,
        older_than: Optional[datetime] = None,
        trace_ids: Optional[List[str]] = None,
    ) -> int:
        """Clear traces from memory."""
        with self._lock:
            deleted_count = 0

            if trace_ids:
                for trace_id in trace_ids:
                    if trace_id in self._entries:
                        del self._entries[trace_id]
                        self._trace_order.remove(trace_id)
                        deleted_count += 1
            elif older_than:
                to_delete: List[str] = []
                for trace_id, entries in self._entries.items():
                    if entries and entries[0].timestamp < older_than:
                        to_delete.append(trace_id)

                for trace_id in to_delete:
                    del self._entries[trace_id]
                    self._trace_order.remove(trace_id)
                    deleted_count += 1
            else:
                deleted_count = len(self._entries)
                self._entries.clear()
                self._trace_order.clear()

            return deleted_count

    def get_trace_count(self) -> int:
        """Get number of traces in memory."""
        with self._lock:
            return len(self._entries)

    def _evict_if_needed(self) -> None:
        """Evict oldest traces if max limit reached."""
        while len(self._trace_order) > self._max_traces:
            oldest_id = self._trace_order.pop(0)
            if oldest_id in self._entries:
                del self._entries[oldest_id]

"""File-based implementation of ITraceStore using JSON Lines format."""

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, Iterator, List, Optional

from ...domain.interfaces.trace_store_interface import (
    ITraceStore,
    TraceEntry,
    TraceSummary,
)
from ...domain.services import build_trace_summary


class FileTraceStore(ITraceStore):
    """File-based implementation of trace storage.

    Persists traces to JSONL (JSON Lines) files for durability.
    Each line is a self-contained JSON object representing one trace entry.

    File format:
        - Default location: ~/.createagents/traces/
        - File pattern: traces_{date}.jsonl
        - Each line: {"timestamp":"...", "trace_id":"...", ...}

    Thread-safe for concurrent writes.
    """

    DEFAULT_TRACE_DIR = Path.home() / '.createagents' / 'traces'

    def __init__(
        self,
        trace_dir: Optional[Path] = None,
        max_file_size_mb: int = 100,
    ):
        """Initialize the file trace store.

        Args:
            trace_dir: Directory for trace files.
                      Defaults to ~/.createagents/traces/
            max_file_size_mb: Max size per trace file before rotation.
        """
        self._trace_dir = trace_dir or self._get_default_dir()
        self._max_file_size = max_file_size_mb * 1024 * 1024
        self._lock = Lock()
        self._ensure_directory()

    def _get_default_dir(self) -> Path:
        """Get default trace directory from env or default path."""
        env_path = os.environ.get('TRACE_STORE_PATH')
        if env_path:
            return Path(env_path)
        return self.DEFAULT_TRACE_DIR

    def _ensure_directory(self) -> None:
        """Ensure trace directory exists."""
        self._trace_dir.mkdir(parents=True, exist_ok=True)

    def _get_current_file(self) -> Path:
        """Get current trace file path."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return self._trace_dir / f'traces_{date_str}.jsonl'

    def _should_rotate(self, file_path: Path) -> bool:
        """Check if file should be rotated."""
        if not file_path.exists():
            return False
        return file_path.stat().st_size >= self._max_file_size

    def _get_all_trace_files(self) -> List[Path]:
        """Get all trace files sorted by date (newest first)."""
        files = list(self._trace_dir.glob('traces_*.jsonl'))
        return sorted(files, reverse=True)

    def _iter_entries(
        self,
        files: Optional[List[Path]] = None,
    ) -> Iterator[TraceEntry]:
        """Iterate over all entries in trace files."""
        trace_files = files or self._get_all_trace_files()

        for file_path in trace_files:
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        yield TraceEntry.from_dict(data)
                    except (json.JSONDecodeError, KeyError):
                        continue

    def save_entry(self, entry: TraceEntry) -> None:
        """Save a trace entry to file."""
        with self._lock:
            file_path = self._get_current_file()

            if self._should_rotate(file_path):
                timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
                new_name = f'traces_{timestamp}.jsonl'
                file_path = self._trace_dir / new_name

            line = json.dumps(entry.to_dict(), default=str, ensure_ascii=False)

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')

    def get_trace(self, trace_id: str) -> Optional[TraceSummary]:
        """Get a trace summary by ID."""
        entries: List[TraceEntry] = []

        for entry in self._iter_entries():
            if entry.trace_id == trace_id:
                entries.append(entry)

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
        traces_by_id: Dict[str, List[TraceEntry]] = defaultdict(list)

        for entry in self._iter_entries():
            if since and entry.timestamp < since:
                continue
            if session_id and entry.session_id != session_id:
                continue
            if agent_name and entry.agent_name != agent_name:
                continue

            traces_by_id[entry.trace_id].append(entry)

        summaries: List[TraceSummary] = []
        for trace_id, entries in traces_by_id.items():
            summary = build_trace_summary(trace_id, entries)
            summaries.append(summary)

        summaries.sort(key=lambda s: s.start_time, reverse=True)
        return summaries[:limit]

    def export_traces(
        self,
        trace_ids: Optional[List[str]] = None,
        format: str = 'jsonl',
    ) -> str:
        """Export traces to string format."""
        entries_to_export: List[TraceEntry] = []

        for entry in self._iter_entries():
            if trace_ids is None or entry.trace_id in trace_ids:
                entries_to_export.append(entry)

        entries_to_export.sort(key=lambda e: e.timestamp)

        if format == 'json':
            return json.dumps(
                [e.to_dict() for e in entries_to_export],
                indent=2,
                default=str,
                ensure_ascii=False,
            )
        else:
            lines = [
                json.dumps(e.to_dict(), default=str, ensure_ascii=False)
                for e in entries_to_export
            ]
            return '\n'.join(lines)

    def clear_traces(
        self,
        older_than: Optional[datetime] = None,
        trace_ids: Optional[List[str]] = None,
    ) -> int:
        """Clear traces from files."""
        with self._lock:
            if older_than is None and trace_ids is None:
                deleted = self.get_trace_count()
                for file_path in self._get_all_trace_files():
                    file_path.unlink()
                return deleted

            entries_to_keep: List[TraceEntry] = []
            deleted_trace_ids: set = set()

            for entry in self._iter_entries():
                should_delete = False

                if trace_ids and entry.trace_id in trace_ids:
                    should_delete = True
                elif older_than and entry.timestamp < older_than:
                    should_delete = True

                if should_delete:
                    deleted_trace_ids.add(entry.trace_id)
                else:
                    entries_to_keep.append(entry)

            for file_path in self._get_all_trace_files():
                file_path.unlink()

            if entries_to_keep:
                for entry in entries_to_keep:
                    self.save_entry(entry)

            return len(deleted_trace_ids)

    def get_trace_count(self) -> int:
        """Get number of unique traces."""
        trace_ids: set = set()
        for entry in self._iter_entries():
            trace_ids.add(entry.trace_id)
        return len(trace_ids)

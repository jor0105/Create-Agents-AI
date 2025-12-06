"""Trace data loader with optimized parsing and tree reconstruction."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import streamlit as st
import pandas as pd

DEFAULT_TRACE_DIR = Path.home() / '.createagents' / 'traces'


@dataclass
class TraceNode:
    """Represents a node in the execution tree (Agent -> Tool -> LLM)."""

    id: str
    name: str
    type: str
    entry: Dict[str, Any]
    children: List['TraceNode'] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = 'running'
    depth: int = 0

    @property
    def duration_ms(self) -> float:
        if self.entry.get('duration_ms'):
            return float(self.entry['duration_ms'])
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    @property
    def type_icon(self) -> str:
        icons = {
            'chain': '🔗',
            'agent': '🧠',
            'llm': '🤖',
            'tool': '🔧',
            'retriever': '📚',
            'embedding': '📊',
            'parser': '📝',
        }
        return icons.get(self.type, '⚡')

    @property
    def status_icon(self) -> str:
        icons = {
            'success': '✅',
            'error': '❌',
            'running': '⏳',
            'started': '▶️',
        }
        return icons.get(self.status, '❓')

    @property
    def status_color(self) -> str:
        colors = {
            'success': '#10B981',
            'error': '#EF4444',
            'running': '#F59E0B',
            'started': '#3B82F6',
        }
        return colors.get(self.status, '#6B7280')

    @property
    def total_tokens(self) -> int:
        total = self.entry.get('total_tokens', 0) or 0
        for child in self.children:
            total += child.total_tokens
        return total

    @property
    def total_cost(self) -> float:
        cost = self.entry.get('cost_usd', 0.0) or 0.0
        for child in self.children:
            cost += child.total_cost
        return cost


class TraceLoader:
    """Optimized trace loader for dashboard consumption."""

    def __init__(self, trace_dir: Path = DEFAULT_TRACE_DIR):
        self.trace_dir = trace_dir

    def get_available_files(self) -> List[Path]:
        """List all .jsonl trace files sorted by modification time (newest first)."""
        if not self.trace_dir.exists():
            return []
        files = list(self.trace_dir.glob('traces_*.jsonl'))
        return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

    def get_file_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get file statistics for display."""
        if not file_path.exists():
            return {}
        stat = file_path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        return {
            'name': file_path.name,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': modified.strftime('%Y-%m-%d %H:%M'),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'lines': self._count_lines(file_path),
        }

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file efficiently."""
        try:
            with open(file_path, 'rb') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    @st.cache_data(ttl=15, show_spinner=False)
    def load_trace_summaries(
        _self,
        file_path: Path,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load trace summaries for the list view with optimized parsing."""
        trace_map: Dict[str, Dict[str, Any]] = {}

        if not file_path.exists():
            return pd.DataFrame()

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    trace_id = data.get('trace_id')
                    if not trace_id:
                        continue

                    if trace_id not in trace_map:
                        trace_map[trace_id] = {
                            'trace_id': trace_id,
                            'run_id': data.get('run_id', ''),
                            'agent_name': 'Unknown',
                            'operation': 'Unknown',
                            'timestamp': None,
                            'status': 'running',
                            'total_tokens': 0,
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'cost_usd': 0.0,
                            'duration_ms': 0.0,
                            'tool_calls': 0,
                            'llm_calls': 0,
                            'error_count': 0,
                            'model': None,
                            'input_preview': '',
                            'output_preview': '',
                            'child_runs': 0,
                        }

                    entry = trace_map[trace_id]
                    event = data.get('event', '')

                    entry['child_runs'] += 1

                    if event == 'tool.call':
                        entry['tool_calls'] += 1
                    elif event in ('llm.request', 'llm.response'):
                        if event == 'llm.request':
                            entry['llm_calls'] += 1

                    if data.get('status') == 'error':
                        entry['error_count'] += 1
                        entry['status'] = 'error'

                    if event == 'trace.start' and not data.get(
                        'parent_run_id'
                    ):
                        entry['agent_name'] = data.get(
                            'agent_name', entry['agent_name']
                        )
                        entry['operation'] = data.get(
                            'operation', entry['operation']
                        )
                        if data.get('timestamp'):
                            entry['timestamp'] = datetime.fromisoformat(
                                data['timestamp']
                            )
                        entry['model'] = data.get('model') or data.get(
                            'data', {}
                        ).get('model')
                        inputs = data.get('inputs', {})
                        if inputs:
                            input_str = str(inputs.get('query', inputs))[:100]
                            entry['input_preview'] = input_str

                    elif event == 'trace.end' and not data.get(
                        'parent_run_id'
                    ):
                        if entry['status'] != 'error':
                            entry['status'] = data.get('status', 'success')
                        entry['duration_ms'] = data.get('duration_ms', 0.0)
                        outputs = data.get('outputs', {})
                        if outputs:
                            output_str = str(outputs.get('response', outputs))[
                                :100
                            ]
                            entry['output_preview'] = output_str

                    if data.get('total_tokens'):
                        entry['total_tokens'] += data.get('total_tokens', 0)
                    if data.get('input_tokens'):
                        entry['input_tokens'] += data.get('input_tokens', 0)
                    if data.get('output_tokens'):
                        entry['output_tokens'] += data.get('output_tokens', 0)
                    if data.get('cost_usd'):
                        entry['cost_usd'] += data.get('cost_usd', 0.0)

                    if data.get('model') and not entry['model']:
                        entry['model'] = data.get('model')
                    if (
                        data.get('data', {}).get('model')
                        and not entry['model']
                    ):
                        entry['model'] = data.get('data', {}).get('model')

                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

        rows = [t for t in trace_map.values() if t['timestamp'] is not None]

        if status_filter and status_filter != 'all':
            rows = [r for r in rows if r['status'] == status_filter]

        if search_query:
            query_lower = search_query.lower()
            rows = [
                r
                for r in rows
                if query_lower in r.get('trace_id', '').lower()
                or query_lower in r.get('agent_name', '').lower()
                or query_lower in r.get('operation', '').lower()
                or query_lower in r.get('input_preview', '').lower()
                or query_lower in r.get('output_preview', '').lower()
                or query_lower in (r.get('model') or '').lower()
            ]

        df = pd.DataFrame(rows)
        if not df.empty:
            df.sort_values('timestamp', ascending=False, inplace=True)
        return df

    def load_full_trace(
        self, trace_id: str, file_paths: List[Path]
    ) -> Optional[TraceNode]:
        """Load and reconstruct a complete trace tree."""
        entries = []

        for file_path in file_paths:
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('trace_id') == trace_id:
                            entries.append(data)
                    except json.JSONDecodeError:
                        continue

            if entries:
                break

        if not entries:
            return None

        return self._build_tree(entries)

    def _build_tree(
        self, entries: List[Dict[str, Any]]
    ) -> Optional[TraceNode]:
        """Reconstruct hierarchical execution tree from flat entries."""
        entries.sort(key=lambda x: x.get('timestamp', ''))

        nodes_by_run_id: Dict[str, TraceNode] = {}
        root: Optional[TraceNode] = None

        for entry in entries:
            run_id = entry.get('run_id')
            event = entry.get('event', '')

            if not run_id:
                continue

            is_start = event in [
                'trace.start',
                'tool.call',
                'llm.request',
                'chain.start',
            ]

            if is_start and run_id not in nodes_by_run_id:
                name = (
                    entry.get('operation')
                    or entry.get('data', {}).get('tool_name')
                    or entry.get('data', {}).get('model')
                    or entry.get('agent_name')
                    or 'Unknown'
                )

                try:
                    start_time = datetime.fromisoformat(entry['timestamp'])
                except (KeyError, ValueError):
                    start_time = datetime.now()

                node = TraceNode(
                    id=run_id,
                    name=name,
                    type=entry.get('run_type', 'unknown'),
                    entry=dict(entry),
                    children=[],
                    start_time=start_time,
                    status='running',
                )
                nodes_by_run_id[run_id] = node

                if not entry.get('parent_run_id') and root is None:
                    root = node

            is_end = event in [
                'trace.end',
                'tool.result',
                'llm.response',
                'chain.end',
            ]

            if run_id in nodes_by_run_id:
                node = nodes_by_run_id[run_id]
                if is_end:
                    if entry.get('timestamp'):
                        try:
                            node.end_time = datetime.fromisoformat(
                                entry['timestamp']
                            )
                        except ValueError:
                            pass
                    node.status = entry.get('status', 'success')
                node.entry.update(entry)

        if root is None and nodes_by_run_id:
            sorted_nodes = sorted(
                nodes_by_run_id.values(),
                key=lambda n: n.start_time or datetime.min,
            )
            root = sorted_nodes[0]

        for run_id, node in nodes_by_run_id.items():
            if node == root:
                continue

            parent_id = node.entry.get('parent_run_id')
            if parent_id and parent_id in nodes_by_run_id:
                parent = nodes_by_run_id[parent_id]
                if node not in parent.children:
                    parent.children.append(node)
                    node.depth = parent.depth + 1
            elif root and node not in root.children:
                root.children.append(node)
                node.depth = 1

        def sort_children(node: TraceNode):
            node.children.sort(key=lambda n: n.start_time or datetime.min)
            for child in node.children:
                sort_children(child)

        if root:
            sort_children(root)

        return root

    def load_all_entries(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load all raw entries from a file."""
        entries: List[Dict[str, Any]] = []
        if not file_path.exists():
            return entries

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    def get_trace_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate aggregate metrics from trace dataframe."""
        if df.empty:
            return {
                'total_runs': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0.0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_duration': 0.0,
                'avg_tokens': 0.0,
                'total_tool_calls': 0,
                'total_llm_calls': 0,
                'p50_duration': 0.0,
                'p95_duration': 0.0,
                'p99_duration': 0.0,
                'models_used': [],
            }

        total = len(df)
        errors = len(df[df['status'] == 'error'])
        successes = total - errors

        duration_series = df['duration_ms'].dropna()

        models = (
            df['model'].dropna().unique().tolist()
            if 'model' in df.columns
            else []
        )

        return {
            'total_runs': total,
            'success_count': successes,
            'error_count': errors,
            'success_rate': (successes / total * 100) if total > 0 else 0.0,
            'total_tokens': int(df['total_tokens'].sum()),
            'total_cost': float(df['cost_usd'].sum()),
            'avg_duration': float(df['duration_ms'].mean())
            if not duration_series.empty
            else 0.0,
            'avg_tokens': float(df['total_tokens'].mean()),
            'total_tool_calls': int(df['tool_calls'].sum()),
            'total_llm_calls': int(df['llm_calls'].sum()),
            'p50_duration': float(duration_series.quantile(0.5))
            if not duration_series.empty
            else 0.0,
            'p95_duration': float(duration_series.quantile(0.95))
            if not duration_series.empty
            else 0.0,
            'p99_duration': float(duration_series.quantile(0.99))
            if not duration_series.empty
            else 0.0,
            'models_used': models,
        }

    def get_timeline_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for timeline visualization."""
        if df.empty:
            return pd.DataFrame()

        timeline = df.copy()
        timeline['hour'] = timeline['timestamp'].dt.floor('h')
        grouped = (
            timeline.groupby('hour')
            .agg(
                {
                    'trace_id': 'count',
                    'total_tokens': 'sum',
                    'cost_usd': 'sum',
                    'duration_ms': 'mean',
                    'error_count': lambda x: (x > 0).sum(),
                }
            )
            .reset_index()
        )
        grouped.columns = [
            'time',
            'runs',
            'tokens',
            'cost',
            'avg_duration',
            'errors',
        ]
        return grouped

    def get_status_breakdown(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get status distribution."""
        if df.empty:
            return {'success': 0, 'error': 0, 'running': 0}
        counts: Dict[str, int] = df['status'].value_counts().to_dict()
        return counts

    def get_model_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get token usage by model."""
        if df.empty or 'model' not in df.columns:
            return pd.DataFrame()

        model_df = df[df['model'].notna()].copy()
        if model_df.empty:
            return pd.DataFrame()

        grouped = (
            model_df.groupby('model')
            .agg(
                {
                    'total_tokens': 'sum',
                    'cost_usd': 'sum',
                    'trace_id': 'count',
                }
            )
            .reset_index()
        )
        grouped.columns = ['model', 'tokens', 'cost', 'calls']
        return grouped.sort_values('tokens', ascending=False)

    def delete_trace(self, trace_id: str, file_path: Path) -> bool:
        """Delete a specific trace from a file.

        Rewrites the file excluding the specified trace_id.
        Returns True if successful, False otherwise.
        """
        if not file_path.exists():
            return False

        try:
            entries_to_keep: List[Dict[str, Any]] = []

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('trace_id') != trace_id:
                            entries_to_keep.append(data)
                    except json.JSONDecodeError:
                        continue

            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in entries_to_keep:
                    f.write(
                        json.dumps(entry, default=str, ensure_ascii=False)
                        + '\n'
                    )

            st.cache_data.clear()
            return True
        except Exception:
            return False

    def delete_multiple_traces(
        self, trace_ids: List[str], file_path: Path
    ) -> int:
        """Delete multiple traces from a file.

        Returns the number of traces deleted.
        """
        if not file_path.exists():
            return 0

        try:
            trace_ids_set = set(trace_ids)
            entries_to_keep: List[Dict[str, Any]] = []
            deleted_count = 0
            seen_trace_ids: set = set()

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        tid = data.get('trace_id')
                        if tid in trace_ids_set:
                            if tid not in seen_trace_ids:
                                deleted_count += 1
                                seen_trace_ids.add(tid)
                        else:
                            entries_to_keep.append(data)
                    except json.JSONDecodeError:
                        continue

            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in entries_to_keep:
                    f.write(
                        json.dumps(entry, default=str, ensure_ascii=False)
                        + '\n'
                    )

            st.cache_data.clear()
            return deleted_count
        except Exception:
            return 0

    def clear_file(self, file_path: Path) -> bool:
        """Clear all traces from a file (truncate to empty).

        Returns True if successful.
        """
        if not file_path.exists():
            return False

        try:
            file_path.write_text('')
            st.cache_data.clear()
            return True
        except Exception:
            return False

    def delete_file(self, file_path: Path) -> bool:
        """Permanently delete a trace file from disk.

        Returns True if successful.
        """
        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            st.cache_data.clear()
            return True
        except Exception:
            return False

    def get_trace_count_in_file(self, file_path: Path) -> int:
        """Count unique trace IDs in a file."""
        if not file_path.exists():
            return 0

        trace_ids: set = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('trace_id'):
                            trace_ids.add(data['trace_id'])
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return 0
        return len(trace_ids)


__all__ = ['TraceLoader', 'TraceNode', 'DEFAULT_TRACE_DIR']

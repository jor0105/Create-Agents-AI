"""CLI command handler for /trace command."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ....utils.text_sanitizer import TextSanitizer
from .base_command import CommandHandler

if TYPE_CHECKING:
    from ....application.facade import CreateAgent
    from ....domain.interfaces.trace_store_interface import TraceSummary


class TraceCommandHandler(CommandHandler):
    """Handles trace-related commands for observability.

    Commands:
        /trace list [--limit N] [--since TIME]
        /trace show <trace_id> [--format tree|json]
        /trace export [--output FILE] [--trace-id ID]
        /trace clear [--older-than TIME]

    Responsibility: Display and manage trace data for debugging.
    """

    def can_handle(self, user_input: str) -> bool:
        """Check if input is a trace command."""
        normalized = self._normalize_input(user_input)
        return normalized.startswith('/trace') or normalized.startswith(
            'trace '
        )

    def execute(self, agent: 'CreateAgent', user_input: str) -> None:
        """Execute the trace command."""
        parts = user_input.strip().split()

        if len(parts) < 2:
            self._show_help()
            return

        subcommand = parts[1].lower()
        args = parts[2:]

        if subcommand == 'list':
            self._handle_list(agent, args)
        elif subcommand == 'show':
            self._handle_show(agent, args)
        elif subcommand == 'export':
            self._handle_export(agent, args)
        elif subcommand == 'clear':
            self._handle_clear(agent, args)
        elif subcommand in ('help', '-h', '--help'):
            self._show_help()
        else:
            self._renderer.render_error(
                f"Unknown subcommand: {subcommand}. Use '/trace help'."
            )

    def get_aliases(self) -> List[str]:
        """Get trace command aliases."""
        return ['/trace', 'trace']

    def _show_help(self) -> None:
        """Show help for trace commands."""
        help_text = """## Trace Commands

| Command | Description |
|---------|-------------|
| `/trace list` | List recent traces |
| `/trace list --limit 20` | List N recent traces |
| `/trace list --since 1h` | Traces from last hour |
| `/trace show <id>` | Show trace details |
| `/trace show <id> --format json` | Export as JSON |
| `/trace export` | Export all traces |
| `/trace export --output file.jsonl` | Export to file |
| `/trace clear` | Clear all traces |
| `/trace clear --older-than 7d` | Clear old traces |
"""
        formatted = TextSanitizer.format_markdown_for_terminal(help_text)
        self._renderer.render_system_message(formatted)

    def _get_trace_store(self, agent: 'CreateAgent') -> Optional[Any]:
        """Get trace store from agent if available."""
        try:
            if hasattr(agent, '_trace_logger') and agent._trace_logger:
                return getattr(agent._trace_logger, 'trace_store', None)
            if hasattr(agent, 'trace_store'):
                return agent.trace_store
        except AttributeError:
            pass
        return None

    def _handle_list(
        self, agent: 'CreateAgent', args: List[str]
    ) -> None:
        """Handle /trace list command."""
        store = self._get_trace_store(agent)
        if not store:
            self._renderer.render_error(
                'Trace store not configured. Enable persistence in agent.'
            )
            return

        limit = 10
        since = None
        session_id = None

        i = 0
        while i < len(args):
            if args[i] == '--limit' and i + 1 < len(args):
                limit = int(args[i + 1])
                i += 2
            elif args[i] == '--since' and i + 1 < len(args):
                since = self._parse_time_delta(args[i + 1])
                i += 2
            elif args[i] == '--session' and i + 1 < len(args):
                session_id = args[i + 1]
                i += 2
            else:
                i += 1

        traces = store.list_traces(
            limit=limit, since=since, session_id=session_id
        )

        if not traces:
            self._renderer.render_system_message('No traces found.')
            return

        output = '## Recent Traces\n\n'
        output += '| Trace ID | Agent | Model | Duration | Status | Tools |\n'
        output += '|----------|-------|-------|----------|--------|-------|\n'

        for trace in traces:
            duration = (
                f'{trace.duration_ms:.0f}ms'
                if trace.duration_ms
                else 'in progress'
            )
            status_icon = self._get_status_icon(trace.status)
            output += (
                f'| `{trace.trace_id[:16]}` | '
                f'{trace.agent_name or "-"} | '
                f'{trace.model or "-"} | '
                f'{duration} | '
                f'{status_icon} | '
                f'{trace.tool_calls_count} |\n'
            )

        formatted = TextSanitizer.format_markdown_for_terminal(output)
        self._renderer.render_system_message(formatted)

    def _handle_show(
        self, agent: 'CreateAgent', args: List[str]
    ) -> None:
        """Handle /trace show <trace_id> command."""
        store = self._get_trace_store(agent)
        if not store:
            self._renderer.render_error('Trace store not configured.')
            return

        if not args:
            self._renderer.render_error(
                'Please provide a trace ID: /trace show <trace_id>'
            )
            return

        trace_id = args[0]
        output_format = 'tree'

        for i, arg in enumerate(args[1:], 1):
            if arg == '--format' and i + 1 < len(args):
                output_format = args[i + 1]

        for t_id in [trace_id, f'trace-{trace_id}']:
            trace = store.get_trace(t_id)
            if trace:
                break

        if not trace:
            self._renderer.render_error(f'Trace not found: {trace_id}')
            return

        if output_format == 'json':
            import json
            output = json.dumps(
                [e.to_dict() for e in trace.entries],
                indent=2,
                default=str,
            )
            self._renderer.render_system_message(f'```json\n{output}\n```')
        else:
            self._render_trace_tree(trace)

    def _render_trace_tree(self, trace: 'TraceSummary') -> None:
        """Render trace as a visual tree."""
        duration = (
            f'{trace.duration_ms:.0f}ms'
            if trace.duration_ms
            else 'in progress'
        )
        status_icon = self._get_status_icon(trace.status)

        output = f"""
╭─────────────────────────────────────────────────────────────────╮
│  🔍 Trace: {trace.trace_id[:40]:<41}│
│  Agent: {(trace.agent_name or 'N/A')[:15]:<15} | Model: {(trace.model or 'N/A')[:15]:<15} | Duration: {duration:<10}│
├─────────────────────────────────────────────────────────────────┤
"""
        entries_by_run: Dict[str, List] = {}
        for entry in trace.entries:
            if entry.run_id not in entries_by_run:
                entries_by_run[entry.run_id] = []
            entries_by_run[entry.run_id].append(entry)

        run_tree = self._build_run_tree(trace.entries)

        for run_id, depth in run_tree:
            entries = entries_by_run.get(run_id, [])
            if not entries:
                continue

            first = entries[0]
            indent = '│  ' + '  ' * depth
            icon = self._get_run_type_icon(first.run_type)

            output += f'{indent}{icon} [{first.run_type.upper()}] {first.operation} ({run_id[:12]})\n'

            for entry in entries:
                if entry.inputs:
                    preview = str(entry.inputs)[:60]
                    output += f'{indent}│  INPUT: {preview}\n'
                if entry.outputs:
                    preview = str(entry.outputs)[:60]
                    output += f'{indent}│  OUTPUT: {preview}\n'
                if entry.duration_ms:
                    output += f'{indent}│  Duration: {entry.duration_ms:.0f}ms\n'

        output += f"""│                                                                 │
│  {status_icon} {trace.status.capitalize():<10} | Duration: {duration:<10} | Runs: {trace.run_count:<5}│
╰─────────────────────────────────────────────────────────────────╯
"""
        self._renderer.render_system_message(output)

    def _build_run_tree(
        self, entries: List[Any]
    ) -> List[tuple]:
        """Build hierarchical tree of runs."""
        runs: Dict[str, Dict] = {}

        for entry in entries:
            if entry.run_id not in runs:
                runs[entry.run_id] = {
                    'parent': entry.parent_run_id,
                    'timestamp': entry.timestamp,
                }

        def get_depth(run_id: str, depth: int = 0) -> int:
            parent = runs.get(run_id, {}).get('parent')
            if parent and parent in runs:
                return get_depth(parent, depth + 1)
            return depth

        result = []
        for run_id in runs:
            depth = get_depth(run_id)
            timestamp = runs[run_id]['timestamp']
            result.append((run_id, depth, timestamp))

        result.sort(key=lambda x: x[2])
        return [(r[0], r[1]) for r in result]

    def _handle_export(
        self, agent: 'CreateAgent', args: List[str]
    ) -> None:
        """Handle /trace export command."""
        store = self._get_trace_store(agent)
        if not store:
            self._renderer.render_error('Trace store not configured.')
            return

        output_file = None
        trace_ids = None
        export_format = 'jsonl'

        i = 0
        while i < len(args):
            if args[i] == '--output' and i + 1 < len(args):
                output_file = args[i + 1]
                i += 2
            elif args[i] == '--trace-id' and i + 1 < len(args):
                trace_ids = [args[i + 1]]
                i += 2
            elif args[i] == '--format' and i + 1 < len(args):
                export_format = args[i + 1]
                i += 2
            else:
                i += 1

        exported = store.export_traces(
            trace_ids=trace_ids, format=export_format
        )

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(exported)
            self._renderer.render_success_message(
                f'Traces exported to: {output_file}'
            )
        else:
            lines = exported.split('\n')
            preview = '\n'.join(lines[:10])
            if len(lines) > 10:
                preview += f'\n... ({len(lines) - 10} more lines)'
            self._renderer.render_system_message(
                f'```\n{preview}\n```\n\nUse --output <file> to save.'
            )

    def _handle_clear(
        self, agent: 'CreateAgent', args: List[str]
    ) -> None:
        """Handle /trace clear command."""
        store = self._get_trace_store(agent)
        if not store:
            self._renderer.render_error('Trace store not configured.')
            return

        older_than = None
        trace_ids = None

        i = 0
        while i < len(args):
            if args[i] == '--older-than' and i + 1 < len(args):
                older_than = self._parse_time_delta(args[i + 1])
                i += 2
            elif args[i] == '--trace-id' and i + 1 < len(args):
                trace_ids = [args[i + 1]]
                i += 2
            else:
                i += 1

        count = store.clear_traces(older_than=older_than, trace_ids=trace_ids)
        self._renderer.render_success_message(f'Cleared {count} trace(s).')

    def _parse_time_delta(self, time_str: str) -> Optional[datetime]:
        """Parse time string like '1h', '7d', '30m' to datetime."""
        now = datetime.now(timezone.utc)
        time_str = time_str.lower().strip()

        try:
            if time_str.endswith('h'):
                hours = int(time_str[:-1])
                return now - timedelta(hours=hours)
            elif time_str.endswith('d'):
                days = int(time_str[:-1])
                return now - timedelta(days=days)
            elif time_str.endswith('m'):
                minutes = int(time_str[:-1])
                return now - timedelta(minutes=minutes)
            elif time_str.endswith('w'):
                weeks = int(time_str[:-1])
                return now - timedelta(weeks=weeks)
        except ValueError:
            pass

        return None

    def _get_status_icon(self, status: str) -> str:
        """Get icon for status."""
        icons = {
            'success': '✅',
            'completed': '✅',
            'error': '❌',
            'in_progress': '🔄',
            'started': '▶️',
        }
        return icons.get(status.lower(), '❓')

    def _get_run_type_icon(self, run_type: str) -> str:
        """Get icon for run type."""
        icons = {
            'chat': '💬',
            'llm': '🤖',
            'tool': '🔧',
            'chain': '🔗',
            'agent': '🤖',
            'retriever': '🔍',
            'embedding': '📊',
        }
        return icons.get(run_type.lower(), '▶️')

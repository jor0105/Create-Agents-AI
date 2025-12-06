"""CreateAgents Trace Dashboard - Professional LangSmith-style observability."""

import streamlit as st

try:
    from examples.dashboard.loader import (
        TraceLoader,
        TraceNode,
        DEFAULT_TRACE_DIR,
    )
except ImportError:
    from loader import TraceLoader, TraceNode, DEFAULT_TRACE_DIR  # type: ignore[no-redef]

st.set_page_config(
    page_title='CreateAgents Traces',
    page_icon='🔍',
    layout='wide',
    initial_sidebar_state='expanded',
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-tertiary: #1a1a24;
    --bg-card: #16161f;
    --bg-hover: #1e1e2a;
    --border-color: rgba(255,255,255,0.06);
    --border-hover: rgba(99,102,241,0.4);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-primary: #6366f1;
    --accent-secondary: #818cf8;
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
    --info: #3b82f6;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
}

.main .block-container {
    padding: 1rem 2rem 2rem 2rem;
    max-width: 100%;
}

/* Header */
.dash-header {
    background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.05) 100%);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.dash-header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.dash-header p {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0.25rem 0 0 0;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1rem;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-1px);
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
}

.metric-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}

.metric-delta {
    font-size: 0.75rem;
    margin-top: 0.25rem;
}

.delta-positive { color: var(--success); }
.delta-negative { color: var(--error); }

/* Trace List */
.trace-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.trace-item {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 0.875rem 1rem;
    cursor: pointer;
    transition: all 0.15s ease;
    display: grid;
    grid-template-columns: auto 1fr auto auto auto auto;
    align-items: center;
    gap: 1rem;
}

.trace-item:hover {
    background: var(--bg-hover);
    border-color: var(--border-hover);
}

.trace-status {
    font-size: 1.25rem;
    width: 28px;
    text-align: center;
}

.trace-info {
    min-width: 0;
}

.trace-operation {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.trace-agent {
    color: var(--text-muted);
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.trace-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

.trace-badge {
    background: rgba(99,102,241,0.15);
    color: var(--accent-secondary);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
}

/* Status Badges */
.status-success { color: var(--success); }
.status-error { color: var(--error); }
.status-running { color: var(--warning); }

/* Tree View */
.tree-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1rem;
}

.tree-node {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin: 0.5rem 0;
    overflow: hidden;
}

.tree-node-header {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    gap: 0.75rem;
    background: rgba(255,255,255,0.02);
}

.tree-node-icon {
    font-size: 1.1rem;
    width: 24px;
    text-align: center;
}

.tree-node-name {
    flex: 1;
    font-weight: 500;
    color: var(--text-primary);
}

.tree-node-type {
    background: rgba(99,102,241,0.15);
    color: var(--accent-secondary);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
}

.tree-node-duration {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
}

.tree-children {
    margin-left: 1.25rem;
    padding-left: 1rem;
    border-left: 2px solid rgba(99,102,241,0.25);
}

/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-tertiary);
    border-radius: 8px;
    padding: 0.25rem;
    gap: 0.25rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    padding: 0.5rem 1rem;
    font-weight: 500;
    font-size: 0.85rem;
}

.stTabs [aria-selected="true"] {
    background: var(--accent-primary);
    color: white;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), #7c3aed);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
    font-size: 0.85rem;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99,102,241,0.4);
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-tertiary);
    border-radius: 8px;
    font-weight: 500;
}

/* JSON Display */
.stJson {
    background: var(--bg-tertiary) !important;
    border-radius: 8px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

/* Hide Streamlit default elements */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6b7280; }

/* Responsive */
@media (max-width: 768px) {
    .main .block-container { padding: 0.75rem; }
    .metric-grid { grid-template-columns: repeat(2, 1fr); }
    .trace-item { grid-template-columns: auto 1fr auto; gap: 0.5rem; }
    .trace-item .trace-meta:nth-child(n+4) { display: none; }
    .dash-header h1 { font-size: 1.25rem; }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def fmt_duration(ms: float) -> str:
    if ms < 1:
        return f'{ms * 1000:.0f}µs'
    if ms < 1000:
        return f'{ms:.0f}ms'
    if ms < 60000:
        return f'{ms / 1000:.1f}s'
    return f'{ms / 60000:.1f}m'


def fmt_tokens(tokens: int) -> str:
    if tokens < 1000:
        return str(tokens)
    if tokens < 1000000:
        return f'{tokens / 1000:.1f}K'
    return f'{tokens / 1000000:.1f}M'


def fmt_cost(cost: float) -> str:
    if cost == 0:
        return '$0'
    if cost < 0.001:
        return f'${cost:.5f}'
    if cost < 0.01:
        return f'${cost:.4f}'
    if cost < 1:
        return f'${cost:.3f}'
    return f'${cost:.2f}'


def render_header():
    st.markdown(
        """
    <div class="dash-header">
        <div>
            <h1>🔍 CreateAgents Traces</h1>
            <p>Real-time observability for AI agent execution</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_metrics(metrics: dict):
    success_rate = metrics['success_rate']
    rate_class = (
        'delta-positive'
        if success_rate >= 95
        else 'delta-negative'
        if success_rate < 80
        else ''
    )

    st.markdown(
        f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{metrics['total_runs']}</div>
            <div class="metric-label">Total Runs</div>
        </div>
        <div class="metric-card">
            <div class="metric-value status-success">✓ {metrics['success_count']}</div>
            <div class="metric-label">Successful</div>
        </div>
        <div class="metric-card">
            <div class="metric-value status-error">{metrics['error_count']}</div>
            <div class="metric-label">Errors</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{success_rate:.1f}%</div>
            <div class="metric-label">Success Rate</div>
            <div class="metric-delta {rate_class}">{'↑ Good' if success_rate >= 95 else '↓ Needs attention' if success_rate < 80 else '→ Acceptable'}</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{fmt_tokens(metrics['total_tokens'])}</div>
            <div class="metric-label">Total Tokens</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{fmt_cost(metrics['total_cost'])}</div>
            <div class="metric-label">Total Cost</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{fmt_duration(metrics['avg_duration'])}</div>
            <div class="metric-label">Avg Duration</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{fmt_duration(metrics['p95_duration'])}</div>
            <div class="metric-label">P95 Latency</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_trace_row(row, idx: int) -> bool:
    status_icon = (
        '✅'
        if row['status'] == 'success'
        else '❌'
        if row['status'] == 'error'
        else '⏳'
    )
    status_class = f'status-{row["status"]}'

    timestamp_str = (
        row['timestamp'].strftime('%H:%M:%S')
        if hasattr(row['timestamp'], 'strftime')
        else str(row['timestamp'])[:8]
    )
    model_badge = (
        f'<span class="trace-badge">{row["model"]}</span>'
        if row.get('model')
        else ''
    )

    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(
            f"""
        <div class="trace-item" style="cursor: default;">
            <span class="trace-status {status_class}">{status_icon}</span>
            <div class="trace-info">
                <div class="trace-operation">{row['operation']}</div>
                <div class="trace-agent">🤖 {row['agent_name']}</div>
            </div>
            <div class="trace-meta">⏰ {timestamp_str}</div>
            <div class="trace-meta">⏱️ {fmt_duration(row['duration_ms'])}</div>
            <div class="trace-meta">🔤 {fmt_tokens(row['total_tokens'])}</div>
            {model_badge}
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        clicked: bool = st.button(
            'View →',
            key=f'btn_{idx}',
            type='primary',
            use_container_width=True,
        )
        return clicked


def render_tree_node(node: TraceNode, depth: int = 0):
    duration_str = fmt_duration(node.duration_ms)

    col1, col2, col3, col4 = st.columns([0.4, 3.5, 1.2, 0.9])

    with col1:
        st.markdown(
            f"<span style='font-size:1.3rem'>{node.status_icon}</span>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.1rem">{node.type_icon}</span>
            <span style="font-weight:600; color:#f8fafc">{node.name}</span>
            <span class="tree-node-type">{node.type}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"<span class='tree-node-duration'>⏱️ {duration_str}</span>",
            unsafe_allow_html=True,
        )

    with col4:
        tokens = node.entry.get('total_tokens', 0)
        if tokens:
            st.markdown(
                f"<span class='tree-node-duration'>🔤 {fmt_tokens(tokens)}</span>",
                unsafe_allow_html=True,
            )

    with st.expander('📋 Details', expanded=depth == 0):
        tabs = st.tabs(['📥 Input', '📤 Output', '📊 Metadata', '⚠️ Errors'])

        with tabs[0]:
            inputs = node.entry.get('inputs', {})
            if inputs:
                st.json(inputs)
            else:
                st.caption('No input data')

        with tabs[1]:
            outputs = node.entry.get('outputs', {})
            if outputs:
                st.json(outputs)
            else:
                st.caption('No output data')

        with tabs[2]:
            meta = {
                'run_id': node.id,
                'run_type': node.type,
                'status': node.status,
                'duration_ms': round(node.duration_ms, 2),
                'start_time': node.start_time.isoformat()
                if node.start_time
                else None,
                'end_time': node.end_time.isoformat()
                if node.end_time
                else None,
            }
            if node.entry.get('model'):
                meta['model'] = node.entry.get('model')
            if node.entry.get('data', {}).get('model'):
                meta['model'] = node.entry.get('data', {}).get('model')
            if node.entry.get('total_tokens'):
                meta['total_tokens'] = node.entry.get('total_tokens')
            if node.entry.get('cost_usd'):
                meta['cost_usd'] = node.entry.get('cost_usd')
            st.json(meta)

        with tabs[3]:
            if node.entry.get('error_message'):
                st.error(f'**Error:** {node.entry.get("error_message")}')
                if node.entry.get('error_type'):
                    st.code(node.entry.get('error_type'), language='text')
                if node.entry.get('error_stack'):
                    st.code(node.entry.get('error_stack'), language='python')
            elif node.status == 'error':
                st.warning('Error occurred but no message captured.')
            else:
                st.success('✓ No errors')

    if node.children:
        st.markdown('<div class="tree-children">', unsafe_allow_html=True)
        for child in node.children:
            render_tree_node(child, depth + 1)
        st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar(loader: TraceLoader) -> tuple:
    with st.sidebar:
        st.markdown(
            """
        <div style="text-align:center; margin-bottom:1.5rem;">
            <span style="font-size:2.5rem">🔬</span>
            <h2 style="margin:0.5rem 0 0; font-size:1.25rem; color:#f8fafc">Trace Explorer</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown('##### 📁 Data Source')
        files = loader.get_available_files()

        if not files:
            st.warning('No trace files found')
            st.info(f'Path: `{loader.trace_dir}`')
            return None, None, None

        selected_file = st.selectbox(
            'Log File',
            files,
            format_func=lambda p: p.name,
            label_visibility='collapsed',
        )

        if selected_file:
            stats = loader.get_file_stats(selected_file)
            st.caption(
                f'📊 {stats.get("size_mb", 0):.2f} MB • {stats.get("lines", 0)} entries'
            )

        st.divider()

        st.markdown('##### 🔍 Filters')

        search_query = st.text_input(
            'Search',
            placeholder='trace ID, agent, operation...',
            label_visibility='collapsed',
        )

        status_filter = st.selectbox(
            'Status',
            ['all', 'success', 'error'],
            format_func=lambda x: f'{"🔘 All" if x == "all" else "✅ Success" if x == "success" else "❌ Errors"}',
            label_visibility='collapsed',
        )

        st.divider()

        st.markdown('##### ⚡ Actions')

        col1, col2 = st.columns(2)
        with col1:
            if st.button('🔄 Refresh', use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button('🔙 Reset', use_container_width=True):
                if 'selected_trace_id' in st.session_state:
                    st.session_state.selected_trace_id = None
                if 'confirm_delete_file' in st.session_state:
                    st.session_state.confirm_delete_file = False
                if 'confirm_clear_file' in st.session_state:
                    st.session_state.confirm_clear_file = False
                st.rerun()

        st.divider()

        st.markdown('##### ⚠️ Danger Zone')

        if selected_file:
            trace_count = loader.get_trace_count_in_file(selected_file)

            with st.expander('🗑️ Delete Options', expanded=False):
                st.warning(
                    '⚠️ **These actions are permanent and cannot be undone!**'
                )

                st.markdown('---')
                st.markdown('**Clear all traces from current file:**')
                st.caption(
                    f'This will delete {trace_count} traces from `{selected_file.name}`'
                )

                if 'confirm_clear_file' not in st.session_state:
                    st.session_state.confirm_clear_file = False

                if not st.session_state.confirm_clear_file:
                    if st.button('🧹 Clear File...', use_container_width=True):
                        st.session_state.confirm_clear_file = True
                        st.rerun()
                else:
                    st.error(
                        '⚠️ Are you sure? This will permanently delete ALL traces!'
                    )
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button(
                            '✅ Yes, Clear',
                            type='primary',
                            use_container_width=True,
                        ):
                            if loader.clear_file(selected_file):
                                st.session_state.confirm_clear_file = False
                                st.success('File cleared!')
                                st.rerun()
                            else:
                                st.error('Failed to clear file.')
                    with col_c2:
                        if st.button('❌ Cancel', use_container_width=True):
                            st.session_state.confirm_clear_file = False
                            st.rerun()

                st.markdown('---')
                st.markdown('**Delete trace file from disk:**')
                st.caption(
                    f'This will permanently remove `{selected_file.name}`'
                )

                if 'confirm_delete_file' not in st.session_state:
                    st.session_state.confirm_delete_file = False

                if not st.session_state.confirm_delete_file:
                    if st.button(
                        '💥 Delete File...', use_container_width=True
                    ):
                        st.session_state.confirm_delete_file = True
                        st.rerun()
                else:
                    st.error(
                        '🚨 DANGER! This will permanently DELETE the file from disk!'
                    )
                    confirm_text = st.text_input(
                        'Type "DELETE" to confirm:',
                        key='delete_confirm_input',
                    )
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        if st.button(
                            '💥 DELETE',
                            type='primary',
                            use_container_width=True,
                        ):
                            if confirm_text == 'DELETE':
                                if loader.delete_file(selected_file):
                                    st.session_state.confirm_delete_file = (
                                        False
                                    )
                                    st.session_state.selected_trace_id = None
                                    st.success('File deleted!')
                                    st.rerun()
                                else:
                                    st.error('Failed to delete file.')
                            else:
                                st.error('Type "DELETE" to confirm.')
                    with col_d2:
                        if st.button(
                            '❌ Cancel',
                            key='cancel_delete',
                            use_container_width=True,
                        ):
                            st.session_state.confirm_delete_file = False
                            st.rerun()

        st.divider()

        st.markdown('##### ℹ️ About')
        st.caption("""
        **CreateAgents Traces**
        Professional observability for AI agents.
        """)

        return selected_file, status_filter, search_query


def main():
    if 'selected_trace_id' not in st.session_state:
        st.session_state.selected_trace_id = None

    loader = TraceLoader(DEFAULT_TRACE_DIR)

    selected_file, status_filter, search_query = render_sidebar(loader)

    if not selected_file:
        render_header()
        st.info('👈 Select a trace file from the sidebar to begin')

        st.markdown("""
        ### Getting Started

        1. **Generate traces** by running your CreateAgents application
        2. Traces are stored in `~/.createagents/traces/`
        3. Select a log file from the sidebar
        4. Click **View →** on a trace to see detailed execution tree

        ### Quick Test

        ```bash
        poetry run python examples/dashboard/trace_generator.py
        ```
        """)
        return

    render_header()

    with st.spinner('Loading traces...'):
        df = loader.load_trace_summaries(
            selected_file, status_filter, search_query
        )

    if df.empty:
        st.info('📭 No traces found matching your filters')
        return

    metrics = loader.get_trace_metrics(df)
    render_metrics(metrics)

    st.divider()

    if st.session_state.selected_trace_id:
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(
                f'### 🔬 Trace: `{st.session_state.selected_trace_id[:12]}...`'
            )
        with col2:
            if st.button('← Back', type='secondary', use_container_width=True):
                st.session_state.selected_trace_id = None
                st.session_state.confirm_delete_trace = False
                st.rerun()
        with col3:
            if 'confirm_delete_trace' not in st.session_state:
                st.session_state.confirm_delete_trace = False

            if not st.session_state.confirm_delete_trace:
                if st.button(
                    '🗑️ Delete', type='secondary', use_container_width=True
                ):
                    st.session_state.confirm_delete_trace = True
                    st.rerun()

        if st.session_state.confirm_delete_trace:
            st.error(
                '⚠️ **Delete this trace permanently?** This action cannot be undone.'
            )
            del_col1, del_col2, del_col3 = st.columns([2, 1, 1])
            with del_col1:
                st.caption(f'Trace ID: `{st.session_state.selected_trace_id}`')
            with del_col2:
                if st.button(
                    '✅ Yes, Delete', type='primary', use_container_width=True
                ):
                    if loader.delete_trace(
                        st.session_state.selected_trace_id, selected_file
                    ):
                        st.session_state.selected_trace_id = None
                        st.session_state.confirm_delete_trace = False
                        st.toast('✅ Trace deleted successfully!')
                        st.rerun()
                    else:
                        st.error('Failed to delete trace.')
            with del_col3:
                if st.button(
                    '❌ Cancel',
                    use_container_width=True,
                    key='cancel_trace_del',
                ):
                    st.session_state.confirm_delete_trace = False
                    st.rerun()

        with st.spinner('Loading trace tree...'):
            root_node = loader.load_full_trace(
                st.session_state.selected_trace_id, [selected_file]
            )

        if root_node:
            trace_rows = df[
                df['trace_id'] == st.session_state.selected_trace_id
            ]
            if not trace_rows.empty:
                trace_row = trace_rows.iloc[0]

                cols = st.columns(6)
                with cols[0]:
                    status_emoji = (
                        '✅' if trace_row['status'] == 'success' else '❌'
                    )
                    st.metric(
                        'Status',
                        f'{status_emoji} {trace_row["status"].upper()}',
                    )
                with cols[1]:
                    st.metric(
                        'Duration', fmt_duration(trace_row['duration_ms'])
                    )
                with cols[2]:
                    st.metric('Tokens', fmt_tokens(trace_row['total_tokens']))
                with cols[3]:
                    st.metric('Tool Calls', trace_row['tool_calls'])
                with cols[4]:
                    st.metric('LLM Calls', trace_row['llm_calls'])
                with cols[5]:
                    st.metric('Cost', fmt_cost(trace_row['cost_usd']))

            st.divider()

            st.markdown('### 🌳 Execution Tree')
            with st.container():
                render_tree_node(root_node)

            with st.expander('📄 Raw JSON'):
                entries = loader.load_all_entries(selected_file)
                trace_entries = [
                    e
                    for e in entries
                    if e.get('trace_id') == st.session_state.selected_trace_id
                ]
                st.json(trace_entries)
        else:
            st.error('Could not load trace tree. Data may be incomplete.')

    else:
        st.markdown('### 📋 Recent Traces')

        for idx, (_, row) in enumerate(df.head(100).iterrows()):
            if render_trace_row(row, idx):
                st.session_state.selected_trace_id = row['trace_id']
                st.rerun()

        if len(df) > 100:
            st.info(
                f'Showing first 100 traces. {len(df) - 100} more available.'
            )


if __name__ == '__main__':
    main()

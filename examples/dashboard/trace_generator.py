import time
import random
import uuid
from datetime import datetime, timezone

# We only use exposed public APIs.
# This ensures the dashboard always reflects what real users see.
from createagents.tracing import FileTraceStore


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_simulation():
    print('🚀 Starting Public Trace Generator Simulation...')
    print("Using ONLY exposed 'FileTraceStore' to generate data.")

    # Initialize the public trace store
    # This matches exactly how a user writes custom traces or how the library persists them.
    store = FileTraceStore()

    # Define some scenarios to simulate diverse usage
    scenarios = [
        ('Calculate 50 + 50', 'calculator', '50 + 50', '100'),
        (
            "Search for 'Python Agents'",
            'google_search',
            'Python Agents',
            'Found 10 results',
        ),
        (
            'Summarize text',
            'summarizer',
            'Long text...',
            'Summary: This is a short summary.',
        ),
        ('Translate Hello', 'translator', 'Hello', 'Hola'),
    ]

    for i in range(5):
        scenario = random.choice(scenarios)
        query, tool_name, tool_input, tool_output = scenario

        trace_id = generate_uuid()
        run_id_chain = generate_uuid()
        run_id_llm = generate_uuid()

        # Store start time to calculate duration later
        start_ts = datetime.now(timezone.utc)
        timestamp_start = start_ts.isoformat()

        # 1. Start Trace (Agent Run)
        # This mirrors the schema documented in createagents.tracing.__init__.py
        store.save(
            {
                'trace_id': trace_id,
                'run_id': run_id_chain,
                'run_type': 'chain',
                'operation': 'AgentWorkflow',
                'event': 'trace.start',
                'timestamp': timestamp_start,
                'agent_name': 'DemoAgent',
                'inputs': {'query': query},
            }
        )

        time.sleep(0.1)

        # 2. LLM Call (Think) - Start
        llm_start_ts = datetime.now(timezone.utc)
        store.save(
            {
                'trace_id': trace_id,
                'run_id': run_id_llm,
                'parent_run_id': run_id_chain,
                'run_type': 'llm',
                'operation': 'Plan Step',
                'event': 'llm.request',
                'timestamp': llm_start_ts.isoformat(),
                'inputs': {'messages': [{'role': 'user', 'content': query}]},
                'model': 'gpt-5-nano',
            }
        )

        time.sleep(0.2)

        # 2. LLM Call (Think) - End
        llm_end_ts = datetime.now(timezone.utc)
        llm_duration = (llm_end_ts - llm_start_ts).total_seconds() * 1000
        store.save(
            {
                'trace_id': trace_id,
                'run_id': run_id_llm,
                'parent_run_id': run_id_chain,
                'run_type': 'llm',
                'operation': 'Plan Step',
                'event': 'llm.response',
                'timestamp': llm_end_ts.isoformat(),
                'status': 'success',
                'outputs': {'response': f'I should use the tool: {tool_name}'},
                'total_tokens': random.randint(50, 200),
                'cost_usd': 0.0002,
                'duration_ms': llm_duration,
            }
        )

        # 3. Tool Call
        # 80% chance of tool execution
        if random.random() > 0.2:
            run_id_tool = generate_uuid()
            tool_start_ts = datetime.now(timezone.utc)

            store.save(
                {
                    'trace_id': trace_id,
                    'run_id': run_id_tool,
                    'parent_run_id': run_id_chain,
                    'run_type': 'tool',
                    'operation': tool_name,
                    'event': 'tool.call',
                    'timestamp': tool_start_ts.isoformat(),
                    'inputs': {'arg': tool_input},
                }
            )

            time.sleep(0.1)

            tool_end_ts = datetime.now(timezone.utc)
            tool_duration = (
                tool_end_ts - tool_start_ts
            ).total_seconds() * 1000

            # Simulate random failure
            is_success = random.random() > 0.1

            store.save(
                {
                    'trace_id': trace_id,
                    'run_id': run_id_tool,
                    'parent_run_id': run_id_chain,
                    'run_type': 'tool',
                    'operation': tool_name,
                    'event': 'tool.result',
                    'timestamp': tool_end_ts.isoformat(),
                    'status': 'success' if is_success else 'error',
                    'outputs': {
                        'result': tool_output
                        if is_success
                        else 'Connection Error'
                    },
                    'duration_ms': tool_duration,
                }
            )

        # 4. End Trace
        end_ts = datetime.now(timezone.utc)
        total_duration = (end_ts - start_ts).total_seconds() * 1000

        store.save(
            {
                'trace_id': trace_id,
                'run_id': run_id_chain,
                'run_type': 'chain',
                'operation': 'AgentWorkflow',
                'event': 'trace.end',
                'timestamp': end_ts.isoformat(),
                'status': 'success',
                'outputs': {'response': 'Task completed successfully.'},
                'total_tokens': random.randint(100, 300),
                'cost_usd': 0.005,
                'duration_ms': total_duration,
            }
        )

        print(f'✅ Generated trace {trace_id}')
        time.sleep(0.5)

    print(
        '\n✨ Done! Now run: poetry run streamlit run examples/dashboard/app.py'
    )


if __name__ == '__main__':
    run_simulation()

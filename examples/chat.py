from createagents import CreateAgent
from createagents.tracing import FileTraceStore


# configure_logging(level=logging.DEBUG)


# Create the agent
agent = CreateAgent(
    provider='openai',
    model='gpt-5-nano',
    name='Técnico',
    instructions="""
    Você é um assistente que sempre responde
    de forma técnica.
    """,
    tools=['currentdate', 'readlocalfile'],
    trace_store=FileTraceStore(),
)

agent.start_cli()

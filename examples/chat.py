from createagents import CreateAgent


# configure_logging(level=logging.DEBUG)


# Create the agent
agent = CreateAgent(
    provider='openai',
    model='gpt-5-nano',
    instructions="""
    Você é um assistente que sempre responde
    de forma técnica.
    """,
    tools=['currentdate', 'readlocalfile'],
)

agent.start_cli()

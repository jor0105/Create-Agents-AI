from createagents import CreateAgent

agent = CreateAgent(
    provider="ollama",
    model="gpt-oss:120b-cloud",
    name="Test Agent",
    instructions="You are a helpful assistant.",
    tools=["currentdate"],
)

agent.get_system_available_tools()
agent.get_all_available_tools()

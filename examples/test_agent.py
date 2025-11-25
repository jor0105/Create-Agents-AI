from createagents import CreateAgent, LoggingConfig     # type: ignore
# import logging


# LoggingConfig.configure_for_development(level=logging.INFO)


agent = CreateAgent(
    provider="ollama",
    model="gpt-oss:120b-cloud",
    name="Chatbot Amigável",
    instructions="Use emojis quando apropriado.",
    tools=["currentdate"],
)
while True:
    user_input = input("Você: ")
    if user_input.lower() in ["sair", "exit", "quit"]:
        break
    response = agent.chat(user_input)
    print(f"Bot: {response}\n")

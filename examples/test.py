import logging

from examples.websearchtool import WebSearchTool
from src import AIAgent
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(level=logging.ERROR)


tools = [WebSearchTool()]

config = {
    "temperature": 0.7,
    "max_tokens": 300,
}

agent = AIAgent(
    provider="openai",
    model="gpt-5-mini",
    name="AgenteTeste",
    instructions="Responda como um assistente educado.",
    # config=config,
    tools=tools,
)
# user_message = "Olá, quem é você?"
# response = agent.chat(user_message)
# print(f"Resposta do agente: {response}")
# print(f"Agente criado: {agent}")


# Segundo exemplo de uso do AIAgent
agent2 = AIAgent(
    provider="ollama",
    model="gpt-oss:120b-cloud",
    name="Agente Ollama",
    instructions="Responda como uma pessoa extremamente culta",
    # config=config,
    tools=tools,
)

# Exemplo de chat
user_message = "como ficar milionario hoje com marketing digital? qual é a melhor estrategia atualmente e pensando no futuro?"

# response = agent.chat(user_message)
# print(f"Resposta do agente: {response}")

print(100 * "_")

response2 = agent2.chat(user_message)
print(f"Resposta do agente 2: {response2}")

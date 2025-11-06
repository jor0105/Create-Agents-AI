from src import AIAgent

# Primeiro exemplo de uso do AIAgent
provider = "openai"  # ou "ollama"
model = "gpt-4.1-mini"  # ou outro modelo suportado
name = "AgenteTeste"
instructions = "Responda como um assistente educado."
tools = ["stock_price"]
config = {
    "temperature": 0.7,
    "max_tokens": 300,
}

agent = AIAgent(
    provider=provider,
    model=model,
    name=name,
    instructions=instructions,
    config=config,
    tools=tools,
)
user_message = "Olá, quem é você?"
response = agent.chat(user_message)
print(f"Resposta do agente: {response}")
print(f"Agente criado: {agent}")

# Segundo exemplo de uso do AIAgent
agent2 = AIAgent(
    provider="ollama",
    model="gpt-oss:120b-cloud",
    name="Agente Tests",
    instructions="Responda como uma pessoa extremamente culta",
    config=config,
)

# Exemplo de chat
user_message = "Olá, quem é você?"
response = agent2.chat(user_message)
print(f"Resposta do agente: {response}")

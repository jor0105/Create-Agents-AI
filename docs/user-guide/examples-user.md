# Exemplos Práticos de Uso

Veja casos reais de uso do Create Agents AI.

## Assistente Educacional

```python
professor = CreateAgent(
    provider="openai",
    model="gpt-5-nano",
    name="Professor Virtual",
    instructions="Você é um professor didático."
)
response = professor.chat("Explique recursão em programação")
print(response)
```

## Assistente Corporativo

```python
assistente = CreateAgent(
    provider="openai",
    model="gpt-5",
    name="Assistente Executivo",
    instructions="Use linguagem formal.",
    tools=["currentdate"]
)
response = assistente.chat("Que dia é hoje? Preciso agendar uma reunião")
print(response)
```

## Code Assistant

```python
code_expert = CreateAgent(
    provider="openai",
    model="gpt-4.1-mini",
    name="Python Expert",
    instructions="Especialista em Python."
)
codigo = code_expert.chat("Crie uma função que valida CPF brasileiro.")
print(codigo)
```

## Tradutor Profissional

```python
tradutor = CreateAgent(
    provider="openai",
    model="gpt-4o",
    name="Tradutor Especializado",
    instructions="Você é um tradutor profissional."
)
response = tradutor.chat(
    "Traduza para inglês: 'A arquitetura clean separa as regras de negócio da infraestrutura.'"
)
print(response)
```

## Analista de Dados

```python
analista = CreateAgent(
    provider="ollama",
    model="granite4:latest",
    name="Data Analyst",
    instructions="Forneça insights acionáveis."
)
dados = "Vendas Q1: Jan=100k, Fev=150k, Mar=120k"
response = analista.chat(f"Analise estes dados: {dados}")
print(response)
```

## Chatbot Interativo Completo

```python
chatbot = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Chatbot Amigável",
    instructions="Use emojis quando apropriado."
)
while True:
    user_input = input("Você: ")
    if user_input.lower() in ["sair", "exit", "quit"]:
        break
    response = chatbot.chat(user_input)
    print(f"Bot: {response}\n")
```

## Agente Local com Ollama

```python
agente_local = CreateAgent(
    provider="ollama",
    model="llama2",
    name="Assistente Privado",
    instructions="Você é um assistente local."
)
response = agente_local.chat("Explique machine learning em termos simples")
print(response)
```

## Monitoramento com Métricas

```python
agente = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Agente Monitorado",
    tools=["currentdate"]
)
for i in range(5):
    agente.chat(f"Mensagem de teste {i+1}")
metrics = agente.get_metrics()
print(metrics)
```

## Próximos Passos

- [FAQ](faq-user.md)

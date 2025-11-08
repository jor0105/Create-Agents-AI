# 🎯 Guia de Uso Básico

Aprenda os fundamentos do **AI Agent Creator**.

---

## 🚀 Primeiro Agente

```python
from src.presentation import AIAgent

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você é um assistente útil"
)
```

---

## 💬 Conversando

### Chat Simples

```python
response = agent.chat("Olá! Como você está?")
print(response)

# Histórico é mantido automaticamente
response = agent.chat("Qual é a capital do Brasil?")
response = agent.chat("E a população?")  # Usa contexto
```

### Chat Interativo

```python
print("Chatbot iniciado! Digite 'sair' para encerrar.\n")

while True:
    user_input = input("Você: ")

    if user_input.lower() in ['sair', 'exit']:
        break

    response = agent.chat(user_input)
    print(f"Bot: {response}\n")
```

---

## 📊 Configurações

### Ver Configurações

```python
config = agent.get_configs()
print(f"Modelo: {config['model']}")
print(f"Histórico: {len(config['history'])} mensagens")
```

### Limpar Histórico

```python
agent.clear_history()
```

**Quando limpar:**

- Ao mudar de assunto
- Para economizar tokens
- Quando histórico ficar longo

---

## ⚙️ Personalizando

```python
# Formal
agent_formal = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Use linguagem formal e corporativa"
)

# Técnico
agent_tecnico = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Especialista em Python. Forneça código detalhado"
)
```

---

## 🔧 Configurações Avançadas

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Assistente customizado",
    config={
        "temperature": 0.7,  # Criatividade
        "max_tokens": 2000,  # Limite
    },
    history_max_size=50
)
```

---

## 🛠️ Ferramentas

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["current_date"]
)

# Agente usa automaticamente
response = agent.chat("Que dia é hoje?")
```

---

## 📊 Métricas

```python
metrics = agent.get_metrics()
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

---

## 🎯 Próximos Passos

- [Exemplos Práticos](exemplos.md)
- [Ferramentas](../tools.md)
- [API Reference](../api.md)

---

**Versão:** 0.1.0 | **Atualização:** Novembro 2025

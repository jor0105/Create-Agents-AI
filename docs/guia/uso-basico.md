# 🎯 Guia de Uso Básico

Aprenda os fundamentos do **AI Agent Creator**.

---

## 🚀 Primeiro Agente

```python
from createagents import CreateAgent

agent = CreateAgent(
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

try:
    while True:
        user_input = input("Você: ").strip()

        if not user_input:
            # ignora entradas vazias
            continue

        if user_input.lower() in ("sair", "exit", "quit"):
            print("Encerrando chat. Até logo!")
            break

        try:
            response = agent.chat(user_input)
        except Exception as e:
            # evita crash se agent.chat falhar; logue ou mostre uma mensagem amigável
            print(f"Erro ao gerar resposta: {e}")
            continue

        # Se response não for string, adapte a formatação conforme necessário
        print(f"Bot: {response}\n")

except KeyboardInterrupt:
    print("\nChat interrompido pelo usuário. Saindo...")
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
agent_formal = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Use linguagem formal e corporativa"
)

# Técnico
agent_tecnico = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Especialista em Python. Forneça código detalhado"
)
```

---

## 🔧 Configurações Avançadas

```python
agent = CreateAgent(
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

### Usar Ferramentas Disponíveis

```python
# Adicionar ferramentas ao agente
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate"]  # Ferramentas do sistema
)

# Agente usa automaticamente
response = agent.chat("Que dia é hoje?")
```

### Verificar Ferramentas Disponíveis

```python
# Ver todas as ferramentas do agente (sistema + customizadas)
all_tools = agent.get_all_available_tools()
print("Ferramentas do agente:")
for name, description in all_tools.items():
    print(f"  • {name}: {description[:50]}...")

# Ver apenas ferramentas do sistema (built-in)
system_tools = agent.get_system_available_tools()
print("\nFerramentas do sistema:")
for name, description in system_tools.items():
    print(f"  • {name}")

# Verificar se ferramenta opcional está instalada
if "readlocalfile" in system_tools:
    print("✅ ReadLocalFileTool disponível")
else:
    print("⚠️  Instale com: poetry install -E file-tools")
```

### Criar Ferramentas Customizadas

```python
from ..domain import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs mathematical calculations"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }

    def execute(self, expression: str) -> str:
        return str(eval(expression))

# Usar ferramenta customizada
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", CalculatorTool()]  # Sistema + customizada
)

# Ver todas as ferramentas (incluindo a customizada)
tools = agent.get_all_available_tools()
print(f"Total de ferramentas: {len(tools)}")
# Saída: Total de ferramentas: 3
# (currentdate, readlocalfile, calculator)
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

**Versão:** 0.1.0 | **Atualização:** 17/11/2025

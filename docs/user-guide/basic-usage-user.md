# Guia de Uso Básico do Usuário

Aprenda a criar e interagir com agentes de IA rapidamente.

## Primeiro Agente

```python
from createagents import CreateAgent
agent = CreateAgent(provider="openai", model="gpt-4", instructions="Você é um assistente útil")
```

## Conversando

```python
response = agent.chat("Olá! Como você está?")
print(response)
response = agent.chat("Qual é a capital do Brasil?")
response = agent.chat("E a população?")
```

## Configurações

```python
config = agent.get_configs()
print(f"Modelo: {config['model']}")
print(f"Histórico: {len(config['history'])} mensagens")
```

## Limpar Histórico

```python
agent.clear_history()
```

## Personalizando

```python
agent_formal = CreateAgent(
    provider="openai", 
    model="gpt-4", 
    instructions="Use linguagem formal"
)
agent_tecnico = CreateAgent(
    provider="openai",
    model="gpt-4", 
    instructions="Especialista em Python"
)
```

## Configurações Avançadas

```python
agent = CreateAgent(
    provider="openai", 
    model="gpt-4", 
    config={"temperature": 0.7, "max_tokens": 2000}, 
    history_max_size=50
)
```

## Ferramentas

```python
agent = CreateAgent(
    provider="openai", 
    model="gpt-4", 
    tools=["currentdate"]
)
response = agent.chat("Que dia é hoje?")
```

## Verificar Ferramentas Disponíveis

```python
all_tools = agent.get_all_available_tools()
for name, description in all_tools.items():
    print(f"• {name}: {description[:50]}...")
```

## Criar Ferramentas Customizadas

```python
from createagents import BaseTool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Realiza cálculos matemáticos"
    parameters = {
        "type": "object", 
        "properties": {
            "expression": {
                "type": "string", 
                "description": "Expressão matemática"
            }
        }, 
        "required": ["expression"]
    }
    def execute(self, expression: str) -> str:
        return str(eval(expression))
```

## Métricas

```python
metrics = agent.get_metrics()
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

## Próximos Passos

- [Exemplos](examples-user.md)
- [FAQ](faq-user.md)

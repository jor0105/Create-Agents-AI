# Exemplos Técnicos para Desenvolvedores

Veja exemplos avançados de uso, extensão e integração do Create Agents AI.

## Criar Ferramenta Customizada

```python
from createagents import BaseTool
class MyTool(BaseTool):
    name = "my_tool"
    description = "Minha ferramenta personalizada"
    parameters = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "Texto de entrada"
            }
        },
        "required": ["input"]
    }
    def execute(self, input: str) -> str:
        return f"Resultado: {input}"
```

## Novo Adapter de Provedor

```python
from createagents.application.interfaces import ChatRepository
class ClaudeAdapter(ChatRepository):
    def chat(self, ...):
        # Implementação para Claude
        pass
```

## Testes Unitários

```python
import pytest
from unittest import TestCase
from unittest.mock import patch
from createagents import CreateAgent

@pytest.mark.unitest
class TestAgentChat(TestCase):
    @patch("createagents.application.facade.client.OpenAIChatAdapter")
    def test_chat(self, mock_adapter):
        # Configura o mock para simular resposta da API
        mock_adapter.return_value.chat.return_value = "Olá, mundo!"
        agent = CreateAgent(provider="openai", model="gpt-4")
        response = agent.chat("Teste")
        self.assertEqual(response, "Olá, mundo!")
```

## Integração com CI/CD

- Use `pytest` e `pytest-cov` para cobertura.

## Extensão de Métricas

```python
metrics = agent.get_metrics()
agent.export_metrics_json("metrics.json")
```

## Contribuindo

Veja [Como Contribuir](contribute.md).

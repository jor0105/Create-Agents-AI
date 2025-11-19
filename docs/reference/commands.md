# Referência de Comandos e Configurações

Veja comandos úteis, parâmetros de configuração e dicas para uso avançado do Create Agents AI.

## Comandos Básicos

- Instalar dependências:
  ```bash
  poetry install
  poetry install -E file-tools
  ```
- Rodar testes:
  ```bash
  poetry run pytest
  ```
- Ativar ambiente:
  ```bash
  poetry shell
  ```

## Configurações do Modelo

```python
config = {
    "temperature": 0.7,   # Criatividade
    "max_tokens": 2000,   # Limite de tokens
    "top_p": 0.9,         # Nucleus sampling
    "think": True,        # Ollama: bool / OpenAI: str = "high", "low" or "effort"
    "top_k": 40,          # Ollama
}
```

## Exportando Métricas

```python
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

## Dicas Avançadas

- Use múltiplos agentes para especialização
- Combine ferramentas built-in e customizadas
- Use modelos locais para privacidade

## Links Relacionados

- [Ferramentas](tools.md)
- [API Reference](../api.md)
- [Guia do Usuário](../user-guide/installation-user.md)

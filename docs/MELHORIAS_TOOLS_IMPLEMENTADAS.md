### 🔄 Uso Futuro

Embora **atualmente não estejamos salvando tool calls no histórico** (para manter a interface do `ChatRepository` simples), a infraestrutura está pronta para isso:

```python
# Exemplo de uso futuro:
if response.has_tool_calls():
    for tool_call in response.tool_calls:
        agent.add_tool_message(
            f"Tool '{tool_call.tool_name}' executed with result: {tool_call.result}"
        )
```

---

## 🚀 Como Usar

### OpenAI (sem mudanças visíveis)

```python
from src.main.composers import create_agent_composer, chat_with_agent_composer

# Criar agente com tools
agent = create_agent_composer(
    provider="openai",
    model="gpt-4",
    tools=["web_search", "stock_price"]  # ← Tools NÃO vão pro prompt
)

# Chat (tools executadas automaticamente)
response = chat_with_agent_composer(
    agent=agent,
    message="What is the price of PETR4?"
)
# → "The current price of PETR4 stock is R$ 38.50."
```

### Ollama (NOVA funcionalidade)

```python
# Criar agente com tools
agent = create_agent_composer(
    provider="ollama",
    model="llama3.2",
    tools=["web_search", "stock_price"]  # ← Tools vão pro prompt + parser
)

# Chat (tools AGORA são executadas automaticamente!)
response = chat_with_agent_composer(
    agent=agent,
    message="What is the price of PETR4?"
)
# → Model detecta necessidade → Executa tool → Retorna resultado
```

### Configurar Max Iterações

```bash
# .env
OLLAMA_MAX_TOOL_ITERATIONS=10  # Padrão: 5
OPENAI_MAX_TOOL_ITERATIONS=10  # Padrão: 5
```

---

## 📝 Notas Técnicas

### Por que não salvamos tool calls no histórico ainda?

**Decisão arquitetural:**

1. **Interface simples**: `ChatRepository.chat()` retorna `str`, não objeto complexo
2. **Compatibilidade**: Não quebra código existente
3. **Infraestrutura pronta**: Quando necessário, basta usar `ChatResponse`
4. **Resposta final suficiente**: Para a maioria dos casos, apenas a resposta final importa

### Quando adicionar tool calls ao histórico?

**Casos de uso futuros:**

- Auditoria completa de conversas
- Debugging de tool executions
- Fine-tuning de modelos
- Análise de uso de ferramentas

**Implementação seria simples:**

```python
# No ChatWithAgentUseCase
if response.has_tool_calls():
    for tool_call in response.tool_calls:
        agent.add_tool_message(f"[{tool_call.tool_name}]: {tool_call.result}")
```

---

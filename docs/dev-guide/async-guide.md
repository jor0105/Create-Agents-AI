# Guia de Programação Assíncrona

Este guia explica como a arquitetura assíncrona funciona no CreateAgents AI.

---

## 🔄 Por Que Async?

O CreateAgents AI usa programação assíncrona para:

- **Streaming**: Tokens em tempo real das APIs (OpenAI/Ollama)
- **Tools**: Execução não-bloqueante de ferramentas
- **Performance**: Múltiplas chamadas concorrentes

---

## 🎯 Componentes Assíncronos

### ChatRepository (Interface)

```python
class ChatRepository(ABC):
    @abstractmethod
    async def chat(self, agent: Agent, message: str) -> AsyncGenerator[str, None]:
        """Chat assíncrono que retorna AsyncGenerator."""
        pass
```

### ChatAdapter (Implementação)

```python
class OpenAIChatAdapter(ChatRepository):
    async def chat(self, agent: Agent, message: str) -> AsyncGenerator[str, None]:
        handler = OpenAIStreamHandler(...)
        async for token in handler.handle_streaming(...):
            yield token
```

### Stream Handlers

#### OpenAIStreamHandler

```python
class OpenAIStreamHandler:
    async def handle_streaming(
        self,
        client,
        model: str,
        messages,
        ...
    ) -> AsyncGenerator[str, None]:
        # Inicia streaming
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            ...
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

#### OllamaStreamHandler

```python
class OllamaStreamHandler:
    async def handle_streaming(
        self,
        client,
        model: str,
        messages,
        ...
    ) -> AsyncGenerator[str, None]:
        async for response in client.chat(
            model=model,
            messages=messages,
            stream=True,
            ...
        ):
            if response.get('message', {}).get('content'):
                yield response['message']['content']
```

---

## 🛠️ Execução Assíncrona de Ferramentas

### ToolExecutor

```python
class ToolExecutor:
    async def execute(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any]
    ) -> ToolExecutionResult:
        self._logger.info("Executing tool: %s", tool.name)

        try:
            # Executa tool (pode ser async ou sync)
            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**arguments)
            else:
                result = tool.execute(**arguments)

            return ToolExecutionResult(success=True, result=result)
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))
```

---

## 🔄 Fluxo Assíncrono Completo

### Sem Ferramentas

```
User: await agent.chat("mensagem")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler.handle_streaming() [async]
              → async for chunk in openai_stream:
                  → yield chunk
          ← AsyncGenerator[str, None]
      ← StreamingResponseDTO
  ← await response (string completa)
```

### Com Ferramentas

```
User: await agent.chat("Que dia é hoje?")
  → ChatWithAgentUseCase.execute() [async]
      → ChatRepository.chat() [async]
          → OpenAIStreamHandler.handle_streaming() [async]
              → async for chunk in openai_stream:
                  → Detecta tool_calls
              → Para cada tool_call:
                  → ToolExecutor.execute(tool, args) [async]
                      ← ToolExecutionResult
              → Segunda chamada API com tool results
              → async for token in second_stream:
                  → yield token
          ← AsyncGenerator[str, None]
      ← StreamingResponseDTO
  ← await response
```

---

## 💡 Padrões de Uso

### Padrão 1: Consumo Simples (Await)

```python
import asyncio

async def simple_chat():
    from createagents import CreateAgent

    agent = CreateAgent(provider="openai", model="gpt-4")
    response = await agent.chat("Olá")  # Aguarda string completa
    print(response)

asyncio.run(simple_chat())
```

### Padrão 2: Streaming Manual (Async For)

```python
import asyncio

async def streaming_chat():
    from createagents import CreateAgent

    agent = CreateAgent(provider="openai", model="gpt-4")
    response = await agent.chat("Conte uma história")

    async for token in response:
        print(token, end='', flush=True)
    print()

asyncio.run(streaming_chat())
```

### Padrão 3: Múltiplas Chamadas Concorrentes

```python
import asyncio

async def concurrent_chats():
    from createagents import CreateAgent

    agent1 = CreateAgent(provider="openai", model="gpt-4")
    agent2 = CreateAgent(provider="openai", model="gpt-4")

    # Executar simultaneamente
    results = await asyncio.gather(
        agent1.chat("Pergunta 1"),
        agent2.chat("Pergunta 2"),
    )

    print(results[0])
    print(results[1])

asyncio.run(concurrent_chats())
```

### Padrão 4: Ferramentas Assíncronas

```python
from createagents import BaseTool
import asyncio
import aiohttp

class AsyncWebTool(BaseTool):
    name = "async_web_fetch"
    description = "Busca dados da web assincronamente"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        },
        "required": ["url"]
    }

    async def execute(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

# Uso
async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=[AsyncWebTool()]
    )

    response = await agent.chat("Busque dados de https://api.example.com")
    print(await response)

asyncio.run(main())
```

---

## 🔧 Implementação de Handlers

### Handler Não-Streaming

```python
class OpenAIHandler:
    async def handle_non_streaming(
        self,
        client,
        model: str,
        messages: List[dict],
        ...
    ) -> str:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            ...
        )
        return response.choices[0].message.content
```

### Handler com Métricas

```python
class OpenAIStreamHandler:
    def __init__(self, ...):
        self._logger = LoggingConfig.get_logger(__name__)
        self._metrics = MetricsRecorder(metrics_list)

    async def handle_streaming(self, ...) -> AsyncGenerator[str, None]:
        start_time = time.time()

        try:
            # Streaming
            async for token in stream:
                yield token

            # Gravar métricas de sucesso
            self._metrics.record_success_metrics(
                model=model,
                start_time=start_time,
                response_api=full_response,
                provider_type='openai'
            )
        except Exception as e:
            # Gravar métricas de erro
            self._metrics.record_error_metrics(
                model=model,
                start_time=start_time,
                error=e
            )
            raise
```

---

## 🐛 Armadilhas Comuns

### 1. Esquecer await

```python
# ❌ ERRADO
response = agent.chat("mensagem")  # Retorna coroutine
print(response)  # <coroutine object...>

# ✅ CORRETO
response = await agent.chat("mensagem")
print(await response)  # String
```

### 2. Bloquear Loop de Eventos

```python
# ❌ ERRADO (blocking I/O)
async def bad_function():
    time.sleep(10)  # Bloqueia todo o loop!

# ✅ CORRETO (non-blocking)
async def good_function():
    await asyncio.sleep(10)  # Permite outras tasks
```

### 3. Não Usar asyncio.run()

```python
# ❌ ERRADO
async def main():
    response = await agent.chat("mensagem")
    print(await response)

main()  # Erro! Coroutine não executada

# ✅ CORRETO
asyncio.run(main())
```

### 4. Consumir Stream Duas Vezes

```python
# ❌ ERRADO
response = await agent.chat("mensagem")
text1 = await response  # Consome stream
text2 = await response  # Já consumido! text2 = ""

# ✅ CORRETO
response = await agent.chat("mensagem")
text = await response  # Consumir apenas uma vez
```

---

## 📊 Performance

### Concorrência vs Sequencial

**Sequencial**:

```python
async def sequential():
    r1 = await agent.chat("Q1")  # 2s
    r2 = await agent.chat("Q2")  # 2s
    r3 = await agent.chat("Q3")  # 2s
    # Total: 6s
```

**Concorrente**:

```python
async def concurrent():
    results = await asyncio.gather(
        agent.chat("Q1"),  # 2s
        agent.chat("Q2"),  # 2s
        agent.chat("Q3"),  # 2s
    )
    # Total: ~2s (paralelizado)
```

---

## 🧪 Testando Código Assíncrono

```python
import pytest

@pytest.mark.asyncio
async def test_chat():
    agent = CreateAgent(provider="openai", model="gpt-4")
    response = await agent.chat("Test message")
    text = await response
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_streaming():
    agent = CreateAgent(provider="openai", model="gpt-4")
    response = await agent.chat("Test")

    tokens = []
    async for token in response:
        tokens.append(token)

    assert len(tokens) > 0
```

---

## 💡 Best Practices

1. **Sempre use await**: Para executar coroutines
2. **Use asyncio.gather**: Para chamadas concorrentes
3. **Não bloqueie**: Use bibliotecas async (aiohttp, aiofiles)
4. **Trate exceções**: try/except em código async
5. **Logging apropriado**: Use logger em funções async
6. **Teste com pytest-asyncio**: Marque tests com `@pytest.mark.asyncio`

---

## 📚 Referências

- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Async Generators](https://peps.python.org/pep-0525/)
- [API de Streaming](../reference/streaming-api.md)

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025

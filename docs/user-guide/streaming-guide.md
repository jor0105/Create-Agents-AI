# Guia de Streaming

Este guia explica como receber respostas do agente em tempo real.

---

## 💡 O que é Streaming?

Streaming permite que você veja a resposta aparecendo **palavra por palavra** em tempo real, como se o agente estivesse digitando. Isso deixa a experiência mais natural e interativa.

**Sem streaming**: Você espera 5 segundos e recebe a resposta completa de uma vez.
**Com streaming**: As palavras aparecem imediatamente, conforme o agente gera a resposta.

---

## 🚀 Como Usar

Existem duas formas de receber respostas do agente:

### 1️⃣ Receber a Resposta Completa (Mais Simples)

Use `await` para esperar a resposta completa:

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(provider="openai", model="gpt-4")

    # Espera a resposta completa
    resposta = await agent.chat("Escreva um poema")
    print(resposta)

asyncio.run(main())
```

### 2️⃣ Ver Palavra por Palavra (Streaming em Tempo Real)

Use `async for` para ver cada palavra aparecer:

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(provider="openai", model="gpt-4")

    resposta = await agent.chat("Conte uma história")

    # Mostra palavra por palavra
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()  # Nova linha no final

asyncio.run(main())
```

> 💡 **Dica**: Use a opção 2 para chatbots ou interfaces onde você quer mostrar o agente "pensando".

---

## 📚 Exemplos Práticos

### Exemplo 1: Chatbot Interativo

Crie um chatbot que mostra as palavras aparecendo:

```python
import asyncio
from createagents import CreateAgent

async def chat_interface():
    agent = CreateAgent(provider="openai", model="gpt-4")

    while True:
        user_input = input("Você: ")
        if user_input.lower() in ['sair', 'exit']:
            break

        print("Agente: ", end='', flush=True)
        resposta = await agent.chat(user_input)

        # Mostra palavra por palavra
        async for palavra in resposta:
            print(palavra, end='', flush=True)
        print("\n")

asyncio.run(chat_interface())
```

### Exemplo 2: Perguntas Simples

Para perguntas diretas, use `await` (mais simples):

```python
import asyncio
from createagents import CreateAgent

async def perguntas_simples():
    agent = CreateAgent(provider="openai", model="gpt-4")

    # Pergunta direta
    resposta = await agent.chat("Qual a capital do Brasil?")
    print(f"Resposta: {resposta}")

asyncio.run(perguntas_simples())
```

---

## ⚙️ Ativando e Desativando Streaming

### Ativar Streaming (Padrão)

Por padrão, o streaming já vem ativado. Você não precisa fazer nada!

```python
import asyncio
from createagents import CreateAgent

async def main():
    # Streaming já está ativo
    agent = CreateAgent(provider="openai", model="gpt-4")

    resposta = await agent.chat("Conte uma história")
    async for palavra in resposta:
        print(palavra, end='', flush=True)

asyncio.run(main())
```

### Desativar Streaming

Se preferir esperar a resposta completa, desative o streaming:

```python
import asyncio

async def main():
    # Desabilita streaming
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        config={"stream": False}
    )

    # Recebe tudo de uma vez
    resposta = await agent.chat("Olá")
    print(resposta)

asyncio.run(main())
```

---

### Usar com Ollama (Modelos Locais)

```python
import asyncio

async def ollama_streaming():
    agent = CreateAgent(provider="ollama", model="llama3.2")

    resposta = await agent.chat("Explique machine learning")
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()

asyncio.run(ollama_streaming())
```

**Funciona igual!** Não importa se usa OpenAI ou Ollama, o streaming funciona da mesma forma.

---

## 🛠️ Usando Ferramentas

O streaming funciona normalmente mesmo quando o agente usa ferramentas:

```python
import asyncio

async def exemplo_com_ferramentas():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["currentdate"]
    )

    print("Perguntando sobre datas...\n")
    resposta = await agent.chat("Que dia é hoje?")

    # O agente usa a ferramenta e responde em streaming
    async for palavra in resposta:
        print(palavra, end='', flush=True)
    print()

asyncio.run(exemplo_com_ferramentas())
```

---

## 📊 Streaming e Métricas

Métricas são coletadas automaticamente, independentemente do modo de consumo:

```python
import asyncio

async def streaming_with_metrics():
    from createagents import CreateAgent

    agent = CreateAgent(provider="openai", model="gpt-4")

    # Streaming
    response = await agent.chat("Conte uma piada")
    async for token in response:
        print(token, end='')
    print("\n")

    # Métricas ainda são gravadas
    metrics = agent.get_metrics()
    print(f"\nLatência: {metrics[-1].latency_ms}ms")
    print(f"Tokens: {metrics[-1].tokens_used}")

asyncio.run(streaming_with_metrics())
```

---

## � Dicas

### 1. Para Perguntas Rápidas

Use `await` para receber a resposta completa:

```python
resposta = await agent.chat("Qual a capital da França?")
print(resposta)
```

### 2. Para Chatbots e Interfaces

Use `async for` para mostrar palavra por palavra:

```python
resposta = await agent.chat("Escreva um artigo")
async for palavra in resposta:
    print(palavra, end='', flush=True)
```

### 3. Lembre-se do `await`

Sempre use `await` ao chamar `agent.chat()`:

```python
# ❌ Errado
resposta = agent.chat("mensagem")  # Não funciona!

# ✅ Correto
resposta = await agent.chat("mensagem")  # Funciona!
```

### 4. Use `asyncio.run()`

Sempre envolva seu código em uma função `async` e execute com `asyncio.run()`:

```python
import asyncio

async def main():
    resposta = await agent.chat("mensagem")
    print(resposta)

asyncio.run(main())
```

---

## 📚 Próximos Passos

- [Uso da CLI](cli-usage.md) - Interface interativa
- [Exemplos Práticos](examples-user.md) - Mais exemplos de uso
- [FAQ](faq-user.md) - Perguntas frequentes

---

**Versão:** 0.1.3 | **Atualização:** 01/12/2025

"""
Testes diversificados entre provedores OpenAI e Ollama.

Este arquivo testa:
1. OpenAI com streaming
2. OpenAI sem streaming
3. Ollama com streaming
4. Ollama sem streaming
5. Ferramentas built-in e customizadas em ambos
"""

import asyncio
import logging
from typing import Optional

from createagents import CreateAgent, tool
from createagents.logging import configure_logging

# Habilitar logging para ver os passos da IA
configure_logging(level=logging.INFO)


# =============================================================================
# Ferramentas Customizadas
# =============================================================================


@tool
def calculator(expression: str) -> str:
    """Calcular uma expressão matemática.

    Args:
        expression: Expressão matemática (ex: "2 + 2", "10 * 5").

    Returns:
        Resultado do cálculo.
    """
    try:
        allowed = set('0123456789+-*/().% ')
        if not all(c in allowed for c in expression):
            return 'Erro: Caracteres não permitidos'
        return f'Resultado: {eval(expression)}'  # nosec B307
    except Exception as e:
        return f'Erro: {e}'


@tool
def weather(city: str) -> str:
    """Consultar previsão do tempo (simulado).

    Args:
        city: Nome da cidade.

    Returns:
        Previsão do tempo para a cidade.
    """
    temps = {'São Paulo': 25, 'Rio': 32, 'Curitiba': 18, 'Brasília': 28}
    temp = temps.get(city, 22)
    return f'🌤️ {city}: {temp}°C, parcialmente nublado'


@tool
async def fetch_data(url: str, timeout: Optional[int] = 30) -> str:
    """Buscar dados de uma URL (assíncrono).

    Args:
        url: URL para buscar dados.
        timeout: Timeout em segundos (padrão: 30).

    Returns:
        Conteúdo da resposta ou erro.
    """
    # Simulação - em produção usaria httpx ou aiohttp
    await asyncio.sleep(0.1)  # Simular latência
    return f'Dados obtidos de {url} (timeout={timeout}s): [Conteúdo simulado]'


# =============================================================================
# Testes OpenAI
# =============================================================================


async def test_openai_stream():
    """Teste OpenAI com streaming habilitado."""
    print('\n' + '=' * 70)
    print('🔵 OPENAI - Stream: True')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        instructions='Você é um assistente técnico conciso.',
        tools=['currentdate', calculator],
        config={'stream': True},
    )

    print('\n📝 Pergunta: Que dia é hoje e quanto é 25 * 4?')
    print('🤖 Resposta: ', end='', flush=True)

    response = await agent.chat('Que dia é hoje e quanto é 25 * 4?')
    async for token in response:
        print(token, end='', flush=True)

    print('\n')
    print(
        f'📊 Métricas: {agent.get_metrics()[-1] if agent.get_metrics() else "N/A"}'
    )


async def test_openai_no_stream():
    """Teste OpenAI sem streaming."""
    print('\n' + '=' * 70)
    print('🔵 OPENAI - Stream: False')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        instructions='Você é um assistente técnico conciso.',
        tools=[calculator, weather],
        config={'stream': False},
    )

    print('\n📝 Pergunta: Quanto é 100 / 4 e qual o tempo em São Paulo?')
    response = await agent.chat(
        'Quanto é 100 / 4 e qual o tempo em São Paulo?'
    )
    print(f'🤖 Resposta: {response}')
    print(
        f'📊 Métricas: {agent.get_metrics()[-1] if agent.get_metrics() else "N/A"}'
    )


# =============================================================================
# Testes Ollama
# =============================================================================


async def test_ollama_stream():
    """Teste Ollama com streaming habilitado."""
    print('\n' + '=' * 70)
    print('🟢 OLLAMA - Stream: True')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        instructions='Você é um assistente técnico conciso.',
        tools=['currentdate', calculator],
        config={'stream': True},
    )

    print('\n📝 Pergunta: Que horas são agora e quanto é 15 + 27?')
    print('🤖 Resposta: ', end='', flush=True)

    response = await agent.chat('Que horas são agora e quanto é 15 + 27?')
    async for token in response:
        print(token, end='', flush=True)

    print('\n')
    print(
        f'📊 Métricas: {agent.get_metrics()[-1] if agent.get_metrics() else "N/A"}'
    )


async def test_ollama_no_stream():
    """Teste Ollama sem streaming."""
    print('\n' + '=' * 70)
    print('🟢 OLLAMA - Stream: False')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        instructions='Você é um assistente técnico conciso.',
        tools=[calculator, weather],
        config={'stream': False},
    )

    print('\n📝 Pergunta: Quanto é 50 * 3 e qual o clima em Curitiba?')
    response = await agent.chat('Quanto é 50 * 3 e qual o clima em Curitiba?')
    print(f'🤖 Resposta: {response}')
    print(
        f'📊 Métricas: {agent.get_metrics()[-1] if agent.get_metrics() else "N/A"}'
    )


# =============================================================================
# Testes Mistos
# =============================================================================


async def test_openai_builtin_only():
    """Teste OpenAI apenas com ferramentas built-in."""
    print('\n' + '=' * 70)
    print('🔵 OPENAI - Apenas Built-in Tools - Stream: True')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        tools=['currentdate', 'readlocalfile'],
        config={'stream': True},
    )

    print('\n📝 Pergunta: Qual é a data de hoje?')
    print('🤖 Resposta: ', end='', flush=True)

    response = await agent.chat('Qual é a data de hoje?')
    async for token in response:
        print(token, end='', flush=True)

    print('\n')


async def test_ollama_custom_only():
    """Teste Ollama apenas com ferramentas customizadas."""
    print('\n' + '=' * 70)
    print('🟢 OLLAMA - Apenas Custom Tools - Stream: False')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather],
        config={'stream': False},
    )

    print('\n📝 Pergunta: Qual a temperatura em Brasília?')
    response = await agent.chat('Qual a temperatura em Brasília?')
    print(f'🤖 Resposta: {response}')


async def test_no_tools():
    """Teste sem ferramentas (apenas conversa)."""
    print('\n' + '=' * 70)
    print('🔵 OPENAI - Sem ferramentas - Stream: False')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        instructions='Responda de forma breve.',
        config={'stream': False},
    )

    print('\n📝 Pergunta: O que é Clean Architecture em uma frase?')
    response = await agent.chat('O que é Clean Architecture em uma frase?')
    print(f'🤖 Resposta: {response}')


async def test_async_tool():
    """Teste com ferramenta assíncrona (async def)."""
    print('\n' + '=' * 70)
    print('⚡ ASYNC TOOL - OpenAI - Stream: True')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        instructions='Você é um assistente que busca dados.',
        tools=[fetch_data],
        config={'stream': True},
    )

    print('\n📝 Pergunta: Busque dados do site example.com')
    print('🤖 Resposta: ', end='', flush=True)

    response = await agent.chat('Busque dados do site example.com')
    async for token in response:
        print(token, end='', flush=True)

    print('\n')


# =============================================================================
# Main
# =============================================================================


async def run_all_tests():
    """Executa todos os testes."""
    print('🚀 CreateAgents - Testes Diversificados de Provedores')
    print('=' * 70)
    print('Provedores: OpenAI (gpt-5-nano) e Ollama (gpt-oss:120b-cloud)')
    print('Modos: Streaming e Não-Streaming')
    print('=' * 70)

    tests = [
        ('OpenAI + Stream', test_openai_stream),
        ('OpenAI sem Stream', test_openai_no_stream),
        ('Ollama + Stream', test_ollama_stream),
        ('Ollama sem Stream', test_ollama_no_stream),
        ('OpenAI Built-in', test_openai_builtin_only),
        ('Ollama Custom', test_ollama_custom_only),
        ('Async Tool', test_async_tool),
        ('Sem ferramentas', test_no_tools),
    ]

    results = []
    for name, test_fn in tests:
        try:
            await test_fn()
            results.append((name, '✅ OK'))
        except Exception as e:
            print(f'\n❌ Erro: {e}')
            results.append((name, f'❌ {type(e).__name__}'))

    # Resumo
    print('\n' + '=' * 70)
    print('📋 RESUMO DOS TESTES')
    print('=' * 70)
    for name, status in results:
        print(f'   {name}: {status}')
    print('=' * 70)


if __name__ == '__main__':
    asyncio.run(run_all_tests())

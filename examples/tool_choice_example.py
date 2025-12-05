"""
Exemplo completo de uso do tool_choice para controle de seleção de ferramentas.

Este arquivo demonstra:
1. Todos os modos de tool_choice (auto, none, required, específico)
2. Formato de string vs formato de dicionário
3. Uso com ToolChoice value object
4. Comportamento em diferentes cenários
"""

import asyncio
import logging

from createagents import CreateAgent, tool, LoggingConfigurator

# Habilitar logging para ver os passos da IA
LoggingConfigurator.configure(level=logging.INFO)


# =============================================================================
# Ferramentas para Demonstração
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
def weather(city: str, detailed: bool = False) -> str:
    """Consultar previsão do tempo.

    Args:
        city: Nome da cidade.
        detailed: Se deve incluir detalhes extras.

    Returns:
        Previsão do tempo para a cidade.
    """
    # Simulação
    temps = {'São Paulo': 25, 'Rio': 32, 'Curitiba': 18}
    temp = temps.get(city, 22)
    base = f'🌤️ {city}: {temp}°C'

    if detailed:
        return f'{base}, Umidade: 65%, Vento: 10km/h'
    return base


@tool
def translate(text: str, to_lang: str = 'en') -> str:
    """Traduzir texto.

    Args:
        text: Texto para traduzir.
        to_lang: Idioma destino (padrão: inglês).

    Returns:
        Texto traduzido.
    """
    # Simulação
    translations = {
        'olá': 'hello',
        'mundo': 'world',
        'bom dia': 'good morning',
    }
    translated = translations.get(text.lower(), f'[{text}]')
    return f"🌍 '{text}' → '{translated}' ({to_lang})"


@tool
def search(query: str, max_results: int = 5) -> str:
    """Buscar informações.

    Args:
        query: Termo de busca.
        max_results: Máximo de resultados.

    Returns:
        Resultados da busca.
    """
    return f"🔍 Resultados para '{query}': [{max_results} itens encontrados]"


# =============================================================================
# Demonstrações de tool_choice
# =============================================================================


async def demo_auto():
    """
    Modo AUTO (padrão): O modelo decide se/qual ferramenta usar.

    Use quando: Quer que o modelo escolha a melhor abordagem.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: auto (padrão) - OPENAI + Stream: False')
    print('   O modelo decide se e qual ferramenta usar')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        tools=[calculator, weather, translate, search],
        config={'stream': False},
    )

    # Cenário 1: Modelo deve usar calculadora
    print('\n🔹 Cenário 1: Pergunta matemática')
    response = await agent.chat('Quanto é 15 vezes 8?')
    print(f'   Resposta: {response}')

    # Cenário 2: Modelo pode responder sem ferramenta
    print('\n🔹 Cenário 2: Pergunta geral (pode não usar ferramenta)')
    response = await agent.chat('Qual é a capital da França?')
    print(f'   Resposta: {response}')


async def demo_none():
    """
    Modo NONE: Modelo não pode usar ferramentas.

    Use quando: Quer apenas conversa, sem ações externas.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: none - OLLAMA + Stream: True')
    print('   Ferramentas desabilitadas - apenas conversa')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather],
        config={'stream': True},
    )

    # Mesmo pedindo cálculo, não usará calculadora (sem tool_choice=none aqui,
    # pois o método chat não aceita tool_choice ainda)
    print('\n🔹 Cenário: Pergunta simples com streaming')
    print('   Resposta: ', end='', flush=True)
    response = await agent.chat('Quanto é 7 mais 3? Responda brevemente.')
    async for token in response:
        print(token, end='', flush=True)
    print()


async def demo_required():
    """
    Modo REQUIRED: Modelo DEVE usar pelo menos uma ferramenta.

    Use quando: Quer garantir que uma ação será executada.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: required - OLLAMA + Stream: False')
    print('   Modelo deve usar alguma ferramenta')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather, search],
        config={'stream': False},
    )

    # Mesmo pergunta vaga, modelo escolherá uma ferramenta
    print('\n🔹 Cenário: Pedido vago - modelo escolhe ferramenta')
    response = await agent.chat(
        'Me diga algo interessante', tool_choice='required'
    )
    print(f'   Resposta: {response}')
    print('   (Note: Usou alguma ferramenta mesmo sem pedido específico)')


async def demo_specific():
    """
    Modo ESPECÍFICO: Força uso de uma ferramenta específica.

    Use quando: Quer garantir que uma ferramenta específica seja usada.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: específico (nome da ferramenta) - OPENAI + Stream: True')
    print('   Força uso de uma ferramenta específica')
    print('=' * 70)

    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        tools=[calculator, weather, translate, search],
        config={'stream': True},
    )

    # Forçar uso de weather mesmo para pergunta genérica
    print("\n🔹 Cenário 1: Forçar 'weather' para qualquer pergunta")
    print('   Resposta: ', end='', flush=True)
    response = await agent.chat(
        'Me fale sobre São Paulo', tool_choice='weather'
    )
    async for token in response:
        print(token, end='', flush=True)
    print()

    # Forçar calculadora
    print("\n🔹 Cenário 2: Forçar 'calculator'")
    print('   Resposta: ', end='', flush=True)
    response = await agent.chat('Qualquer coisa', tool_choice='calculator')
    async for token in response:
        print(token, end='', flush=True)
    print()


async def demo_dict_format():
    """
    Formato de DICIONÁRIO: Compatível com formato OpenAI.

    Use quando: Precisa de compatibilidade com API OpenAI direta.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: Formato de Dicionário - OLLAMA + Stream: True')
    print('   Usa formato compatível com API OpenAI')
    print('=' * 70)

    agent = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather],
        config={'stream': True},
    )

    # Formato de dicionário para ferramenta específica
    print("\n🔹 Cenário: Formato dict para 'calculator'")
    print('   Resposta: ', end='', flush=True)
    response = await agent.chat(
        'Faça algo',
        tool_choice={'type': 'function', 'function': {'name': 'calculator'}},
    )
    async for token in response:
        print(token, end='', flush=True)
    print()


async def demo_with_value_object():
    """
    Usando ToolChoice VALUE OBJECT diretamente.

    Use quando: Quer type-safety e validação.
    """
    print('\n' + '=' * 70)
    print('📌 MODO: ToolChoice Value Object - OpenAI e Ollama alternados')
    print('   Usando o value object para type-safety')
    print('=' * 70)

    from createagents.domain.value_objects import ToolChoice

    # OpenAI + Stream: False
    agent_openai = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        tools=[calculator, weather, search],
        config={'stream': False},
    )

    # Ollama + Stream: True
    agent_ollama = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather, search],
        config={'stream': True},
    )

    # Usando factory methods do ToolChoice
    print('\n🔹 Cenário 1: ToolChoice.auto() - OpenAI')
    response = await agent_openai.chat(
        'Quanto é 5 + 5?', tool_choice=ToolChoice.auto()
    )
    print(f'   Resposta: {response}')

    print('\n🔹 Cenário 2: ToolChoice.required() - Ollama com streaming')
    print('   Resposta: ', end='', flush=True)
    response = await agent_ollama.chat(
        'Olá!', tool_choice=ToolChoice.required()
    )
    async for token in response:
        print(token, end='', flush=True)
    print()

    print("\n🔹 Cenário 3: ToolChoice.specific('weather') - OpenAI")
    response = await agent_openai.chat(
        'Qualquer coisa', tool_choice=ToolChoice.specific('weather')
    )
    print(f'   Resposta: {response}')

    print('\n🔹 Cenário 4: ToolChoice.none() - Ollama com streaming')
    print('   Resposta: ', end='', flush=True)
    response = await agent_ollama.chat(
        'Calcule 2 + 2', tool_choice=ToolChoice.none()
    )
    async for token in response:
        print(token, end='', flush=True)
    print()


async def demo_practical_scenarios():
    """Cenários PRÁTICOS de uso do tool_choice."""
    print('\n' + '=' * 70)
    print('📌 CENÁRIOS PRÁTICOS - Alternando OpenAI/Ollama e stream')
    print('   Quando usar cada modo')
    print('=' * 70)

    # OpenAI com streaming
    agent_openai_stream = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        tools=[calculator, weather, translate, search],
        config={'stream': True},
    )

    # Ollama sem streaming
    agent_ollama = CreateAgent(
        provider='ollama',
        model='gpt-oss:120b-cloud',
        tools=[calculator, weather, translate, search],
        config={'stream': False},
    )

    # Cenário 1: Chatbot com ferramentas opcionais - OpenAI + Stream
    print('\n🔹 1. Chatbot Inteligente (auto) - OpenAI + Stream')
    print("   Use 'auto' para deixar o modelo decidir naturalmente")
    print('   → ', end='', flush=True)
    response = await agent_openai_stream.chat(
        'Qual a previsão do tempo para São Paulo?', tool_choice='auto'
    )
    async for token in response:
        print(token, end='', flush=True)
    print()

    # Cenário 2: Executor de tarefas - Ollama sem stream
    print('\n🔹 2. Executor de Tarefas (required) - Ollama')
    print("   Use 'required' quando o usuário espera uma ação")
    response = await agent_ollama.chat(
        'Execute uma tarefa útil para mim', tool_choice='required'
    )
    print(f'   → {response}')

    # Cenário 3: Assistente de cálculos - OpenAI + Stream
    print('\n🔹 3. Assistente de Cálculos (específico) - OpenAI + Stream')
    print('   Use específico para garantir consistência')
    print('   → ', end='', flush=True)
    response = await agent_openai_stream.chat(
        'Preciso calcular meu orçamento: 1500 + 800 - 300',
        tool_choice='calculator',
    )
    async for token in response:
        print(token, end='', flush=True)
    print()

    # Cenário 4: Modo conversa - Ollama sem stream
    print('\n🔹 4. Modo Conversa (none) - Ollama')
    print("   Use 'none' para conversas sem ações")
    response = await agent_ollama.chat(
        'Me explique o que você pode fazer', tool_choice='none'
    )
    print(f'   → {response}')


# =============================================================================
# Tabela de Referência
# =============================================================================


def print_reference_table():
    """Imprime tabela de referência dos modos."""
    print('\n' + '=' * 70)
    print('📖 TABELA DE REFERÊNCIA - tool_choice')
    print('=' * 70)
    print("""
┌─────────────────┬─────────────────────────────────────────────────────────┐
│ Modo            │ Descrição                                               │
├─────────────────┼─────────────────────────────────────────────────────────┤
│ "auto"          │ Modelo decide se/qual ferramenta usar (PADRÃO)          │
│ "none"          │ Ferramentas desabilitadas, apenas conversa              │
│ "required"      │ Modelo DEVE usar pelo menos uma ferramenta              │
│ "<nome>"        │ Força uso da ferramenta com esse nome                   │
│ {dict}          │ Formato OpenAI: {"type": "function", "function": {...}} │
│ ToolChoice.*()  │ Value object com factory methods (auto/none/required)   │
└─────────────────┴─────────────────────────────────────────────────────────┘

📝 Quando usar cada modo:

• AUTO: Comportamento padrão, ideal para chatbots inteligentes
• NONE: Modo conversa pura, útil para explicações ou smalltalk
• REQUIRED: Quando você PRECISA de uma ação, não apenas texto
• ESPECÍFICO: Garante consistência, ex: sempre usar calculadora para math

⚠️ Dicas:
1. 'required' pode gerar chamadas desnecessárias - use com cuidado
2. Modo específico ignora contexto - modelo não escolhe ferramenta
3. Use ToolChoice value object para type-safety em código Python
4. Formato dict é útil para interoperabilidade com outras APIs
    """)


# =============================================================================
# Main
# =============================================================================


async def main():
    """Executar todas as demonstrações."""
    print('🚀 CreateAgents - Demonstração Completa de tool_choice')
    print('=' * 70)

    # Referência
    print_reference_table()

    # Demonstrações
    await demo_auto()
    await demo_none()
    await demo_required()
    await demo_specific()
    await demo_dict_format()
    await demo_with_value_object()
    await demo_practical_scenarios()

    print('\n' + '=' * 70)
    print('✅ Demonstração concluída!')
    print('=' * 70)


if __name__ == '__main__':
    # Mostrar apenas referência (não precisa de API key)
    print_reference_table()

    print('\n💡 Executando demos com agente...')
    asyncio.run(main())

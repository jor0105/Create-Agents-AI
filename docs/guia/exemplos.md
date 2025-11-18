# 💡 Exemplos Práticos

Casos de uso reais do **AI Agent Creator** para inspirar suas aplicações.

---

## 🎓 Assistente Educacional

```python
from createagents import CreateAgent

professor = CreateAgent(
    provider="openai",
    model="gpt-5-nano",
    name="Professor Virtual",
    instructions="""
    Você é um professor paciente e didático.
    Explique conceitos de forma clara com exemplos práticos.
    Adapte a linguagem ao nível do aluno.
    Use analogias quando apropriado.
    """
)

# Explicar conceitos
response = professor.chat("Explique como funciona recursão em programação")
print(response)

# Ensinar com exemplos
response = professor.chat("Me dê um exemplo prático em Python")
print(response)
```

---

## 💼 Assistente Corporativo

```python
assistente_corporativo = CreateAgent(
    provider="openai",
    model="gpt-5",
    name="Assistente Executivo",
    instructions="""
    Você é um assistente executivo profissional.
    Use linguagem formal e corporativa.
    Seja objetivo, claro e direto.
    Forneça informações estruturadas.
    """,
    tools=["currentdate"]  # Acesso à data/hora
)

# Agendar reunião
response = assistente_corporativo.chat("Que dia é hoje? Preciso agendar uma reunião")
print(response)

# Redigir email
response = assistente_corporativo.chat("Redija um email formal agradecendo participação em reunião")
print(response)
```

---

## 👨‍💻 Code Assistant (Assistente de Programação)

```python
code_expert = CreateAgent(
    provider="openai",
    model="gpt-4.1-mini",
    name="Python Expert",
    instructions="""
    Você é um especialista em Python e boas práticas.
    Forneça código limpo seguindo PEP 8.
    Inclua type hints e docstrings.
    Explique suas decisões de design.
    Sugira melhorias quando apropriado.
    """,
    config={"temperature": 0.3}  # Menos criativo, mais preciso
)

# Pedir implementação
codigo = code_expert.chat("""
Crie uma função que valida CPF brasileiro.
Inclua validação de formato e dígitos verificadores.
""")
print(codigo)

# Code review
code_review = code_expert.chat("""
Revise este código:
def calc(a,b):
    return a+b
""")
print(code_review)
```

---

## 🌐 Tradutor Profissional

```python
tradutor = CreateAgent(
    provider="openai",
    model="gpt-4o",
    name="Tradutor Especializado",
    instructions="""
    Você é um tradutor profissional.
    Preserve o tom, contexto e nuances.
    Adapte expressões idiomáticas.
    Mantenha formatação quando relevante.
    """
)

# Tradução técnica
response = tradutor.chat("""
Traduza para inglês (técnico):
'A arquitetura clean separa as regras de negócio da infraestrutura.'
""")
print(response)

# Tradução criativa
response = tradutor.chat("""
Traduza para português (mantendo o tom informal):
'Hey buddy! What's up? Long time no see!'
""")
print(response)
```

---

## 📊 Analista de Dados

```python
analista = CreateAgent(
    provider="ollama",
    model="granite4:latest",    # Seu modelo ollama instalado
    name="Data Analyst",
    instructions="""
    Você é um analista de dados experiente.
    Forneça insights acionáveis e objetivos.
    Explique tendências e padrões.
    Sugira próximos passos quando relevante.
    Use visualizações quando apropriado (descreva-as).
    """
)

# Analisar dados
dados = """
Vendas Q1: Jan=100k, Fev=150k, Mar=120k
Vendas Q2: Abr=180k, Mai=200k, Jun=190k
"""

response = analista.chat(f"Analise estes dados e forneça insights:\n{dados}")
print(response)

# Sugerir ações
response = analista.chat("Que ações você recomenda baseado nessa análise?")
print(response)
```

---

## 🤖 Chatbot Interativo Completo

```python
chatbot = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Chatbot Amigável",
    instructions="""
    Você é um assistente amigável e prestativo.
    Use emojis quando apropriado 😊
    Seja empático e atencioso.
    Faça perguntas de follow-up quando necessário.
    """,
    history_max_size=20  # Mantém mais contexto
)

print("=" * 50)
print("🤖 Chatbot Iniciado!")
print("Digite 'sair' para encerrar, 'limpar' para limpar histórico")
print("=" * 50 + "\n")

while True:
    user_input = input("Você: ")

    if user_input.lower() in ['sair', 'exit', 'quit']:
        print("\n👋 Obrigado por conversar! Até logo!")
        break

    if user_input.lower() == 'limpar':
        chatbot.clear_history()
        print("🧹 Histórico limpo! Vamos começar uma nova conversa.\n")
        continue

    try:
        response = chatbot.chat(user_input)
        print(f"🤖 Bot: {response}\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")

# Exibir estatísticas
config = chatbot.get_configs()
print(f"\n📊 Estatísticas:")
print(f"  - Mensagens trocadas: {len(config['history'])}")
print(f"  - Modelo usado: {config['model']}")
```

---

## 🌍 Agente com Ferramentas Múltiplas

```python
from createagents import BaseTool

# Criar ferramenta customizada
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Busca informações na internet"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta de busca a ser realizada"
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> str:
        # Implementação da busca
        return f"Resultados para: {query}"

# Requer: poetry install -E file-tools
agente_completo = CreateAgent(
    provider="openai",
    model="gpt-5",
    name="Assistente Completo",
    instructions="""
    Você é um assistente com múltiplas capacidades.
    Use as ferramentas disponíveis quando necessário.
    Seja proativo em sugerir o uso de ferramentas.
    """,
    tools=["currentdate", "readlocalfile", WebSearchTool()]
)

# Verificar todas as ferramentas disponíveis
print("🛠️  Ferramentas disponíveis neste agente:")
all_tools = agente_completo.get_all_available_tools()
for name, description in all_tools.items():
    print(f"  • {name}: {description[:50]}...")

# Saída:
# • currentdate: Get the current date and/or time...
# • readlocalfile: Use this tool to read local files...
# • web_search: Busca informações na internet

# Verificar apenas ferramentas do sistema
print("\n📦 Ferramentas do sistema:")
system_tools = agente_completo.get_system_available_tools()
for name in system_tools.keys():
    print(f"  • {name}")

# Saída:
# • currentdate
# • readlocalfile

# Usar ferramentas
response = agente_completo.chat("Que dia da semana é hoje?")
print(response)  # Usa currentdate

response = agente_completo.chat("Leia o arquivo relatorio.pdf e resuma")
print(response)  # Usa readlocalfile

response = agente_completo.chat("Busque as últimas notícias sobre IA")
print(response)  # Usa web_search
```

---

## 🏢 Sistema Multi-Agente (Especialistas)

```python
# Criar múltiplos agentes especializados
agentes = {
    "python": CreateAgent(
        provider="openai",
        model="gpt-4",
        name="Python Expert",
        instructions="Especialista em Python. Forneça código limpo e eficiente."
    ),
    "sql": CreateAgent(
        provider="openai",
        model="gpt-4",
        name="SQL Expert",
        instructions="Especialista em SQL. Otimize queries e explique planos de execução."
    ),
    "devops": CreateAgent(
        provider="openai",
        model="gpt-4",
        name="DevOps Expert",
        instructions="Especialista em DevOps. Foque em CI/CD, Docker, Kubernetes."
    ),
}

def consultar_especialista(area, pergunta):
    """Roteia pergunta para o especialista correto"""
    if area in agentes:
        return agentes[area].chat(pergunta)
    return "❌ Especialista não encontrado"

# Usar especialistas
resposta_python = consultar_especialista("python", "Como criar decorators?")
resposta_sql = consultar_especialista("sql", "Otimize: SELECT * FROM users WHERE active=1")
resposta_devops = consultar_especialista("devops", "Como fazer deploy com Docker?")

print(f"Python Expert: {resposta_python}\n")
print(f"SQL Expert: {resposta_sql}\n")
print(f"DevOps Expert: {resposta_devops}\n")
```

---

## 🎮 Agente Local com Ollama (Privacidade Total)

```python
# Requer Ollama instalado e rodando
agente_local = CreateAgent(
    provider="ollama",
    model="llama2",  # ou mistral, codellama, etc
    name="Assistente Privado",
    instructions="Você é um assistente que roda 100% localmente",
)

# Tudo roda na sua máquina - zero envio de dados externos
response = agente_local.chat("Explique machine learning em termos simples")
print(response)

# Ideal para dados sensíveis
dados_confidenciais = "Informações internas da empresa..."
response = agente_local.chat(f"Analise: {dados_confidenciais}")
# Dados nunca saem da sua máquina!
```

---

## 📈 Monitoramento com Métricas

```python
agente_monitored = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Agente Monitorado",
    tools=["currentdate"]
)

# Ver ferramentas disponíveis antes de começar
print("Ferramentas disponíveis:")
tools = agente_monitored.get_all_available_tools()
print(f"  Total: {len(tools)} ferramentas")
for name in tools.keys():
    print(f"  • {name}")

# Fazer várias chamadas
for i in range(5):
    agente_monitored.chat(f"Mensagem de teste {i+1}")

# Analisar performance
metrics = agente_monitored.get_metrics()

print("\n📊 Análise de Performance:")
total_time = sum(m.response_time for m in metrics)
avg_time = total_time / len(metrics)
total_tokens = sum(m.tokens_used for m in metrics)

print(f"  - Total de chamadas: {len(metrics)}")
print(f"  - Tempo total: {total_time:.2f}s")
print(f"  - Tempo médio: {avg_time:.2f}s")
print(f"  - Total de tokens: {total_tokens}")

# Exportar para análise posterior
agente_monitored.export_metrics_json("performance_report.json")
agente_monitored.export_metrics_prometheus("metrics.prom")

print("\n✅ Métricas exportadas!")
```

---

## 💡 Dicas Avançadas

### Gerenciar Contexto Dinamicamente

```python
agente = CreateAgent(provider="openai", model="gpt-4", name="Smart")

# Conversa longa
for i in range(20):
    agente.chat(f"Mensagem {i}")

# Limpar histórico quando mudar de assunto
agente.clear_history()
agente.chat("Novo assunto completamente diferente")
```

### Otimizar Custos

```python
# Usar modelo mais barato para tarefas simples
agente_economico = CreateAgent(
    provider="openai",
    model="gpt-5-nano",  # Mais barato que GPT-5
    name="Economico",
    history_max_size=5  # Menos contexto = menos tokens
)

# Usar GPT-4 apenas quando necessário
agente_premium = CreateAgent(
    provider="openai",
    model="gpt-5",
    name="Premium"
)

# Rotear baseado em complexidade
def rotear_agente(pergunta):
    if len(pergunta) < 300:  # Pergunta simples
        return agente_economico.chat(pergunta)
    else:  # Pergunta complexa
        return agente_premium.chat(pergunta)
```

---

## 🎯 Próximos Passos

Explore mais recursos:

1. [Ferramentas (Tools)](../tools.md) - Adicione mais capacidades
2. [API Reference](../api.md) - Documentação completa
3. [Arquitetura](../arquitetura.md) - Entenda o design

---

**Versão:** 0.1.0 | **Atualização:** 17/11/2025

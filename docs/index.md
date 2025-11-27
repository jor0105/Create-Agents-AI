# 🤖 Create Agents AI

> Framework Python enterprise para criar agentes de IA inteligentes com arquitetura limpa, múltiplos provedores e ferramentas extensíveis.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-brightgreen.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 🎯 O que este sistema oferece?

**Create Agents AI** é um framework Python que permite criar agentes conversacionais inteligentes de forma profissional:

✅ **Múltiplos provedores**: OpenAI e Ollama (local) com fácil integração
✅ **Ferramentas extensíveis**: CurrentDateTool e ReadLocalFileTool (PDF, Excel, CSV e Parquet)
✅ **Histórico automático**: Conversas contextualizadas sem esforço
✅ **Métricas integradas**: Monitore performance em JSON ou Prometheus
✅ **Arquitetura limpa**: Código testável, manutenível e escalável seguindo SOLID

---

## 🚀 Quick Start

### Instalação

```bash
# Instalação básica via PyPI
pip install createagents

# OU com suporte a leitura de arquivos (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

### Configuração

```bash
# Configure sua chave de API da OpenAI
export OPENAI_API_KEY="sk-proj-sua-chave"

# Ou crie um arquivo .env no seu projeto
echo "OPENAI_API_KEY=sk-proj-sua-chave" > .env
```

### Primeiro Agente em 3 Linhas

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você é um assistente útil"
)

response = agent.chat("Olá!")
print(response)
```

---

## ✨ Funcionalidades Principais

### 🤝 Múltiplos Provedores

```python
# OpenAI (GPT-4, GPT-3.5-turbo, GPT-4o)
agent_openai = CreateAgent(provider="openai", model="gpt-4")

# Ollama (llama2, mistral, codellama - 100% local e privado)
agent_local = CreateAgent(provider="ollama", model="llama2")
```

### 🔧 Ferramentas Integradas

Adicione capacidades aos seus agentes com ferramentas prontas:

```python
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", "readlocalfile"]  # Ferramentas disponíveis
)

# O agente usa automaticamente as ferramentas quando necessário
agent.chat("Que dia é hoje?")  # Usa CurrentDateTool
agent.chat("Leia o arquivo report.pdf")  # Usa ReadLocalFileTool

# Verificar ferramentas disponíveis
all_tools = agent.get_all_available_tools()
print(f"Total de ferramentas: {len(all_tools)}")

# Ver apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()
for name in system_tools.keys():
    print(f"  • {name}")
```

**Ferramentas Disponíveis:**

- `currentdate` - Data/hora em qualquer timezone (sempre disponível)
- `readlocalfile` - Lê PDF, Excel, CSV, Parquet, JSON, YAML, TXT (requer
  `pip install createagents[file-tools]`)

**Criar ferramentas customizadas:**

```python
from createagents import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs mathematical calculations"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate",
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

# Ver todas (sistema + customizadas)
print(agent.get_all_available_tools().keys())
# Saída: dict_keys(['currentdate', 'readlocalfile', 'my_tool'])
```

### 💬 Histórico Contextual

```python
agent.chat("Olá!")
agent.chat("Qual é a capital do Brasil?") # Mantém contexto
agent.chat("E a população?")              # Usa contexto anterior

# Ver histórico
config = agent.get_configs()
print(f"Histórico: {len(config['history'])} mensagens")

# Limpar quando necessário
agent.clear_history()
```

### 📊 Métricas e Monitoramento

```python
# Coletar métricas
metrics = agent.get_metrics()

# Exportar em diferentes formatos
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

### ⚙️ Configurações Personalizadas

```python
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Seja conciso e técnico",
    config={
        "temperature": 0.7,      # Criatividade (0-1)
        "max_tokens": 2000,      # Limite de resposta
    },
    history_max_size=20         # Tamanho do histórico
)
```

---

## 📚 Documentação

### Para Usuários

- **[Instalação](user-guide/installation-user.md)** - Configure seu ambiente passo a passo
- **[Uso Básico](user-guide/basic-usage-user.md)** - Aprenda os fundamentos
- **[Exemplos Práticos](user-guide/examples-user.md)** - Casos de uso reais
- **[FAQ](user-guide/faq-user.md)** - Perguntas frequentes

### Para Desenvolvedores

- **[Arquitetura](dev-guide/architecture-developer.md)** - Clean Architecture e padrões de design
- **[Exemplos Técnicos](dev-guide/technical-examples.md)** - Exemplos avançados
- **[Como Contribuir](dev-guide/contribute.md)** - Guia de contribuição

### Referência

- **[API Reference](reference/api.md)** - Documentação completa da API
- **[Ferramentas](reference/tools.md)** - Guia completo das tools disponíveis
- **[Comandos](reference/commands.md)** - Referência de comandos

---

## 🏗️ Por Que Usar Este Framework?

### Para Empresas

- ✅ **Privacidade**: Opção de modelos 100% locais com Ollama
- ✅ **Segurança**: Sanitização automática de dados sensíveis nos logs
- ✅ **Monitoramento**: Métricas em tempo real para produção
- ✅ **Escalabilidade**: Arquitetura preparada para crescimento

### Para Desenvolvedores

- ✅ **Clean Architecture**: Código limpo, testável e manutenível
- ✅ **SOLID**: Fácil de estender com novos provedores e ferramentas
- ✅ **Type hints**: Suporte completo para IDEs
- ✅ **CI/CD**: Quality checks automáticos com GitHub Actions

---

## 📊 Arquitetura

O projeto segue **Clean Architecture** e **SOLID principles**:

```
┌─────────────────────────────────────┐
│        application                 │  ← CreateAgent (interface simples)
│     (Controllers/UI)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  ← Use Cases & DTOs
│    (Business Logic)                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  ← Entities & Rules
│    (Core Business)                  │
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  ← Adapters (OpenAI, Ollama)
│  (External Services)                │
└─────────────────────────────────────┘
```

**Benefícios**: Testável, Flexível, Escalável e Manutenível

[Saiba mais sobre a arquitetura →](dev-guide/architecture-developer.md)

---

## 🤝 Contribuindo

Quer adicionar um novo provedor ou criar uma ferramenta?

1. Fork o repositório
1. Crie uma branch: `git checkout -b feature/nova-feature`
1. Implemente seguindo os padrões existentes
1. Teste: `poetry run pytest --cov=src`
1. Envie um Pull Request

[Guia completo de contribuição →](dev-guide/contribute.md)

---

## 📞 Suporte

- 📧 **Email**: estraliotojordan@gmail.com
- 🐛 **Bugs**: [GitHub Issues](https://github.com/jor0105/Create-Agents-AI/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/jor0105/Create-Agents-AI/discussions)

---

## 📄 Licença

MIT - Use livremente em seus projetos.

---

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jor0105](https://github.com/jor0105)
- Email: estraliotojordan@gmail.com

---

**Versão:** 0.1.2\
**Última atualização:** 25/11/2025\
**Status:** 🚀 Projeto publicado! Aberto para contribuições e sugestões.

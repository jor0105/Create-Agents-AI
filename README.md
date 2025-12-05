# 🤖 Create Agents AI

<div align="center">

**Framework Python enterprise para criar agentes de IA inteligentes com arquitetura limpa, múltiplos provedores e ferramentas extensíveis.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/createagents.svg)](https://pypi.org/project/createagents/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)

[Documentação](https://jor0105.github.io/Create-Agents-AI/) • [Exemplos](#-exemplos-de-uso) • [API Reference](https://jor0105.github.io/Create-Agents-AI/reference/api/) • [Contribuir](#-contribuindo)

</div>

---

## 🎯 Sobre

**Create Agents AI** é um framework Python modular e extensível para construção de agentes conversacionais inteligentes, seguindo os princípios de **Clean Architecture** e **SOLID**. Projetado para ambientes enterprise, oferece suporte a múltiplos provedores de IA (OpenAI, Ollama), ferramentas extensíveis e métricas integradas.

### Por que usar?

- ✅ **Arquitetura Limpa**: Código testável, manutenível e escalável
- ✅ **Múltiplos Provedores**: OpenAI e Ollama (local/privado)
- ✅ **Ferramentas Extensíveis**: Sistema de tools com suporte a customização
- ✅ **Histórico Contextual**: Gerenciamento automático de conversas
- ✅ **Métricas Integradas**: Monitoramento em JSON e Prometheus
- ✅ **Type Safety**: Suporte completo a type hints
- ✅ **CI/CD Profissional**: Quality checks automáticos com GitHub Actions

---

## ✨ Features

### 🤖 Provedores de IA

| Provedor   | Status     |
| ---------- | ---------- |
| **OpenAI** | ✅ Estável |
| **Ollama** | ✅ Estável |

### 🔧 Ferramentas Built-in

| Ferramenta            | Descrição                                    | Instalação                     |
| --------------------- | -------------------------------------------- | ------------------------------ |
| **CurrentDateTool**   | Data/hora em qualquer timezone               | Padrão                         |
| **ReadLocalFileTool** | Lê PDF, Excel, CSV, Parquet, JSON, YAML, TXT | `poetry install -E file-tools` |

### 📊 Recursos Avançados

- **Histórico Automático**: Gerenciamento de contexto conversacional
- **Métricas de Performance**: Exportação em JSON e Prometheus
- **Sanitização de Logs**: Proteção automática de dados sensíveis
- **Logging Configurável**: Silencioso por padrão, ativável para debug
- **Ferramentas Customizadas**: Interface `BaseTool` para extensões
- **Configuração Flexível**: Temperature, max_tokens, top_p, think mode e mais.

### 📝 Logging

A biblioteca é **silenciosa por padrão** (não emite logs). Para ver logs durante o desenvolvimento:

```python
import logging
from createagents import LoggingConfig

# Ativar logs para debug
LoggingConfig.configure_for_development(level=logging.INFO)
```

📖 [Guia completo de Logging](docs/dev-guide/logging_guide.md)

---

## 🚀 Instalação Rápida

### Pré-requisitos

- Python 3.12 ou superior
- pip (geralmente incluído com Python)

### Instalação via PyPI (Usuários)

```bash
# Instalação básica
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

### Instalação para Desenvolvimento (Contribuidores)

Se você deseja contribuir com o projeto:

```bash
# Clone o repositório
git clone https://github.com/jor0105/Create-Agents-AI.git
cd Create-Agents-AI

# Instale com Poetry
poetry install

# OU com suporte a file-tools
poetry install -E file-tools

# Configure o ambiente
cp .env.example .env
# Edite .env e adicione: OPENAI_API_KEY=sk-proj-sua-chave
```

📖 [Guia completo para contribuidores →](https://jor0105.github.io/Create-Agents-AI/dev-guide/contribute/)

---

## 💡 Quick Start

### Exemplo Básico

```python
import asyncio
from createagents import CreateAgent

async def main():
    # Criar agente
    agent = CreateAgent(
        provider="openai",
        model="gpt-5-nano",
        instructions="Você é um assistente técnico especializado em Python"
    )

    # Conversar
    response = await agent.chat("Como criar uma função recursiva?")
    print(response)

asyncio.run(main())
```

### Com Ferramentas

```python
import asyncio
from createagents import CreateAgent

async def main():
    # Agente com ferramentas
    agent = CreateAgent(
        provider="openai",
        model="gpt-5-nano",
        tools=["currentdate"]
    )

    # O agente usa ferramentas automaticamente
    response = await agent.chat("Que dia é hoje?")  # Usa CurrentDateTool
    print(response)

asyncio.run(main())
```

### Ollama (Local)

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama3.2:latest
ollama serve
```

### Agente Local com Ollama

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="ollama",
        model="llama3.2",
        instructions="Você é um assistente local"
    )

    response = await agent.chat("Explique Clean Architecture")
    print(response)

asyncio.run(main())
```

---

## 📋 Exemplos de Uso

### Exemplo 1: Assistente de Programação

```python
import asyncio
from createagents import CreateAgent

async def main():
    assistant = CreateAgent(
        provider="openai",
        model="gpt-5-nano",
        name="Code Assistant",
        instructions="Você é um especialista em programação Python. Sempre forneça exemplos de código.",
        config={"temperature": 0.3}  # Menos criatividade para código
    )

    # Conversar
    resposta = await assistant.chat("Como ordenar uma lista de dicionários por chave?")
    print(resposta)

    # Ver histórico
    config = assistant.get_configs()
    print(f"Histórico: {len(config['history'])} mensagens")

    # Limpar e começar novo diálogo
    assistant.clear_history()

asyncio.run(main())
```

### Exemplo 2: Múltiplos Agentes

```python
import asyncio
from createagents import CreateAgent

async def main():
    # Um para análise
    analyzer = CreateAgent(
        provider="openai",
        model="gpt-5-nano",
        instructions="Você analisa código e fornece feedback crítico",
        config={"temperature": 0.5}
    )

    # Outro para documentação
    documentor = CreateAgent(
        provider="openai",
        model="gpt-5-nano",
        instructions="Você escreve documentação clara e profissional",
        config={"temperature": 0.3}
    )

    # Usar ambos
    code = "def sum(a,b): return a+b"

    analise = await analyzer.chat(f"Analise este código: {code}")
    print("Análise:", analise)

    docs = await documentor.chat(f"Documente esta função: {code}")
    print("\nDocumentação:", docs)

asyncio.run(main())
```

### Exemplo 3: Ferramenta Customizada

```python
from createagents import CreateAgent, BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Realiza cálculos matemáticos"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Expressão matemática"}
        },
        "required": ["expression"]
    }

    def execute(self, expression: str) -> str:
        return str(eval(expression))

# Criar agente com ferramenta customizada
agent = CreateAgent(
    provider="openai",
    model="gpt-5-nano",
    tools=["currentdate", CalculatorTool()]
)

# Ver todas as ferramentas
all_tools = agent.get_all_available_tools()
print(f"Total de ferramentas: {len(all_tools)}")
for name, description in all_tools.items():
    print(f"  • {name}: {description[:50]}...")
```

### Exemplo 4: Métricas e Performance

```python
# Ver métricas de chamadas
metrics = agent.get_metrics()

# Exportar como JSON
json_data = agent.export_metrics_json()

# Exportar formato Prometheus
prom_data = agent.export_metrics_prometheus()

# Salvar em arquivo
agent.export_metrics_json("metrics.json")
agent.export_metrics_prometheus("metrics.prom")
```

---

## 🏗️ Arquitetura

Este projeto segue **Clean Architecture** e **SOLID Principles**:

```
src/
└─ createagents/                # Pacote principal
    ├─ domain/                 # Regras de negócio (entidades, services, value_objects, exceptions)
    ├─ application/            # Casos de uso e DTOs (lógica da aplicação)
    ├─ infra/                  # Implementações externas (adapters, factories, config)
    ├─ main/                   # Composição e injeção de dependências (composers)
    └─ utils/                  # Utilitários (text_sanitizer, helpers)
```

### Diagrama de Camadas

```
┌─────────────────────────────────────┐
│        PRESENTATION                 │  ← CreateAgent (interface simples)
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

📖 [Documentação completa da arquitetura](https://jor0105.github.io/Create-Agents-AI/dev-guide/architecture-developer/)

---

## 📚 Documentação

### Guia do Usuário

- 📖 [Instalação](https://jor0105.github.io/Create-Agents-AI/user-guide/installation-user/)
- 🚀 [Uso Básico](https://jor0105.github.io/Create-Agents-AI/user-guide/basic-usage-user/)
- 💡 [Exemplos Práticos](https://jor0105.github.io/Create-Agents-AI/user-guide/examples-user/)
- ❓ [FAQ](https://jor0105.github.io/Create-Agents-AI/user-guide/faq-user/)

### Guia do Desenvolvedor

- 🏗️ [Arquitetura](https://jor0105.github.io/Create-Agents-AI/dev-guide/architecture-developer/)
- 🔧 [Exemplos Técnicos](https://jor0105.github.io/Create-Agents-AI/dev-guide/technical-examples/)
- 🤝 [Como Contribuir](https://jor0105.github.io/Create-Agents-AI/dev-guide/contribute/)

### Referência

- 📚 [API Reference](https://jor0105.github.io/Create-Agents-AI/reference/api/)
- 🛠️ [Ferramentas](https://jor0105.github.io/Create-Agents-AI/reference/tools/)
- ⌨️ [Comandos](https://jor0105.github.io/Create-Agents-AI/reference/commands/)

### Build Local da Documentação

```bash
poetry run mkdocs serve
# Acesse: http://localhost:8000
```

---

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-xxx...
```

### Configuração do Modelo

```python
config = {
    "temperature": 0.7,     # Criatividade (0-1)
    "max_tokens": 1000,     # Limite de resposta
    "top_p": 0.9,           # Nucleus sampling
    "think": True,          # Ollama: bool / OpenAI: "low"|"medium"|"high"
}

agent = CreateAgent(
    provider="openai",
    model="gpt-5-nano",
    name="Assistente",
    instructions="Seja conciso",
    config=config,
    history_max_size=20
)
```

---

## 📊 API Reference

### CreateAgent

```python
CreateAgent(
    provider: str,              # "openai" ou "ollama" (obrigatório)
    model: str,                 # Nome do modelo (obrigatório)
    name: str = None,           # Nome do agente (opcional)
    instructions: str = None,   # Instruções do sistema (opcional)
    config: dict = None,        # Configuração do modelo (opcional)
    tools: list = None,         # Lista de ferramentas (opcional)
    history_max_size: int = 10  # Tamanho máximo do histórico
)
```

#### Métodos Principais

| Método                                 | Retorno | Descrição                                            |
| -------------------------------------- | ------- | ---------------------------------------------------- |
| `chat(message)`                        | `str`   | Enviar mensagem e receber resposta                   |
| `get_configs()`                        | `dict`  | Obter configurações e histórico                      |
| `clear_history()`                      | `None`  | Limpar histórico de mensagens                        |
| `get_all_available_tools()`            | `dict`  | Listar todas as ferramentas (sistema + customizadas) |
| `get_system_available_tools()`         | `dict`  | Listar apenas ferramentas do sistema                 |
| `get_metrics()`                        | `list`  | Obter métricas de performance                        |
| `export_metrics_json(path=None)`       | `str`   | Exportar métricas em JSON                            |
| `export_metrics_prometheus(path=None)` | `str`   | Exportar métricas em Prometheus                      |

📖 [Documentação completa da API](https://jor0105.github.io/Create-Agents-AI/reference/api/)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. **Fork** o repositório

1. **Crie uma branch**: `git checkout -b feature/nova-feature`

1. **Implemente** seguindo os padrões existentes

1. **Adicione testes**: Garanta cobertura mínima de 70%

1. **Execute os checks**:

   ```bash
   # Instalar pre-commit hooks
   poetry run pre-commit install

   # Executar todos os checks
   poetry run pre-commit run --all-files

   # Executar testes com cobertura
   poetry run pytest --cov=src --cov-fail-under=70
   ```

1. **Envie um Pull Request**

### Adicionando um Novo Provedor

1. Crie um novo adapter em `src/infra/adapters/NomeProvedor/`
1. Implemente a interface `ChatRepository`
1. Registre em `ChatAdapterFactory`
1. Adicione testes em `tests/infra/adapters/`

Exemplo:

```python
class MeuAdapter(ChatRepository):
    async def chat(self, message: str) -> str:
        # Sua implementação
        pass
```

📖 [Guia completo de contribuição](https://jor0105.github.io/Create-Agents-AI/dev-guide/contribute/)

---

## 🧪 CI/CD & Workflows

Este projeto tem automação profissional com GitHub Actions:

### Quality Checks (CI)

- **Executa em**: Push/PR para `develop` ou `main`
- **Matrix**: Python 3.12, 3.13, 3.14
- **Checks**:
  - ✅ Lint (Black, Ruff, isort)
  - ✅ Type checking (mypy)
  - ✅ Security (Bandit, detect-secrets)
  - ✅ Tests com cobertura mínima de 70%
  - ✅ Docstring validation (pydocstyle)

### Documentation Build

- **Executa**: Manualmente via `workflow_dispatch`
- **Ação**: Build e validação da documentação com MkDocs

### Pre-commit Hooks

15+ verificadores automáticos antes de cada commit:

```bash
# Instalar
poetry run pre-commit install

# Executar manualmente
poetry run pre-commit run --all-files
```

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📞 Suporte

- 📖 [Documentação Completa](https://jor0105.github.io/Create-Agents-AI/)
- 🐛 [Reportar Bugs](https://github.com/jor0105/Create-Agents-AI/issues)
- 💬 [Discussões](https://github.com/jor0105/Create-Agents-AI/discussions)
- 📧 Email: estraliotojordan@gmail.com

---

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jor0105](https://github.com/jor0105)
- Email: estraliotojordan@gmail.com

---

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

<div align="center">

**Versão:** 0.2.0
**Última atualização:** 02/12/2025
**Status:** 🚀 Projeto publicado! Aberto para contribuições e sugestões.

⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!

</div>

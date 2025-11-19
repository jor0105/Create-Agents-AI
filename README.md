src/
createagents/
application/
domain/
infra/
main/
utils/

# 🤖 Create Agents AI

Framework Python enterprise para criar agentes de IA inteligentes com arquitetura limpa, múltiplos provedores e ferramentas extensíveis.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-brightgreen.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 📚 Documentação

Este repositório contém a documentação oficial do **Create Agents AI**.

### Estrutura dos Docs

- `index.md`: Visão geral, principais recursos, arquitetura resumida, links rápidos.
- `user-guide/`: Guia do usuário (instalação, uso básico, exemplos, FAQ).
- `guia/`: Guia avançado (instalação avançada, exemplos avançados).
- `dev-guide/`: Guia do desenvolvedor (arquitetura, exemplos técnicos, contribuição).
- `reference/`: Referência técnica (ferramentas, comandos).
- `api.md`: Referência da API pública.
- `arquitetura.md`: Resumo visual e explicativo da arquitetura.
- `tools.md`: Guia antigo de ferramentas (mantido para referência).

### Navegação Recomendada

- **Guia do Usuário**: [Instalação](docs/user-guide/installation-user.md) | [Uso Básico](docs/user-guide/basic-usage-user.md) | [Exemplos](docs/user-guide/examples-user.md) | [FAQ](docs/user-guide/faq-user.md)
- **Guia Avançado**: [Instalação Avançada](docs/guia/instalacao.md) | [Exemplos Avançados](docs/guia/exemplos.md)
- **Guia do Desenvolvedor**: [Arquitetura](docs/dev-guide/architecture-developer.md) | [Exemplos Técnicos](docs/dev-guide/technical-examples.md) | [Como Contribuir](docs/dev-guide/contribute.md)
- **Referência**: [Ferramentas](docs/reference/tools.md) | [Comandos](docs/reference/commands.md) | [API Reference](docs/api.md)
- **Outros**: [Arquitetura (resumo)](docs/arquitetura.md)

---

## 🚀 Instalação Rápida

```bash
git clone https://github.com/jor0105/Creator-Agents-AI.git
cd Create-Agents-AI
poetry install
# ou
poetry install -E file-tools
```

## 🏗️ Build Local da Documentação

```bash
poetry run mkdocs serve
# Acesse: http://localhost:8000
```

## 📄 Licença

MIT - Use livremente em seus projetos.

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jor0105](https://github.com/jor0105)
- Email: estraliotojordan@gmail.com

**Versão:** 0.1.0 | **Atualização:** 17/11/2025

# Conversar

response = agent.chat("Qual é a diferença entre lista e tupla?")

# Obter histórico

configs = agent.get_configs()

# Limpar histórico

agent.clear_history()

````

### ✅ Gerenciamento de histórico

```python
# Histórico automático (últimas 10 mensagens por padrão)
agent.chat("Primeira mensagem")
agent.chat("Segunda mensagem")

# Personalizar tamanho do histórico
agent = CreateAgent(provider="openai", model="gpt-4", history_max_size=20)

# Limpar quando necessário
agent.clear_history()
````

### ✅ Configuração customizada

```python
config = {
    "temperature": 0.7,     # Criatividade (0-1)
    "max_tokens": 1000,     # Limite de resposta
}

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Assistente",
    instructions="Seja conciso",
    config=config,
)
```

### ✅ Métricas e performance

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

## 📋 Exemplos de Uso

### Exemplo 1: Assistente de Programação

```python
from createagents import CreateAgent

assistant = CreateAgent(
    provider="openai",
    model="gpt-4",
    name="Code Assistant",
    instructions="Você é um especialista em programação Python. Sempre forneça exemplos de código.",
    config={"temperature": 0.3}  # Menos criatividade para código
)

# Conversar
response = assistant.chat("Como ordenar uma lista de dicionários por chave?")
print(response)

# Ver histórico
config = assistant.get_configs()
print(f"Histórico: {len(config['history'])} mensagens")

# Limpar e começar novo diálogo
assistant.clear_history()
```

### Exemplo 2: Agente Local com Ollama

```python
# Certifique-se que Ollama está rodando
# ollama serve

agent = CreateAgent(
    provider="ollama",
    model="llama2",
    name="Local Assistant"
)

# Usar localmente (sem custos de API)
response = agent.chat("Resuma Clean Architecture em 3 pontos")
print(response)
```

### Exemplo 3: Múltiplos Agentes

```python
# Um para análise
analyzer = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você analisa código e fornece feedback crítico",
    config={"temperature": 0.5}
)

# Outro para documentação
documentor = CreateAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você escreve documentação clara e profissional",
    config={"temperature": 0.3}
)

# Usar ambos
code = "def sum(a,b): return a+b"
feedback = analyzer.chat(f"Revise este código:\n{code}")
docs = documentor.chat(f"Documente este código:\n{code}")

print("Feedback:", feedback)
print("Documentação:", docs)
```

### Exemplo 4: Verificando Ferramentas Disponíveis

```python
from createagents import BaseTool

# Criar ferramenta customizada
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

# Criar agente com ferramentas
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", CalculatorTool()]
)

# Ver todas as ferramentas do agente (sistema + customizadas)
all_tools = agent.get_all_available_tools()
print(f"Total de ferramentas: {len(all_tools)}")
for name, description in all_tools.items():
    print(f"  • {name}: {description[:50]}...")

# Ver apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()
print(f"\nFerramentas do sistema: {list(system_tools.keys())}")

# Verificar se ferramenta opcional está instalada
if "readlocalfile" in system_tools:
    print("✅ ReadLocalFileTool disponível")
else:
    print("⚠️  Execute: poetry install -E file-tools")
```

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx...

```

## 📊 API Referência

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

#### Métodos

| Método                                 | Retorno | Descrição                                                      |
| -------------------------------------- | ------- | -------------------------------------------------------------- |
| `chat(message)`                        | `str`   | Enviar mensagem e receber resposta                             |
| `get_configs()`                        | `dict`  | Obter configurações e histórico                                |
| `clear_history()`                      | `None`  | Limpar histórico de mensagens                                  |
| `get_all_available_tools()`            | `dict`  | Listar todas as ferramentas do agente (sistema + customizadas) |
| `get_system_available_tools()`         | `dict`  | Listar apenas ferramentas do sistema                           |
| `get_metrics()`                        | `list`  | Obter métricas de performance                                  |
| `export_metrics_json(path=None)`       | `str`   | Exportar métricas em JSON                                      |
| `export_metrics_prometheus(path=None)` | `str`   | Exportar métricas em Prometheus                                |

## 📚 Arquitetura (Para Desenvolvedores)

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

## 🤝 Contribuindo

Quer adicionar um novo provedor de IA?

1. **Crie um novo adapter** em `src/infra/adapters/NomeProvedor/`
1. **Implemente** a interface `ChatRepository`
1. **Registre** em `ChatAdapterFactory`
1. **Adicione testes** em `tests/infra/adapters/`

Exemplo:

```python
class MeuAdapter(ChatRepository):
    async def chat(self, message: str) -> str:
        # Sua implementação
        pass
```

## 🧪 Para Desenvolvedores: CI/CD & Workflows

Este projeto tem automação profissional com GitHub Actions:

- **Quality Checks (CI)**: Lint, formatação, type checking, security, testes com cobertura mínima de 70%

  - Executa em: Push/PR para `develop` ou `main`
  - Matrix: Python 3.12, 3.13, 3.14

- **Documentation Build**: Build e validação da documentação com MkDocs

  - Executa: Manualmente via workflow_dispatch

- **Pre-commit Hooks**: 15+ verificadores automáticos antes de cada commit

  - Black, Ruff, isort, mypy, pydocstyle, yamllint e mais

**📖 Documentação Completa:** [`docs/ci-cd.md`](./docs/ci-cd.md)

**Quick start para contribuir:**

```bash
# Instalar pre-commit hooks
poetry run pre-commit install

# Executar todos os checks localmente
poetry run pre-commit run --all-files

# Executar testes com cobertura
poetry run pytest --cov=src --cov-fail-under=70
```

## 📄 Licença

MIT - Use livremente em seus projetos!

## 📞 Suporte

- 📖 [Documentação Completa](./docs/)
- 🐛 [Reportar Bugs](https://github.com/jor0105/Create-Agents-AI/issues)
- 💬 [Discussões](https://github.com/jor0105/Create-Agents-AI/discussions)

## 👨‍💻 Autor

**Jordan Estralioto**

- Email: estraliotojordan@gmail.com
- GitHub: [@jor0105](https://github.com/jor0105)

---

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**Versão:** 0.1.0
**Última atualização:** 17/11/2025

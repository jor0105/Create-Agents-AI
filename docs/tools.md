# 🛠️ Ferramentas (Tools)

Este guia explica as ferramentas disponíveis para seus agentes de IA e como usá-las.

---

## 📦 Visão Geral

Ferramentas são **capacidades adicionais** que seus agentes podem usar para executar tarefas específicas. Para manter o sistema leve, algumas ferramentas com dependências pesadas são **opcionais**.

---

## 🎯 Ferramentas Disponíveis

### ✅ CurrentDateTool (Sempre Disponível)

Obtém data e hora atuais em qualquer timezone.

**Dependências:** Nenhuma (biblioteca padrão Python)

**Uso:**

```python
from src.presentation import AIAgent

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["current_date"]
)

response = agent.chat("Que dia é hoje?")
print(response)
```

**Ações suportadas:**

- `date` - Data (YYYY-MM-DD)
- `time` - Hora (HH:MM:SS)
- `datetime` - Data e hora completos
- `timestamp` - Unix timestamp
- `date_with_weekday` - Data com dia da semana

---

### 🔧 ReadLocalFileTool (Opcional)

Lê arquivos locais em múltiplos formatos.

**Formatos:** TXT, MD, CSV, Excel (XLS/XLSX), PDF, Parquet, JSON, YAML

**Dependências:** `tiktoken`, `unstructured`, `pandas`, `openpyxl`, `pyarrow`, `chardet`

**Instalação:**

```bash
# Com pip
pip install ai-agent[file-tools]

# Com poetry
poetry install -E file-tools
```

**Uso:**

```python
from src.presentation import AIAgent

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["readlocalfile"]
)

response = agent.chat("Leia o arquivo report.pdf e resuma")
print(response)
```

**Limites:**

- Tamanho máximo: 100MB
- Tokens máximos: Depende da AI utilizada

**Funcionalidades:**

- ✅ Validação de tamanho
- ✅ Detecção automática de encoding
- ✅ Suporte a múltiplos formatos
- ✅ Tratamento robusto de erros

---

## 🚀 Uso com Agentes

### Exemplo 1: Ferramenta de Data

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você pode verificar data/hora quando necessário",
    tools=["current_date"]
)

# O agente usa a ferramenta automaticamente
response = agent.chat("Que dia da semana é hoje?")
```

### Exemplo 2: Leitura de Arquivos

```python
# Certifique-se que instalou: poetry install -E file-tools

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    instructions="Você pode ler arquivos locais",
    tools=["readlocalfile"]
)

response = agent.chat("Resuma o documento relatorio.pdf")
```

### Exemplo 3: Múltiplas Ferramentas

```python
agent = AIAgent(
    provider="openai",
    model="gpt-4",
    tools=["current_date", "readlocalfile"]
)

# O agente escolhe qual ferramenta usar
agent.chat("Que dia é hoje?")  # Usa current_date
agent.chat("Leia notas.txt")   # Usa readlocalfile
```

---

## 📋 Checklist de Instalação

### Instalação Básica ✅

```bash
poetry install
```

Inclui:

- [x] CurrentDateTool
- [x] Gerenciamento de histórico
- [x] Métricas de performance
- [x] OpenAI e Ollama adapters

### Instalação com File Tools 📁

```bash
poetry install -E file-tools
```

Inclui:

- [x] Tudo da instalação básica
- [x] ReadLocalFileTool
- [x] Suporte para PDF, Excel, CSV, Parquet

---

## 🔍 Verificar Ferramentas Disponíveis

```python
from src.presentation import AIAgent

agent = AIAgent(
    provider="openai",
    model="gpt-4"
)

# Obter todas as ferramentas disponíveis
tools = agent.get_available_tools()

print("Ferramentas disponíveis:")
for name, tool in tools.items():
    print(f"  - {name}: {tool.description[:50]}...")

# Verificar ferramenta específica
if "readlocalfile" in tools:
    print("✅ ReadLocalFileTool disponível!")
else:
    print("⚠️ Instale com: poetry install -E file-tools")
```

---

## ⚡ Performance

### Uso de Memória

| Instalação     | Memória Base | Com ReadLocalFileTool |
| -------------- | ------------ | --------------------- |
| Básica         | ~50MB        | N/A                   |
| Com file-tools | ~50MB        | ~200MB (quando usada) |

---

## 🎨 Criar Suas Próprias Ferramentas

### Ferramenta Simples

```python
from src.domain import BaseTool

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
```

### Ferramenta com Dependências Opcionais

```python
from src.domain import BaseTool

# Lazy import
try:
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = e

class MLTool(BaseTool):
    name = "ml_tool"
    description = "Ferramenta com ML"

    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError(
                f"MLTool requires: pip install ai-agent[ml-tools]\n"
                f"Error: {IMPORT_ERROR}"
            )

    def execute(self, data: str) -> str:
        # Sua lógica aqui
        pass
```

---

## 🤔 FAQ

**P: Por que algumas ferramentas são opcionais?**
R: Para manter o sistema leve. Se você não precisa ler PDFs/Excel, não precisa instalar pandas, unstructured, etc.

**P: Como sei quais ferramentas estão disponíveis?**
R: Use `agent.get_available_tools()` para listar.

**P: O que acontece se eu tentar usar uma ferramenta não instalada?**
R: Você receberá erro claro: `pip install ai-agent[file-tools]`

**P: Posso criar minhas próprias ferramentas?**
R: Sim! Siga o padrão de lazy loading e estenda `BaseTool`.

---

**Última atualização:** Novembro 2025

# 🛠️ Ferramentas (Tools) do AI Agent

Este documento descreve as ferramentas disponíveis para seus agentes de IA e como instalá-las.

## 📦 Visão Geral

As ferramentas são **funcionalidades adicionais** que seus agentes podem usar para executar tarefas específicas. Para manter a biblioteca leve e performática, algumas ferramentas pesadas são **opcionais** e só são carregadas quando necessário.

## 🎯 Ferramentas Disponíveis

### ✅ Ferramentas Básicas (Sempre Disponíveis)

Estas ferramentas são leves e vêm instaladas por padrão:

#### 1. **CurrentDateTool**

- **Descrição**: Obtém a data e hora atuais
- **Dependências**: Nenhuma (biblioteca padrão Python)
- **Uso**:

```python
from src.infra.adapters.Tools import CurrentDateTool

tool = CurrentDateTool()
result = tool.execute()
print(result)  # "2025-11-07 14:30:00"
```

### 🔧 Ferramentas Opcionais (Requer Instalação Extra)

Estas ferramentas possuem dependências pesadas e precisam ser instaladas separadamente:

#### 2. **ReadLocalFileTool**

- **Descrição**: Lê arquivos locais com suporte a múltiplos formatos
- **Formatos Suportados**: TXT, MD, CSV, Excel (XLS/XLSX), PDF, Parquet, JSON, YAML, e mais
- **Dependências**: `tiktoken`, `pymupdf`, `pandas`, `openpyxl`, `pyarrow`, `chardet`
- **Instalação**:

```bash
# Com pip
pip install ai-agent[file-tools]

# Com poetry
poetry install -E file-tools
```

- **Uso**:

```python
from src.infra.adapters.Tools import ReadLocalFileTool

# Tentará importar - falhará se dependências não instaladas
try:
    tool = ReadLocalFileTool()
    content = tool.execute(path="/caminho/para/arquivo.pdf", max_tokens=30000)
    print(content)
except ImportError as e:
    print("ReadLocalFileTool não disponível. Instale com: pip install ai-agent[file-tools]")
```

- **Funcionalidades**:
  - ✅ Validação de tamanho de arquivo (max 100MB)
  - ✅ Validação de limite de tokens
  - ✅ Detecção automática de encoding
  - ✅ Suporte a múltiplos formatos
  - ✅ Tratamento robusto de erros

## 🚀 Como Usar Ferramentas com Agentes

### Exemplo 1: Agente com Ferramenta de Data

```python
from src.presentation import AIAgent

# Criar agente (ferramenta CurrentDateTool é registrada automaticamente)
agent = AIAgent(
    model="gpt-4",
    name="Assistente Temporal",
    instructions="Você pode verificar a data/hora atual quando necessário"
)

# O agente pode usar a ferramenta automaticamente
response = agent.chat("Que dia é hoje?")
print(response)  # O agente usará CurrentDateTool internamente
```

### Exemplo 2: Agente com Ferramenta de Leitura de Arquivos

```python
from src.presentation import AIAgent

# Certifique-se que instalou: poetry install -E file-tools

agent = AIAgent(
    model="gpt-4",
    name="Leitor de Documentos",
    instructions="Você pode ler arquivos locais para ajudar o usuário"
)

# O agente pode usar ReadLocalFileTool automaticamente
response = agent.chat("Resuma o arquivo /home/user/documento.pdf")
print(response)  # O agente lerá o PDF e criará um resumo
```

## 📋 Checklist de Instalação

### Instalação Básica ✅

- [x] OpenAI / Ollama adapters
- [x] CurrentDateTool
- [x] Gerenciamento de histórico
- [x] Métricas e performance

### Instalação Completa com File Tools 📁

```bash
poetry install -E file-tools
```

- [x] Tudo da instalação básica
- [x] ReadLocalFileTool
- [x] Suporte para PDF, Excel, CSV, Parquet
- [x] Análise de documentos com tokens

## 🔍 Verificando Ferramentas Disponíveis

```python
from src.infra.config.available_tools import AvailableTools

# Obter todas as ferramentas disponíveis
tools = AvailableTools.get_available_tools()

print("Ferramentas disponíveis:")
for name, tool in tools.items():
    print(f"  - {name}: {tool.description[:50]}...")

# Verificar se uma ferramenta específica está disponível
if "readlocalfile" in tools:
    print("✅ ReadLocalFileTool está disponível!")
else:
    print("⚠️ ReadLocalFileTool não instalada. Use: poetry install -E file-tools")
```

## 🛡️ Tratamento de Erros

A biblioteca trata graciosamente quando dependências opcionais não estão instaladas:

```python
from src.infra.config.available_tools import AvailableTools

tools = AvailableTools.get_available_tools()

# Se file-tools não estiver instalado:
# - CurrentDateTool estará disponível
# - ReadLocalFileTool será silenciosamente ignorada
# - Um warning será logado

# Sem crashes! Sem erros fatais!
```

## ⚡ Performance

### Impacto no Tempo de Importação

**Sem lazy loading (antigo)**:

```python
import src.infra.adapters  # ~2-3 segundos (carrega pandas, tiktoken, etc)
```

**Com lazy loading (novo)**:

```python
import src.infra.adapters  # ~0.1 segundos (só carrega o necessário)
from src.infra.adapters import ReadLocalFileTool  # ~2 segundos (só quando usado)
```

### Uso de Memória

| Instalação     | Memória Base | Com ReadLocalFileTool |
| -------------- | ------------ | --------------------- |
| Básica         | ~50MB        | N/A (não instalada)   |
| Com file-tools | ~50MB        | ~200MB (quando usada) |

## 🎨 Criando Suas Próprias Ferramentas

### Ferramenta Simples (Sem Dependências Pesadas)

```python
from src.domain import BaseTool

class MySimpleTool(BaseTool):
    name = "my_tool"
    description = "Uma ferramenta simples sem dependências pesadas"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Entrada da ferramenta"}
        },
        "required": ["input"]
    }

    def execute(self, input: str) -> str:
        return f"Processado: {input}"
```

### Ferramenta com Dependências Pesadas (Opcional)

```python
# my_heavy_tool.py
from src.domain import BaseTool

# Lazy import das dependências pesadas
try:
    import numpy as np
    import tensorflow as tf
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = e

class MyHeavyTool(BaseTool):
    name = "my_heavy_tool"
    description = "Ferramenta com dependências pesadas (ML)"

    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError(
                "MyHeavyTool requires: pip install ai-agent[ml-tools]\n"
                f"Error: {IMPORT_ERROR}"
            )
        # Inicializar recursos pesados aqui

    def execute(self, data: str) -> str:
        # Sua lógica com numpy/tensorflow
        pass
```

Depois adicione aos extras no `pyproject.toml`:

```toml
[tool.poetry.extras]
ml-tools = ["numpy", "tensorflow"]
```

## 📚 Referências

- [Documentação de Instalação](./guia/instalacao.md)
- [Exemplos de Uso](./guia/exemplos.md)
- [API Completa](./api.md)

## 🤔 FAQ

**P: Por que algumas ferramentas são opcionais?**
R: Para manter a biblioteca leve. Se você não precisa ler PDFs/Excel, não precisa instalar pandas, pymupdf, etc. Isso resulta em instalações mais rápidas e menor uso de memória.

**P: Como sei quais ferramentas estão disponíveis?**
R: Use `AvailableTools.get_available_tools()` para listar todas as ferramentas carregadas.

**P: O que acontece se eu tentar usar uma ferramenta não instalada?**
R: Você receberá um erro claro informando qual extra instalar: `pip install ai-agent[file-tools]`

**P: Posso criar minhas próprias ferramentas opcionais?**
R: Sim! Siga o padrão de lazy loading e adicione seus extras no `pyproject.toml`.

---

**Última atualização:** Novembro 2025
